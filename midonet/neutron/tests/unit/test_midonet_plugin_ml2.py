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

import functools
import mock
import testscenarios
from webob import exc

from midonet.neutron.tests.unit import test_midonet_plugin as test_mn_plugin

from neutron.extensions import external_net
from neutron.extensions import providernet as pnet
from neutron.tests.unit.api import test_extensions
from neutron.tests.unit.db import test_db_base_plugin_v2 as test_plugin
from neutron.tests.unit.extensions import test_l3
from neutron.tests.unit.extensions import test_securitygroup as test_sg

from oslo_config import cfg

load_tests = testscenarios.load_tests_apply_scenarios

PLUGIN_NAME = 'neutron.plugins.ml2.plugin.Ml2Plugin'

cfg.CONF.import_group('ml2', 'neutron.plugins.ml2.config')


class MidonetPluginConf(object):
    """Plugin configuration shared across the unit and functional tests.
    """

    plugin_name = PLUGIN_NAME

    @staticmethod
    def setUp(test_case, parent_setup=None):
        """Perform additional configuration around the parent's setUp."""
        cfg.CONF.set_override('client', test_mn_plugin.TEST_MN_CLIENT,
                              group='MIDONET')
        cfg.CONF.set_override('type_drivers',
                              ['midonet', 'uplink', 'local'],
                              group='ml2')
        cfg.CONF.set_override('mechanism_drivers',
                              ['midonet', 'openvswitch'],
                              group='ml2')
        cfg.CONF.set_override('tenant_network_types',
                              ['midonet', 'uplink', 'local'],
                              group='ml2')
        if parent_setup:
            parent_setup()


class MidonetPluginML2TestCase(test_plugin.NeutronDbPluginV2TestCase):

    def setup_parent(self, service_plugins=None, ext_mgr=None):

        # Set up mock for the midonet client to be made available in tests
        patcher = mock.patch(test_mn_plugin.TEST_MN_CLIENT)
        self.client_mock = mock.MagicMock()
        patcher.start().return_value = self.client_mock

        l3_plugin = {'l3_plugin_name': 'midonet_l3'}

        if service_plugins:
            service_plugins.update(l3_plugin)
        else:
            service_plugins = l3_plugin

        # Ensure that the parent setup can be called without arguments
        # by the common configuration setUp.
        parent_setup = functools.partial(
            super(MidonetPluginML2TestCase, self).setUp,
            plugin=MidonetPluginConf.plugin_name,
            service_plugins=service_plugins,
            ext_mgr=ext_mgr,
        )
        MidonetPluginConf.setUp(self, parent_setup)
        self.port_create_status = 'DOWN'

    def setUp(self, plugin=None, service_plugins=None, ext_mgr=None):
        self.setup_parent(service_plugins=service_plugins, ext_mgr=ext_mgr)


class TestMidonetNetworksML2(MidonetPluginML2TestCase,
                            test_plugin.TestNetworksV2):
    pass


class TestMidonetSecurityGroupML2(test_sg.TestSecurityGroups,
                                  MidonetPluginML2TestCase):
    pass


class TestMidonetSubnetsML2(MidonetPluginML2TestCase,
                            test_plugin.TestSubnetsV2):

    def test_delete_subnet_port_exists_owned_by_network(self):
        # MidoNet doesn't support updating dhcp port's fixed-ips.
        pass

    def test_delete_subnet_dhcp_port_associated_with_other_subnets(self):
        # MidoNet doesn't support updating dhcp port's fixed-ips.
        pass


class TestMidonetPortsML2(MidonetPluginML2TestCase,
                          test_plugin.TestPortsV2):

    def test_update_dhcp_port_with_exceeding_fixed_ips(self):
        # MidoNet doesn't support updating dhcp port's fixed-ips.
        pass


class TestMidonetRouterML2(MidonetPluginML2TestCase,
                           test_l3.L3NatTestCaseMixin):
    scenarios = [
        ('midonet',
         dict(network_type='midonet',
              expected_code=exc.HTTPOk.code,
              expected_code_for_create=exc.HTTPCreated.code)),
        ('uplink',
         dict(network_type='uplink',
              expected_code=exc.HTTPOk.code,
              expected_code_for_create=exc.HTTPCreated.code)),
        ('local',
         dict(network_type='local',
              expected_code=exc.HTTPBadRequest.code,
              expected_code_for_create=exc.HTTPBadRequest.code)),
    ]

    def setUp(self):
        ext_mgr = test_l3.L3TestExtensionManager()
        super(TestMidonetRouterML2, self).setUp(ext_mgr=ext_mgr)
        self.ext_api = test_extensions.setup_extensions_middleware(ext_mgr)

    def test_router_gateway_incompatible_network_for_create(self):
        if self.network_type == 'uplink':
            self.skipTest('This test case is not appropriate for uplink')
        net_param = {
            pnet.NETWORK_TYPE: self.network_type,
            external_net.EXTERNAL: True,
            'arg_list': (pnet.NETWORK_TYPE, external_net.EXTERNAL),
        }
        with self.network(**net_param) as net, \
                self.subnet(network=net):
            gw_info = {
                'network_id': net['network']['id'],
            }
            res = self._create_router(self.fmt, tenant_id=None,
                                      arg_list=('external_gateway_info',),
                                      external_gateway_info=gw_info)
            self.assertEqual(self.expected_code_for_create, res.status_int)

    def test_router_gateway_incompatible_network_for_update(self):
        if self.network_type == 'uplink':
            self.skipTest('This test case is not appropriate for uplink')
        net_param = {
            pnet.NETWORK_TYPE: self.network_type,
            external_net.EXTERNAL: True,
            'arg_list': (pnet.NETWORK_TYPE, external_net.EXTERNAL),
        }
        with self.network(**net_param) as net, \
                self.subnet(network=net), \
                self.router() as r:
            self._add_external_gateway_to_router(
                router_id=r['router']['id'],
                network_id=net['network']['id'],
                expected_code=self.expected_code)

    def test_router_interface_incompatible_network(self):
        net_param = {
            pnet.NETWORK_TYPE: self.network_type,
            'arg_list': (pnet.NETWORK_TYPE,),
        }
        with self.network(**net_param) as net, \
                self.subnet(network=net) as subnet, \
                self.router() as r:
            self._router_interface_action(
                'add', r['router']['id'], subnet['subnet']['id'], None,
                expected_code=self.expected_code)
