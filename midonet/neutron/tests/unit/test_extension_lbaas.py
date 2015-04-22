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

from neutron.tests.unit.api import test_extensions as test_ex
from neutron.tests.unit.extensions import test_l3
from neutron_lbaas.extensions import loadbalancer
from neutron_lbaas.tests.unit.db.loadbalancer import test_db_loadbalancer


class LoadbalancerTestExtensionManager(test_l3.L3TestExtensionManager):

    def get_resources(self):
        res = super(LoadbalancerTestExtensionManager, self).get_resources()
        return res + loadbalancer.Loadbalancer.get_resources()

    def get_actions(self):
        return []

    def get_request_extensions(self):
        return []


class LoadbalancerTestCase(test_db_loadbalancer.LoadBalancerTestMixin,
                           test_mn.MidonetPluginTaskV2TestCase,
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
        self._subnet_id = subnet['subnet']['id']
        router = self._make_router(self.fmt, self._tenant_id, 'router1', True)
        self._router_id = router['router']['id']
        self._router_interface_action('add', self._router_id, self._subnet_id,
                                      None)

    def tearDown(self):
        super(LoadbalancerTestCase, self).tearDown()

    def _create_pool(self, fmt, name, lb_method, protocol, admin_state_up,
                     expected_res_status=None, **kwargs):
        data = {'pool': {'name': name,
                         'subnet_id': self._subnet_id,
                         'lb_method': lb_method,
                         'protocol': protocol,
                         'admin_state_up': admin_state_up,
                         'tenant_id': self._tenant_id}}
        pool_req = self.new_create_request('pools', data, fmt)
        pool_res = pool_req.get_response(self.ext_api)
        if expected_res_status:
            self.assertEqual(pool_res.status_int, expected_res_status)

        return pool_res

    def test_create_pool(self):
        name = "pool1"
        keys = [('name', name),
                ('subnet_id', self._subnet_id),
                ('tenant_id', self._tenant_id),
                ('protocol', 'HTTP'),
                ('lb_method', 'ROUND_ROBIN'),
                ('admin_state_up', True),
                ('status', 'ACTIVE')]
        with self.pool(name=name) as pool:
            for k, v in keys:
                self.assertEqual(pool['pool'][k], v)

    def test_delete_pool(self):
        with self.pool(do_delete=False) as pool:
            req = self.new_delete_request('pools', pool['pool']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPNoContent.code)

    def test_show_pool(self):
        name = "pool1"
        keys = [('name', name),
                ('subnet_id', self._subnet_id),
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
