# Copyright (C) 2015 Midokura SARL.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import contextlib
import mock
from webob import exc

from midonet.neutron.tests.unit import test_midonet_plugin_v2 as test_mn

from neutron.db import servicetype_db as st_db
from neutron.plugins.common import constants
from neutron.services import provider_configuration as provconf
from neutron.tests.unit.api import test_extensions as test_ex
from neutron.tests.unit.extensions import test_l3
from neutron_lbaas.extensions import loadbalancer
from neutron_lbaas.tests.unit.db.loadbalancer import test_db_loadbalancer
from oslo_utils import uuidutils

MN_DRIVER_KLASS = ('midonet.neutron.services.loadbalancer.driver.'
                   'MidonetLoadbalancerDriver')


class LoadbalancerTestExtensionManager(test_l3.L3TestExtensionManager):

    def get_resources(self):
        res = super(LoadbalancerTestExtensionManager, self).get_resources()
        return res + loadbalancer.Loadbalancer.get_resources()

    def get_actions(self):
        return []

    def get_request_extensions(self):
        return []


class LoadbalancerTestCase(test_db_loadbalancer.LoadBalancerTestMixin,
                           test_l3.L3NatTestCaseMixin,
                           test_mn.MidonetPluginV2TestCase):

    def setUp(self):
        service_plugins = {
            'lb_plugin_name': test_db_loadbalancer.DB_LB_PLUGIN_KLASS}
        lbaas_provider = (constants.LOADBALANCER + ':lbaas:' +
                          MN_DRIVER_KLASS + ':default')
        mock.patch.object(provconf.NeutronModule, 'service_providers',
                          return_value=[lbaas_provider]).start()
        manager = st_db.ServiceTypeManager.get_instance()
        manager.add_provider_configuration(
            constants.LOADBALANCER, provconf.ProviderConfiguration())
        ext_mgr = LoadbalancerTestExtensionManager()

        super(LoadbalancerTestCase, self).setUp(
            service_plugins=service_plugins, ext_mgr=ext_mgr)
        self.ext_api = test_ex.setup_extensions_middleware(ext_mgr)

        # Subnet and router must always exist and associated
        network = self._make_network(self.fmt, 'net1', True)
        self._subnet = self._make_subnet(self.fmt, network, "10.0.0.1",
                                   '10.0.0.0/24')
        self._subnet_id = self._subnet['subnet']['id']
        router = self._make_router(self.fmt, self._tenant_id, 'router1', True)
        self._router_id = router['router']['id']
        self._router_interface_action('add', self._router_id, self._subnet_id,
                                      None)

        # Also prepare external network and subnet which are needed for VIP
        ext_network = self._make_network(self.fmt, 'ext_net1', True)
        self._set_net_external(ext_network['network']['id'])
        self._ext_subnet = self._make_subnet(self.fmt, ext_network,
                                             "200.0.0.1", '200.0.0.0/24')

        # Router must have gateway set for VIP - Pool association
        self._add_external_gateway_to_router(self._router_id,
                                             ext_network['network']['id'])

        # Override the default subnet ID used in the upstream load balancer
        # tests so that the midonet-specific tests use the specific subnet
        # created in the setup
        test_db_loadbalancer._subnet_id = self._subnet_id

    def tearDown(self):
        super(LoadbalancerTestCase, self).tearDown()

    @contextlib.contextmanager
    def subnet_with_router(self, cidr='10.0.1.0/24'):
        with self.subnet(cidr=cidr) as sub:
            subnet = sub['subnet']
            self._router_interface_action('add', self._router_id,
                                          subnet['id'], None)
            yield sub

    @contextlib.contextmanager
    def pool_with_hm_associated(self, subnet_id=None, do_delete=True):
        with self.health_monitor(do_delete=do_delete) as hm:
            with self.pool(subnet_id=subnet_id, do_delete=do_delete) as pool:
                # Associate the health_monitor to the pool
                assoc = {"health_monitor": {
                         "id": hm['health_monitor']['id'],
                         'tenant_id': self._tenant_id}}
                req = self.new_create_request("pools",
                                              assoc,
                                              fmt=self.fmt,
                                              id=pool['pool']['id'],
                                              subresource="health_monitors")
                res = req.get_response(self.ext_api)
                self.assertEqual(exc.HTTPCreated.code, res.status_int)

                # Due to the policy check, the returned response gets the
                # associated health monitor IDs stripped and an empty list is
                # returned.  So verify the association by doing a separate
                # 'get'.
                req = self.new_show_request('pools',
                                            pool['pool']['id'],
                                            fmt=self.fmt)
                p = self.deserialize(self.fmt, req.get_response(self.ext_api))

                yield p, hm

    def _test_create_vip(self, name="VIP", pool_id=None, protocol='HTTP',
                         port_number=80, admin_state_up=True,
                         subnet_id=None,
                         expected_res_status=exc.HTTPCreated.code):
        if subnet_id is None:
            subnet_id = self._ext_subnet['subnet']['id']
        self._create_vip(self.fmt, name, pool_id, protocol, port_number,
                         admin_state_up, subnet_id=subnet_id,
                         expected_res_status=expected_res_status)

    def _test_vip_status(self, vip_id, status):
        req = self.new_show_request('vips', vip_id)
        resp = req.get_response(self.ext_api)
        self.assertEqual(exc.HTTPOk.code, resp.status_int)
        vip = self.deserialize(self.fmt, resp)
        self.assertEqual(status, vip['vip']['status'])

    def _test_create_pool(self, name="pool", lb_method='ROUND_ROBIN',
                          protocol='TCP', admin_state_up=True,
                          subnet_id=test_db_loadbalancer._subnet_id,
                          expected_res_status=exc.HTTPOk.code):
        self._create_pool(self.fmt, name, lb_method, protocol, admin_state_up,
                          subnet_id=subnet_id,
                          expected_res_status=expected_res_status)

    def test_create_pool(self):
        name = "pool1"
        keys = [('name', name),
                ('subnet_id', test_db_loadbalancer._subnet_id),
                ('tenant_id', self._tenant_id),
                ('protocol', 'HTTP'),
                ('lb_method', 'ROUND_ROBIN'),
                ('admin_state_up', True),
                ('status', 'ACTIVE')]
        with self.pool(name=name) as pool:
            for k, v in keys:
                self.assertEqual(v, pool['pool'][k])

    def test_create_pool_with_bad_subnet(self):
        # Subnet does not exist so it should throw an error
        self._create_pool(self.fmt, 'pool1', 'ROUND_ROBIN', 'TCP', True,
                          expected_res_status=exc.HTTPNotFound.code,
                          subnet_id=uuidutils.generate_uuid())

    def test_create_pool_with_external_subnet(self):
        # Subnet is on an external network, which results in an error
        self._test_create_pool(subnet_id=self._ext_subnet['subnet']['id'],
                               expected_res_status=exc.HTTPBadRequest.code)

    def test_create_pool_with_no_router(self):
        # Subnet with no router association should throw an exception
        with self.subnet() as sub:
            self._test_create_pool(subnet_id=sub['subnet']['id'],
                                   expected_res_status=exc.HTTPBadRequest.code)

    def test_delete_pool(self):
        with self.pool(do_delete=False) as pool:
            req = self.new_delete_request('pools', pool['pool']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(exc.HTTPNoContent.code, res.status_int)

    def test_show_pool(self):
        name = "pool1"
        keys = [('name', name),
                ('subnet_id', test_db_loadbalancer._subnet_id),
                ('tenant_id', self._tenant_id),
                ('protocol', 'HTTP'),
                ('lb_method', 'ROUND_ROBIN'),
                ('admin_state_up', True),
                ('status', 'ACTIVE')]
        with self.pool(name=name) as pool:
            req = self.new_show_request('pools',
                                        pool['pool']['id'],
                                        fmt=self.fmt)
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            for k, v in keys:
                self.assertEqual(v, res['pool'][k])

    def test_update_pool(self):
        keys = [('name', 'new_name'),
                ('admin_state_up', False)]
        with self.pool() as pool:
            req = self.new_update_request('pools',
                                          {'pool': {
                                              'name': 'new_name',
                                              'admin_state_up': False}},
                                          pool['pool']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            for k, v in keys:
                self.assertEqual(v, res['pool'][k])

    def test_create_vip(self):
        keys = [('name', 'vip1'),
                ('subnet_id', self._ext_subnet['subnet']['id']),
                ('tenant_id', self._tenant_id),
                ('protocol', 'HTTP'),
                ('protocol_port', 80),
                ('admin_state_up', True)]
        with self.pool() as pool:
            with self.vip(pool=pool, subnet=self._ext_subnet) as vip:
                for k, v in keys:
                    self.assertEqual(v, vip['vip'][k])

    def test_create_vip_with_bad_subnet(self):
        # Subnet does not exist so it should throw an error
        with self.pool() as pool:
            self._test_create_vip(pool_id=pool['pool']['id'],
                                  subnet_id=uuidutils.generate_uuid(),
                                  expected_res_status=exc.HTTPNotFound.code)

    def test_create_vip_same_subnet_as_pool_with_hm(self):
        # VIP and pool subnets cannot be the same if HM is associated
        with self.pool_with_hm_associated() as (pool, hm):
            self._test_create_vip(pool_id=pool['pool']['id'],
                                  subnet_id=pool['pool']['subnet_id'],
                                  expected_res_status=exc.HTTPBadRequest.code)

    def test_create_vip_same_subnet_as_pool_with_no_hm(self):
        # VIP and pool subnets can be the same if HM is not associated
        with self.pool(do_delete=False) as pool:
            self._test_create_vip(pool_id=pool['pool']['id'],
                                  subnet_id=pool['pool']['subnet_id'])

    def test_create_vip_with_bad_pool(self):
        # Non-existent pool results in an error
        self._test_create_vip(pool_id=uuidutils.generate_uuid(),
                              expected_res_status=exc.HTTPNotFound.code)

    def test_create_vip_with_ext_subnet_and_pool_with_no_gw(self):
        # Pool associated with vip must be attached to a router that has gw
        self._remove_external_gateway_from_router(
            self._router_id, self._ext_subnet['subnet']['network_id'])
        with self.pool() as pool:
            self._test_create_vip(pool_id=pool['pool']['id'],
                                  subnet_id=self._ext_subnet['subnet']['id'],
                                  expected_res_status=exc.HTTPBadRequest.code)

    def test_update_vip(self):
        keys = [('name', 'new_name'),
                ('subnet_id', self._ext_subnet['subnet']['id']),
                ('tenant_id', self._tenant_id),
                ('protocol', 'HTTP'),
                ('protocol_port', 80),
                ('admin_state_up', False)]
        with self.pool() as pool:
            with self.vip(pool=pool, subnet=self._ext_subnet) as vip:
                req = self.new_update_request('vips',
                                              {'vip': {
                                                  'name': 'new_name',
                                                  'admin_state_up': False}},
                                              vip['vip']['id'])
                res = self.deserialize(
                    self.fmt, req.get_response(self.ext_api))
                for k, v in keys:
                    self.assertEqual(v, res['vip'][k])

    def test_update_vip_same_subnet_as_pool_with_hm(self):
        # Updating the pool Id to a pool with the same subnet as the VIP
        # when HM is associated with the pool results in a validation error
        with self.subnet_with_router() as sub:
            subnet = sub['subnet']
            with self.pool() as pool1:
                with self.vip(pool=pool1, subnet=sub) as vip:
                    with self.pool_with_hm_associated(
                            do_delete=False,
                            subnet_id=subnet['id']) as (pool2, hm):
                        req = self.new_update_request(
                            'vips', {'vip': {'pool_id': pool2['pool']['id']}},
                            vip['vip']['id'])
                        res = req.get_response(self.ext_api)
                        self.assertEqual(exc.HTTPBadRequest.code,
                                         res.status_int)
                        self._test_vip_status(vip['vip']['id'],
                                              constants.ERROR)

    def test_update_vip_same_subnet_as_pool_with_no_hm(self):
        # Updating the pool Id to a pool with the same subnet as the VIP
        # when HM is NOT associated with the pool is accepted
        with self.subnet_with_router() as sub:
            subnet = sub['subnet']
            with self.pool(subnet_id=subnet['id']) as pool1:
                with self.pool(subnet_id=self._subnet_id) as pool2:
                    with self.vip(pool=pool1, subnet=self._ext_subnet) as vip:
                        req = self.new_update_request(
                            'vips', {'vip': {'pool_id': pool2['pool']['id']}},
                            vip['vip']['id'])
                        res = req.get_response(self.ext_api)
                        self.assertEqual(exc.HTTPOk.code, res.status_int)
                        self._test_vip_status(vip['vip']['id'],
                                              constants.ACTIVE)

    def test_create_pool_health_monitor(self):
        with self.pool_with_hm_associated() as (p, hm):
            self.assertEqual(1, len(p['pool']['health_monitors']))
            self.assertEqual(p['pool']['health_monitors'][0],
                             hm['health_monitor']['id'])

    def test_create_pool_health_monitor_already_associated(self):
        # Associating two health monitors to a pool throws an error
        with self.pool_with_hm_associated() as (p, hm):
            with self.health_monitor() as hm2:
                # Associate the second hm
                assoc2 = {"health_monitor": {
                          "id": hm2['health_monitor']['id'],
                          'tenant_id': self._tenant_id}}
                req2 = self.new_create_request(
                    "pools", assoc2, fmt=self.fmt, id=p['pool']['id'],
                    subresource="health_monitors")
                res2 = req2.get_response(self.ext_api)
                self.assertEqual(exc.HTTPBadRequest.code, res2.status_int)

    def test_delete_pool_health_monitor(self):
        with self.pool_with_hm_associated() as (p, hm):
            req = self.new_delete_request("pools", fmt=self.fmt,
                                          id=p['pool']['id'],
                                          sub_id=hm['health_monitor']['id'],
                                          subresource="health_monitors")
            res = req.get_response(self.ext_api)
            self.assertEqual(exc.HTTPNoContent.code, res.status_int)

            # Verify that it's gone
            req = self.new_show_request('pools', p['pool']['id'], fmt=self.fmt)
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertEqual(0, len(res['pool']['health_monitors']))

    def test_create_pool_health_monitor_with_same_vip_subnet(self):
        # Associating two health monitors to a pool which is associated
        # with a vip of the same subnet
        with self.pool(subnet_id=self._subnet_id) as pool:
            with self.vip(pool=pool, subnet=self._subnet):
                with self.health_monitor() as hm:
                    assoc = {"health_monitor": {
                             "id": hm['health_monitor']['id'],
                             'tenant_id': self._tenant_id}}
                    req = self.new_create_request(
                        "pools", assoc, fmt=self.fmt, id=pool['pool']['id'],
                        subresource="health_monitors")
                    res = req.get_response(self.ext_api)
                    self.assertEqual(exc.HTTPBadRequest.code, res.status_int,)
