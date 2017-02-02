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
import testtools
from webob import exc

from oslo_config import cfg

from neutron_lib.api.definitions import provider_net as pnet
from neutron_lib import constants as n_const
from neutron_lib.plugins import directory

from neutron import context
from neutron.extensions import external_net
from neutron.tests.unit.api import test_extensions
from neutron.tests.unit.db import test_db_base_plugin_v2 as test_plugin
from neutron.tests.unit.extensions import test_extraroute as test_ext_route
from neutron.tests.unit.extensions import test_l3
from neutron.tests.unit.extensions import test_securitygroup as test_sg

from midonet.neutron.tests.unit import test_midonet_plugin as test_mn_plugin

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
        self.client_mock = mock.Mock()
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


class TestMidonetL3NatExtraRoute(test_ext_route.ExtraRouteDBIntTestCase,
                                 MidonetPluginML2TestCase):

    def test_router_update_gateway_upon_subnet_create_max_ips_ipv6(self):
        # MidoNet doesn't support IPv6.
        # MidoNet doesn't support fixed_ips updates on a router gateway port.
        pass

    def test_router_remove_ipv6_subnet_from_interface(self):
        # MidoNet doesn't support IPv6.
        # This specific case examines _add_interface_by_subnet,
        # which ends up with updating the existing router interface port's
        # fixed-ips.
        pass

    def test_router_add_interface_multiple_ipv6_subnets_same_net(self):
        # MidoNet doesn't support IPv6.
        # This specific case examines _add_interface_by_subnet,
        # which ends up with updating the existing router interface port's
        # fixed-ips.
        pass

    def test_router_update_gateway_add_multiple_prefixes_ipv6(self):
        # MidoNet doesn't support IPv6.
        # This specific case examines updating a router's ext_ips,
        # which ends up with updating its gateway port's fixed-ips.
        pass

    def test_router_update_gateway_upon_subnet_create_ipv6(self):
        # MidoNet doesn't support IPv6.
        # Even for IPv4, with the reference implementation, create_subnet
        # can ends up with adding an IP to the router's gateway port.
        # However, it can't happen for us because we reject a gateway port
        # without IP addresses.  ("No IPs assigned to the gateway port")
        pass

    def test_router_update_gateway_with_different_external_subnet(self):
        # This specific case examines updating a router's ext_ips,
        # which ends up with updating its gateway port's fixed-ips.
        pass

    def test_router_add_gateway_no_subnet(self):
        # Midonet does not support the case where a gateway is set
        # without a subnet, therefore we don't want to test this.
        pass

    def test_create_floatingip_ipv6_only_network_returns_400(self):
        # MidoNet supports floating IPv6, where it is possible to assign a
        # floating IP on an external network with only an IPv6 subnet.
        pass

    def test_create_router_no_gateway_ip(self):
        with self.network() as net:
            self._set_net_external(net['network']['id'])
            router_data = {'router': {
                'tenant_id': 'tenant_one',
                'external_gateway_info': {
                    'network_id': net['network']['id']}}}
            router_req = self.new_create_request('routers', router_data,
                                                 self.fmt)
            res = router_req.get_response(self.ext_api)
            self.assertEqual(400, res.status_int)

    def test_add_router_interface_by_port_failure(self):
        class _MyException(Exception):
            pass

        with self.port() as port, self.router() as router:
            ctx = context.get_admin_context()
            plugin = directory.get_plugin()
            l3_plugin = directory.get_plugin(n_const.L3)
            router_id = router['router']['id']
            port_id = port['port']['id']
            interface_info = {
                'port_id': port_id,
            }
            with mock.patch.object(l3_plugin.client,
                                   'add_router_interface_postcommit',
                                   auto_spec=True,
                                   side_effect=_MyException), \
                testtools.ExpectedException(_MyException):
                l3_plugin.add_router_interface(ctx, router_id, interface_info)
            port2 = plugin.get_port(ctx, port_id)
            self.assertEqual(port_id, port2['id'])

    def test_update_floatingip_error_change_resource_status_to_error(self):
        self.client_mock.update_floatingip_postcommit.side_effect = (
            Exception("Fake Error"))
        with self.port() as p:
            private_sub = {'subnet': {'id':
                    p['port']['fixed_ips'][0]['subnet_id']}}
            with self.floatingip_no_assoc(private_sub) as fip:
                data = {'floatingip': {'port_id': p['port']['id']}}
                req = self.new_update_request('floatingips',
                                              data,
                                              fip['floatingip']['id'])
                res = req.get_response(self.ext_api)
                self.assertEqual(exc.HTTPInternalServerError.code,
                                 res.status_int)
                req = self.new_show_request(
                        'floatingips', fip['floatingip']['id'])
                res = self.deserialize(self.fmt,
                                       req.get_response(self.ext_api))
                self.assertEqual(n_const.FLOATINGIP_STATUS_ERROR,
                        res['floatingip']['status'])

    def test_update_router_error_change_resource_status_to_error(self):
        self.client_mock.update_router_postcommit.side_effect = (
            Exception("Fake Error"))
        with self.subnet(cidr='11.0.0.0/24') as pub_sub:
            pub_net = pub_sub['subnet']['network_id']
            self._set_net_external(pub_net)
            with self.router() as r:
                data = {'router':
                        {'external_gateway_info': {'network_id': pub_net}}}
                req = self.new_update_request('routers',
                                              data,
                                              r['router']['id'])
                res = req.get_response(self.ext_api)
                self.assertEqual(exc.HTTPInternalServerError.code,
                                 res.status_int)
                req = self.new_show_request(
                        'routers', r['router']['id'])
                res = self.deserialize(self.fmt,
                                       req.get_response(self.ext_api))
                self.assertEqual('ERROR', res['router']['status'])

    def test_floatingip_via_router_interface_returns_404(self):
        self.skipTest('Not appropriate with router-interface-fip extension.')

    def test_floatingip_via_router_interface_returns_201(self):
        self._test_floatingip_via_router_interface(exc.HTTPCreated.code)

    # NOTE(yamamoto): ML2 no longer uses NeutronDbPluginV2.create_port
    def test_floatingip_with_invalid_create_port(self):
        self._test_floatingip_with_invalid_create_port(PLUGIN_NAME)
