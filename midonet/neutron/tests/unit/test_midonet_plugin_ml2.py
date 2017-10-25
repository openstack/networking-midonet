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
import functools

import mock
import testscenarios
import testtools
from webob import exc

from oslo_config import cfg

from neutron_lib.api.definitions import external_net
from neutron_lib.api.definitions import portbindings
from neutron_lib.api.definitions import provider_net as pnet
from neutron_lib import constants as n_const
from neutron_lib import context
from neutron_lib.plugins import constants as plugin_constants
from neutron_lib.plugins import directory

from neutron.tests.unit import _test_extension_portbindings as test_bindings
from neutron.tests.unit.api import test_extensions
from neutron.tests.unit.db import test_allowedaddresspairs_db as test_addr
from neutron.tests.unit.db import test_db_base_plugin_v2 as test_plugin
from neutron.tests.unit.extensions import test_extra_dhcp_opt as test_dhcpopts
from neutron.tests.unit.extensions import test_extraroute as test_ext_route
from neutron.tests.unit.extensions import test_l3
from neutron.tests.unit.extensions import test_l3_ext_gw_mode as test_gw_mode
from neutron.tests.unit.extensions import test_portsecurity as test_psec
from neutron.tests.unit.extensions import test_securitygroup as test_sg

from midonet.neutron.common import constants as m_const
from midonet.neutron.tests.unit import test_midonet_plugin as test_mn_plugin

load_tests = testscenarios.load_tests_apply_scenarios

PLUGIN_NAME = 'neutron.plugins.ml2.plugin.Ml2Plugin'

cfg.CONF.import_group('ml2', 'neutron.conf.plugins.ml2.config')


