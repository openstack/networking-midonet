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

import webob.exc

from midonet.neutron.tests.unit import test_midonet_plugin as test_mn
from midonet.neutron.tests.unit import test_midonet_plugin_api as test_mn_api

from neutron.tests.unit.api import test_extensions as test_ex
from neutron.tests.unit.extensions import test_l3
from neutron_lbaas.extensions import loadbalancer
from neutron_lbaas.tests.unit.db.loadbalancer import test_db_loadbalancer
from oslo_utils import uuidutils


class LoadbalancerTestExtensionManager(test_l3.L3TestExtensionManager):

    def get_resources(self):
        res = super(LoadbalancerTestExtensionManager, self).get_resources()
        return res + loadbalancer.Loadbalancer.get_resources()

    def get_actions(self):
        return []

    def get_request_extensions(self):
        return []


class LoadbalancerTestCase(test_db_loadbalancer.LoadBalancerTestMixin,
                           test_l3.L3NatTestCaseMixin):

    def setUp(self, core_plugin=None, lb_plugin=None, lbaas_provider=None,
              ext_mgr=None):

        super(LoadbalancerTestCase, self).setUp()
        ext_mgr = LoadbalancerTestExtensionManager()
        self.ext_api = test_ex.setup_extensions_middleware(ext_mgr)

        # Subnet and router must always exist and associated
        network = self._make_network(self.fmt, 'net1', True)
        subnet = self._make_subnet(self.fmt, network, "10.0.0.1",
                                   '10.0.0.0/24')
        subnet_id = subnet['subnet']['id']
        router = self._make_router(self.fmt, self._tenant_id, 'router1', True)
        self._router_id = router['router']['id']
        self._router_interface_action('add', self._router_id, subnet_id, None)

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
        test_db_loadbalancer._subnet_id = subnet_id

    def tearDown(self):
        super(LoadbalancerTestCase, self).tearDown()

    def _test_create_vip(self, name="VIP", pool_id=None, protocol='HTTP',
                         port_number=80, admin_state_up=True,
                         subnet_id=None,
                         expected_res_status=200):
        if subnet_id is None:
            subnet_id = self._ext_subnet['subnet']['id']
        self._create_vip(self.fmt, name, pool_id, protocol, port_number,
                         admin_state_up, subnet_id=subnet_id,
                         expected_res_status=expected_res_status)

    def _test_create_pool(self, name="pool", lb_method='ROUND_ROBIN',
                          protocol='TCP', admin_state_up=True,
                          subnet_id=test_db_loadbalancer._subnet_id,
                          expected_res_status=200):
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
                self.assertEqual(pool['pool'][k], v)

    def test_create_pool_with_bad_subnet(self):
        # Subnet does not exist so it should throw an error
        self._create_pool(self.fmt, 'pool1', 'ROUND_ROBIN', 'TCP', True,
                          expected_res_status=404,
                          subnet_id=uuidutils.generate_uuid())

    def test_create_pool_with_external_subnet(self):
        # Subnet is on an external network, which results in an error
        self._test_create_pool(subnet_id=self._ext_subnet['subnet']['id'],
                               expected_res_status=400)

    def test_create_pool_with_no_router(self):
        # Subnet with no router association should throw an exception
        with self.subnet() as sub:
            self._test_create_pool(subnet_id=sub['subnet']['id'],
                                   expected_res_status=400)

    def test_delete_pool(self):
        with self.pool(do_delete=False) as pool:
            req = self.new_delete_request('pools', pool['pool']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPNoContent.code)

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
                self.assertEqual(res['pool'][k], v)

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
                self.assertEqual(res['pool'][k], v)

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
                    self.assertEqual(vip['vip'][k], v)

    def test_create_vip_with_bad_subnet(self):
        # Subnet does not exist so it should throw an error
        with self.pool() as pool:
            self._test_create_vip(pool_id=pool['pool']['id'],
                                  subnet_id=uuidutils.generate_uuid(),
                                  expected_res_status=404)

    def test_create_vip_same_subnet_as_pool(self):
        # VIP and subnet cannot be set to the same subnet
        with self.pool() as pool:
            self._test_create_vip(pool_id=pool['pool']['id'],
                                  subnet_id=pool['pool']['subnet_id'],
                                  expected_res_status=400)

    def test_create_vip_with_bad_pool(self):
        # Non-existent pool results in an error
        self._test_create_vip(pool_id=uuidutils.generate_uuid(),
                              expected_res_status=404)

    def test_create_vip_with_ext_subnet_and_pool_with_no_gw(self):
        # Pool associated with vip must be attached to a router that has gw
        self._remove_external_gateway_from_router(
            self._router_id, self._ext_subnet['subnet']['network_id'])
        with self.pool() as pool:
            self._test_create_vip(pool_id=pool['pool']['id'],
                                  subnet_id=self._ext_subnet['subnet']['id'],
                                  expected_res_status=400)


class LoadbalancerClusterTestCase(LoadbalancerTestCase,
                                  test_mn.MidonetPluginV2TestCase):

    pass


class LoadbalancerApiTestCase(LoadbalancerTestCase,
                              test_mn_api.MidonetPluginApiV2TestCase):

    pass
