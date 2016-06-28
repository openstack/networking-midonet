# Copyright (C) 2012 Midokura Japan K.K.
# Copyright (C) 2013 Midokura PTE LTD
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
import testtools
from webob import exc

from midonet.neutron.client import base as cli_base
# Import all data models
from midonet.neutron.common import config  # noqa
from midonet.neutron.db.migration.models import head  # noqa

from neutron.common import constants as n_const
from neutron import context
from neutron import manager
from neutron.plugins.common import constants as p_const
from neutron.tests.unit.db import test_db_base_plugin_v2 as test_plugin
from neutron.tests.unit.extensions import test_extra_dhcp_opt as test_dhcpopts
from neutron.tests.unit.extensions import test_l3
from neutron.tests.unit.extensions import test_l3_ext_gw_mode as test_gw_mode
from neutron.tests.unit.extensions import test_securitygroup as test_sg

from oslo_config import cfg


PLUGIN_NAME = 'midonet.neutron.plugin_v1.MidonetPluginV2'
TEST_MN_CLIENT = ('midonet.neutron.tests.unit.test_midonet_plugin.'
                  'NoopMidonetClient')
FAKE_CIDR = '10.0.0.0/24'
FAKE_IP = '10.0.0.240'


class NoopMidonetClient(cli_base.MidonetClientBase):
    """Dummy midonet client used for the unit tests"""
    pass


class MidonetPluginConf(object):
    """Plugin configuration shared across the unit and functional tests.
    """

    plugin_name = PLUGIN_NAME

    @staticmethod
    def setUp(test_case, parent_setup=None):
        """Perform additional configuration around the parent's setUp."""
        cfg.CONF.set_override('client', TEST_MN_CLIENT, group='MIDONET')
        if parent_setup:
            parent_setup()


class MidonetPluginV2TestCase(test_plugin.NeutronDbPluginV2TestCase):

    def setup_parent(self, service_plugins=None, ext_mgr=None):

        # Set up mock for the midonet client to be made available in tests
        patcher = mock.patch(TEST_MN_CLIENT)
        self.client_mock = mock.MagicMock()
        patcher.start().return_value = self.client_mock

        # Ensure that the parent setup can be called without arguments
        # by the common configuration setUp.
        parent_setup = functools.partial(
            super(MidonetPluginV2TestCase, self).setUp,
            plugin=MidonetPluginConf.plugin_name,
            service_plugins=service_plugins,
            ext_mgr=ext_mgr,
        )
        MidonetPluginConf.setUp(self, parent_setup)

    def setUp(self, plugin=None, service_plugins=None, ext_mgr=None):
        self.setup_parent(service_plugins=service_plugins, ext_mgr=ext_mgr)


class TestMidonetNetworksV2(MidonetPluginV2TestCase,
                            test_plugin.TestNetworksV2):
    pass


class TestMidonetSecurityGroup(test_sg.TestSecurityGroups,
                               MidonetPluginV2TestCase):
    pass


class TestMidonetSubnetsV2(MidonetPluginV2TestCase,
                           test_plugin.TestSubnetsV2):
    pass


class TestMidonetPortsV2(MidonetPluginV2TestCase,
                         test_plugin.TestPortsV2):

    def test_update_dhcp_port_with_exceeding_fixed_ips(self):
        # MidoNet doesn't support updating dhcp port's fixed-ips.
        pass

    def test_update_port_error_change_resource_status_to_error(self):
        self.client_mock.update_port_postcommit.side_effect = (
            Exception("Fake Error"))
        with self.subnet(cidr=FAKE_CIDR) as sub:
            with self.port(subnet=sub) as port:
                data = {'port': {'fixed_ips':
                        [{'ip_address': FAKE_IP,
                          'subnet_id': sub['subnet']['id']}]}}
                req = self.new_update_request(
                        'ports', data, port['port']['id'])
                res = req.get_response(self.api)
                self.assertEqual(exc.HTTPInternalServerError.code,
                        res.status_int)
                req = self.new_show_request('ports', port['port']['id'])
                res = self.deserialize(self.fmt,
                        req.get_response(self.api))
                self.assertEqual(n_const.PORT_STATUS_ERROR,
                        res['port']['status'])

    def test_create_port_with_admin_state_up_false(self):
        with self.subnet(cidr=FAKE_CIDR) as sub:
            with self.port(subnet=sub,
                    admin_state_up=False) as port:
                req = self.new_show_request('ports', port['port']['id'])
                res = self.deserialize(self.fmt,
                        req.get_response(self.api))
                self.assertEqual(n_const.PORT_STATUS_DOWN,
                        res['port']['status'])

    def test_update_port_admin_state_up_to_false_and_true(self):
        with self.subnet(cidr=FAKE_CIDR) as sub:
            with self.port(subnet=sub) as port:
                data = {'port': {'admin_state_up': False}}
                req = self.new_update_request(
                        'ports', data, port['port']['id'])
                res = req.get_response(self.api)
                res = self.deserialize(self.fmt,
                        req.get_response(self.api))
                self.assertEqual(n_const.PORT_STATUS_DOWN,
                                 res['port']['status'])
                data = {'port': {'admin_state_up': True}}
                req = self.new_update_request(
                        'ports', data, port['port']['id'])
                res = req.get_response(self.api)
                res = self.deserialize(self.fmt,
                        req.get_response(self.api))
                self.assertEqual(n_const.PORT_STATUS_ACTIVE,
                                 res['port']['status'])


class TestMidonetExtGwMode(test_gw_mode.ExtGwModeIntTestCase,
                           MidonetPluginV2TestCase):

    pass


class TestMidonetExtraDHCPOpts(test_dhcpopts.TestExtraDhcpOpt,
                               MidonetPluginV2TestCase):

    pass


class TestMidonetL3NatDBIntTest(test_l3.L3NatDBIntTestCase,
                                MidonetPluginV2TestCase):

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
            plugin = manager.NeutronManager.get_plugin()
            l3_plugin = manager.NeutronManager.get_service_plugins().get(
                p_const.L3_ROUTER_NAT)
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