class MidonetPluginConf(object):
    """Plugin configuration shared across the unit and functional tests."""

    plugin_name = PLUGIN_NAME

    @staticmethod
    def setUp(test_case, parent_setup=None):
        """Perform additional configuration around the parent's setUp."""
        ovo_push_interface_p = mock.patch(
            'neutron.plugins.ml2.ovo_rpc.OVOServerRpcInterface')
        ovo_push_interface_p.start()
        cfg.CONF.set_override('client', test_mn_plugin.TEST_MN_CLIENT,
                              group='MIDONET')
        cfg.CONF.set_override('type_drivers',
                              ['midonet', 'uplink', 'local'],
                              group='ml2')
        cfg.CONF.set_override('mechanism_drivers',
                              ['midonet', 'openvswitch'],
                              group='ml2')
        cfg.CONF.set_override('tenant_network_types',
                              ['midonet'],
                              group='ml2')
        cfg.CONF.set_override('extension_drivers',
                              ['port_security'],
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
            l3_plugin = directory.get_plugin(plugin_constants.L3)
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
            private_sub = {
                'subnet': {
                    'id': p['port']['fixed_ips'][0]['subnet_id']
                }
            }
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
                self.assertEqual(
                    n_const.FLOATINGIP_STATUS_ERROR,
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


class TestMidonetProviderNet(MidonetPluginML2TestCase):

    @contextlib.contextmanager
    def provider_net(self, name='name1', net_type=m_const.TYPE_UPLINK,
                     admin_state_up=True):
        args = {pnet.NETWORK_TYPE: net_type,
                'tenant_id': 'admin'}
        net = self._make_network(self.fmt, name, admin_state_up,
                                 arg_list=(pnet.NETWORK_TYPE, 'tenant_id'),
                                 **args)
        yield net

    def test_create_provider_net(self):
        keys = {pnet.NETWORK_TYPE: m_const.TYPE_UPLINK,
                'name': 'name1'}
        with self.provider_net() as net:
            self.assertDictSupersetOf(keys, net['network'])

    def test_create_provider_net_with_bogus_type(self):
        # Create with a bogus network type
        with testtools.ExpectedException(exc.HTTPClientError), \
                self.provider_net(net_type="random"):
            pass

    def test_create_provider_net_with_local(self):
        with self.provider_net(net_type=n_const.TYPE_LOCAL) as net:
            self.assertEqual(n_const.TYPE_LOCAL,
                             net['network'][pnet.NETWORK_TYPE])

    def test_create_provider_net_with_flat(self):
        with testtools.ExpectedException(exc.HTTPClientError), \
                self.provider_net(net_type=n_const.TYPE_FLAT):
            pass

    def test_create_provider_net_with_gre(self):
        with testtools.ExpectedException(exc.HTTPClientError), \
                self.provider_net(net_type=n_const.TYPE_GRE):
            pass

    def test_create_provider_net_with_vlan(self):
        with testtools.ExpectedException(exc.HTTPClientError), \
                self.provider_net(net_type=n_const.TYPE_VLAN):
            pass

    def test_create_provider_net_with_vxlan(self):
        with testtools.ExpectedException(exc.HTTPClientError), \
                self.provider_net(net_type=n_const.TYPE_VXLAN):
            pass

    def test_create_provider_net_with_geneve(self):
        with testtools.ExpectedException(exc.HTTPClientError), \
                self.provider_net(net_type=n_const.TYPE_GENEVE):
            pass

    def test_create_provider_net_with_midonet(self):
        with self.provider_net(net_type=m_const.TYPE_MIDONET) as net:
            self.assertEqual(m_const.TYPE_MIDONET,
                             net['network'][pnet.NETWORK_TYPE])

    def test_create_provider_net_without_type(self):
        args = {'network': {'tenant_id': 'admin'}}
        req = self.new_create_request('networks', args, self.fmt)
        res = req.get_response(self.api)
        self.assertEqual(201, res.status_int)
        net_res = self.deserialize(self.fmt, res)
        self.assertEqual(m_const.TYPE_MIDONET,
                         net_res['network'][pnet.NETWORK_TYPE])

    def test_update_provider_net_unsupported(self):
        # Update including the network type is not supported
        with self.provider_net() as net:
            args = {"network": {"name": "foo",
                                pnet.NETWORK_TYPE: m_const.TYPE_UPLINK}}
            req = self.new_update_request('networks', args,
                                          net['network']['id'])
            res = req.get_response(self.api)
            self.assertEqual(400, res.status_int)

    def test_delete_provider_net(self):
        with self.provider_net() as net:
            req = self.new_delete_request('networks', net['network']['id'])
            res = req.get_response(self.api)
            self.assertEqual(exc.HTTPNoContent.code, res.status_int)

    def test_show_provider_net(self):
        with self.provider_net() as net:
            req = self.new_show_request('networks', net['network']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.api))
            self.assertEqual(m_const.TYPE_UPLINK,
                             res['network'][pnet.NETWORK_TYPE])

    def test_list_provider_nets(self):
        # Create two uplink prov nets and retrieve them
        with self.provider_net():
            with self.provider_net(name="net2"):
                req = self.new_list_request('networks')
                res = self.deserialize(
                    self.fmt, req.get_response(self.api))
                self.assertEqual(2, len(res['networks']))
                for res_net in res['networks']:
                    self.assertEqual(m_const.TYPE_UPLINK,
                                     res_net[pnet.NETWORK_TYPE])

    def test_list_provider_nets_filtered_by_invalid_type(self):
        # Search a list of two provider networks with type uplink and type vlan
        with self.provider_net(name="net2"):
            with self.provider_net(name="net2"):
                params_str = "%s=%s" % (pnet.NETWORK_TYPE, 'vlan')
                req = self.new_list_request('networks', None,
                                            params=params_str)
                res = self.deserialize(
                    self.fmt, req.get_response(self.api))
                self.assertEqual(0, len(res['networks']))


class TestMidonetPortBinding(MidonetPluginML2TestCase,
                             test_bindings.PortBindingsTestCase):

    # Test case does not set binding:host_id, so ml2 does not attempt
    # to bind port
    VIF_TYPE = portbindings.VIF_TYPE_UNBOUND
    HAS_PORT_FILTER = True

    @contextlib.contextmanager
    def port_with_binding_profile(self, host='host', if_name='if_name'):
        args = {portbindings.PROFILE: {'interface_name': if_name},
                portbindings.HOST_ID: host}
        with test_plugin.optional_ctx(None, self.subnet) as subnet_to_use:
            net_id = subnet_to_use['subnet']['network_id']
            port = self._make_port(self.fmt, net_id,
                                   arg_list=(portbindings.PROFILE,
                                             portbindings.HOST_ID,), **args)
            yield port

    def test_create_mido_portbinding(self):
        keys = {portbindings.PROFILE: {'interface_name': 'if_name'},
                portbindings.HOST_ID: 'host'}
        with self.port_with_binding_profile() as port:
            self.assertDictSupersetOf(keys, port['port'])

    def test_show_mido_portbinding(self):
        keys = {portbindings.PROFILE: {'interface_name': 'if_name'},
                portbindings.HOST_ID: 'host'}
        with self.port_with_binding_profile() as port:
            self.assertDictSupersetOf(keys, port['port'])
            req = self.new_show_request('ports', port['port']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.api))
            self.assertDictSupersetOf(keys, res['port'])

    def test_create_mido_portbinding_no_profile_specified(self):
        with self.port() as port:
            # NOTE(yamamoto): midonet_v2 returns None where ML2 returns {}.
            self.assertEqual({}, port['port'][portbindings.PROFILE])

    def test_create_mido_portbinding_no_host_binding(self):
        # Create a binding when there is no host binding.
        # ML2 allows it and makes the port UNBOUND.
        # (Unlike midonet_v2, where it fails with 400.)
        with self.network() as net:
            args = {'port': {'tenant_id': net['network']['tenant_id'],
                             'network_id': net['network']['id'],
                             portbindings.PROFILE:
                                 {'interface_name': 'if_name'},
                             portbindings.HOST_ID: None}}
            req = self.new_create_request('ports', args, self.fmt)
            res = req.get_response(self.api)
            self.assertEqual(201, res.status_int)
            result = self.deserialize(self.fmt, res)
            self.assertDictSupersetOf({
                portbindings.PROFILE: {'interface_name': 'if_name'},
                portbindings.VIF_TYPE: portbindings.VIF_TYPE_UNBOUND,
            }, result['port'])

    def test_create_mido_portbinding_no_interface(self):
        # Create binding with no interface name.
        # ML2 allows it.
        # (Unlike midonet_v2, where a non empty profile should always have
        # a valid interface_name and otherwise fails with 400.)
        with self.network() as net:
            args = {'port': {'tenant_id': net['network']['tenant_id'],
                             'network_id': net['network']['id'],
                             portbindings.PROFILE: {'foo': ''},
                             portbindings.HOST_ID: 'host'}}
            req = self.new_create_request('ports', args, self.fmt)
            res = req.get_response(self.api)
            self.assertEqual(201, res.status_int)
            result = self.deserialize(self.fmt, res)
            self.assertDictSupersetOf({
                portbindings.PROFILE: {'foo': ''},
                portbindings.VIF_TYPE: m_const.VIF_TYPE_MIDONET,
            }, result['port'])

    def test_create_mido_portbinding_bad_interface(self):
        # Create binding with a bad interface name.  Should return an error.
        # It succeeds because our mech driver doesn't validate it.
        # (Unlike midonet_v2, where it fails with 400.)
        with self.network() as net:
            args = {'port': {'tenant_id': net['network']['tenant_id'],
                             'network_id': net['network']['id'],
                             portbindings.PROFILE: {'interface_name': ''},
                             portbindings.HOST_ID: 'host'}}
            req = self.new_create_request('ports', args, self.fmt)
            res = req.get_response(self.api)
            self.assertEqual(201, res.status_int)
            result = self.deserialize(self.fmt, res)
            self.assertDictSupersetOf({
                portbindings.PROFILE: {'interface_name': ''},
                portbindings.VIF_TYPE: m_const.VIF_TYPE_MIDONET,
            }, result['port'])

    def test_update_mido_portbinding(self):
        keys = {portbindings.HOST_ID: 'host2',
                portbindings.PROFILE: {'interface_name': 'if_name2'},
                'admin_state_up': False,
                'name': 'test_port2'}
        with self.port_with_binding_profile() as port:
            args = {
                'port': {portbindings.PROFILE: {'interface_name': 'if_name2'},
                         portbindings.HOST_ID: 'host2',
                         'admin_state_up': False,
                         'name': 'test_port2'}}
            req = self.new_update_request('ports', args, port['port']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.api))
            self.assertDictSupersetOf(keys, res['port'])

    def test_update_mido_portbinding_no_profile_specified(self):
        # Modify binding without specifying the profile.
        keys = {portbindings.HOST_ID: 'host2',
                portbindings.PROFILE: {'interface_name': 'if_name'},
                'admin_state_up': False,
                'name': 'test_port2'}
        with self.port_with_binding_profile() as port:
            args = {'port': {portbindings.HOST_ID: 'host2',
                             'admin_state_up': False,
                             'name': 'test_port2'}}
            req = self.new_update_request('ports', args, port['port']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.api))
            self.assertDictSupersetOf(keys, res['port'])

    def test_update_mido_portbinding_no_host_binding(self):
        # Update a binding when there is no host binding.
        # ML2 allows it and makes the port UNBOUND.
        # (Unlike midonet_v2, where it fails with 400.)
        with self.port() as port:
            args = {
                'port': {portbindings.PROFILE: {'interface_name': 'if_name2'}}}
            req = self.new_update_request('ports', args, port['port']['id'])
            res = req.get_response(self.api)
            self.assertEqual(200, res.status_int)
            result = self.deserialize(self.fmt, res)
            self.assertDictSupersetOf({
                portbindings.PROFILE: {'interface_name': 'if_name2'},
                portbindings.VIF_TYPE: portbindings.VIF_TYPE_UNBOUND,
            }, result['port'])

    def test_update_mido_portbinding_unbind(self):
        # Unbinding a bound port
        with self.port_with_binding_profile() as port:
            args = {'port': {portbindings.PROFILE: None}}
            req = self.new_update_request('ports', args, port['port']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.api))
            # NOTE(yamamoto): midonet_v2 returns None where ML2 returns {}.
            self.assertEqual({}, res['port'][portbindings.PROFILE])

    def test_update_mido_portbinding_unbind_already_unbound(self):
        # Unbinding an unbound port results in no-op
        with self.port() as port:
            args = {'port': {portbindings.PROFILE: None}}
            req = self.new_update_request('ports', args, port['port']['id'])
            # Success with profile set to None
            res = self.deserialize(self.fmt, req.get_response(self.api))
            # NOTE(yamamoto): midonet_v2 returns None where ML2 returns {}.
            self.assertEqual({}, res['port'][portbindings.PROFILE])

    def test_update_mido_portbinding_no_interface(self):
        # Update binding with no interface name.
        # ML2 allows it.
        # (Unlike midonet_v2, where a non empty profile should always have
        # a valid interface_name and otherwise fails with 400.)
        with self.port_with_binding_profile() as port:
            args = {
                'port': {portbindings.PROFILE: {'foo': ''}}}
            req = self.new_update_request('ports', args, port['port']['id'])
            res = req.get_response(self.api)
            self.assertEqual(200, res.status_int)
            result = self.deserialize(self.fmt, res)
            self.assertDictSupersetOf({
                portbindings.PROFILE: {'foo': ''},
                portbindings.VIF_TYPE: m_const.VIF_TYPE_MIDONET,
            }, result['port'])

    def test_update_mido_portbinding_bad_interface(self):
        # Update binding with a bad interface name.
        # It succeeds because our mech driver doesn't validate it.
        # (Unlike midonet_v2, where it fails with 400.)
        with self.port_with_binding_profile() as port:
            args = {
                'port': {portbindings.PROFILE: {'interface_name': ''}}}
            req = self.new_update_request('ports', args, port['port']['id'])
            res = req.get_response(self.api)
            self.assertEqual(200, res.status_int)
            result = self.deserialize(self.fmt, res)
            self.assertDictSupersetOf({
                portbindings.PROFILE: {'interface_name': ''},
                portbindings.VIF_TYPE: m_const.VIF_TYPE_MIDONET,
            }, result['port'])


class TestMidonetAllowedAddressPair(test_addr.TestAllowedAddressPairs,
                                    MidonetPluginML2TestCase):
    pass


class TestMidonetPortSecurity(test_psec.TestPortSecurity,
                              MidonetPluginML2TestCase):
    pass


class TestMidonetExtGwMode(test_gw_mode.ExtGwModeIntTestCase,
                           MidonetPluginML2TestCase):

    pass


class TestMidonetExtraDHCPOpts(test_dhcpopts.TestExtraDhcpOpt,
                               MidonetPluginML2TestCase):

    pass
