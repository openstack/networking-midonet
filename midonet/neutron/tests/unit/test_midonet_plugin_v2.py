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
import datetime
import functools
import mock
from sqlalchemy.orm import sessionmaker
import testscenarios
import testtools
from webob import exc

from midonet.neutron.common import config  # noqa
from midonet.neutron.common import constants as m_const
from midonet.neutron.db import agent_membership_db  # noqa
from midonet.neutron.db import data_state_db
from midonet.neutron.db import data_version_db as dv_db
from midonet.neutron.db import port_binding_db  # noqa
from midonet.neutron.db import provider_network_db  # noqa
from midonet.neutron.db import task_db  # noqa
from midonet.neutron.tests.unit import test_midonet_plugin as test_mn_plugin
from neutron import context
from neutron.db import api as db_api
from neutron.extensions import portbindings
from neutron.extensions import portsecurity as psec
from neutron.extensions import providernet as pnet
from neutron.extensions import securitygroup as sg
from neutron import manager
from neutron.plugins.common import constants as p_const
from neutron.tests.unit import _test_extension_portbindings as test_bindings
from neutron.tests.unit.api import test_extensions
from neutron.tests.unit.db import test_allowedaddresspairs_db as test_addr
from neutron.tests.unit.db import test_db_base_plugin_v2 as test_plugin
from neutron.tests.unit.extensions import test_agent
from neutron.tests.unit.extensions import test_extra_dhcp_opt as test_dhcpopts
from neutron.tests.unit.extensions import test_extraroute as test_ext_route
from neutron.tests.unit.extensions import test_l3_ext_gw_mode as test_gw_mode
from neutron.tests.unit.extensions import test_portsecurity as test_psec
from neutron.tests.unit.extensions import test_securitygroup as test_sg
from neutron.tests.unit import testlib_api

from oslo_config import cfg
from oslo_utils import uuidutils


load_tests = testscenarios.load_tests_apply_scenarios


PLUGIN_NAME = 'midonet.neutron.plugin_v2.MidonetPluginV2'


class MidonetPluginConf(object):
    """Plugin configuration shared across the unit and functional tests.
    """

    plugin_name = PLUGIN_NAME

    @staticmethod
    def setUp(test_case, parent_setup=None):
        """Perform additional configuration around the parent's setUp."""
        cfg.CONF.set_override('client', test_mn_plugin.TEST_MN_CLIENT,
                              group='MIDONET')
        if parent_setup:
            parent_setup()


class MidonetPluginV2TestCase(test_plugin.NeutronDbPluginV2TestCase):

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
    pass


class TestMidonetPortBinding(MidonetPluginV2TestCase,
                             test_bindings.PortBindingsTestCase):

    VIF_TYPE = m_const.VIF_TYPE_MIDONET
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
        keys = [(portbindings.PROFILE, {'interface_name': 'if_name'}),
                (portbindings.HOST_ID, 'host')]
        with self.port_with_binding_profile() as port:
            for k, v in keys:
                self.assertEqual(v, port['port'][k])

    def test_create_mido_portbinding_no_profile_specified(self):
        with self.port() as port:
            self.assertIsNone(port['port'][portbindings.PROFILE])

    def test_create_mido_portbinding_no_host_binding(self):
        # Create a binding when there is no host binding.  This should throw
        # an error.
        with self.network() as net:
            args = {'port': {'tenant_id': net['network']['tenant_id'],
                             'network_id': net['network']['id'],
                             portbindings.PROFILE:
                                 {'interface_name': 'if_name'},
                             portbindings.HOST_ID: None}}
            req = self.new_create_request('ports', args, self.fmt)
            res = req.get_response(self.api)
            self.assertEqual(400, res.status_int)

    def test_create_mido_portbinding_no_interface(self):
        # Create binding with no interface name.  Should return an error.
        with self.network() as net:
            args = {'port': {'tenant_id': net['network']['tenant_id'],
                             'network_id': net['network']['id'],
                             portbindings.PROFILE: {'foo': ''},
                             portbindings.HOST_ID: 'host'}}
            req = self.new_create_request('ports', args, self.fmt)
            res = req.get_response(self.api)
            self.assertEqual(400, res.status_int)

    def test_create_mido_portbinding_bad_interface(self):
        # Create binding with a bad interface name.  Should return an error.
        with self.network() as net:
            args = {'port': {'tenant_id': net['network']['tenant_id'],
                             'network_id': net['network']['id'],
                             portbindings.PROFILE: {'interface_name': ''},
                             portbindings.HOST_ID: 'host'}}
            req = self.new_create_request('ports', args, self.fmt)
            res = req.get_response(self.api)
            self.assertEqual(400, res.status_int)

    def test_update_mido_portbinding(self):
        keys = [(portbindings.HOST_ID, 'host2'),
                (portbindings.PROFILE, {'interface_name': 'if_name2'}),
                ('admin_state_up', False),
                ('name', 'test_port2')]
        with self.port_with_binding_profile() as port:
            args = {
                'port': {portbindings.PROFILE: {'interface_name': 'if_name2'},
                         portbindings.HOST_ID: 'host2',
                         'admin_state_up': False,
                         'name': 'test_port2'}}
            req = self.new_update_request('ports', args, port['port']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.api))
            for k, v in keys:
                self.assertEqual(v, res['port'][k])

    def test_update_mido_portbinding_no_profile_specified(self):
        # Modify binding without specifying the profile.
        keys = [(portbindings.HOST_ID, 'host2'),
                (portbindings.PROFILE, {'interface_name': 'if_name'}),
                ('admin_state_up', False),
                ('name', 'test_port2')]
        with self.port_with_binding_profile() as port:
            args = {'port': {portbindings.HOST_ID: 'host2',
                             'admin_state_up': False,
                             'name': 'test_port2'}}
            req = self.new_update_request('ports', args, port['port']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.api))
            for k, v in keys:
                self.assertEqual(v, res['port'][k])

    def test_update_mido_portbinding_no_host_binding(self):
        # Update a binding when there is no host binding.  This should throw
        # an error.
        with self.port() as port:
            args = {
                'port': {portbindings.PROFILE: {'interface_name': 'if_name2'}}}
            req = self.new_update_request('ports', args, port['port']['id'])
            res = req.get_response(self.api)
            self.assertEqual(400, res.status_int)

    def test_update_mido_portbinding_unbind(self):
        # Unbinding a bound port
        with self.port_with_binding_profile() as port:
            args = {'port': {portbindings.PROFILE: None}}
            req = self.new_update_request('ports', args, port['port']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.api))
            self.assertIsNone(res['port'][portbindings.PROFILE])

    def test_update_mido_portbinding_unbind_already_unbound(self):
        # Unbinding an unbound port results in no-op
        with self.port() as port:
            args = {'port': {portbindings.PROFILE: None}}
            req = self.new_update_request('ports', args, port['port']['id'])
            # Success with profile set to None
            res = self.deserialize(self.fmt, req.get_response(self.api))
            self.assertIsNone(res['port'][portbindings.PROFILE])

    def test_update_mido_portbinding_no_interface(self):
        # Update binding with no interface name.  Should return an error.
        with self.port_with_binding_profile() as port:
            args = {
                'port': {portbindings.PROFILE: {'foo': ''}}}
            req = self.new_update_request('ports', args, port['port']['id'])
            res = req.get_response(self.api)
            self.assertEqual(400, res.status_int)

    def test_update_mido_portbinding_bad_interface(self):
        # Update binding with a bad interface name.  Should return an error.
        with self.port_with_binding_profile() as port:
            args = {
                'port': {portbindings.PROFILE: {'interface_name': ''}}}
            req = self.new_update_request('ports', args, port['port']['id'])
            res = req.get_response(self.api)
            self.assertEqual(400, res.status_int)


class TestMidonetExtGwMode(test_gw_mode.ExtGwModeIntTestCase,
                           MidonetPluginV2TestCase):

    pass


class TestMidonetExtraDHCPOpts(test_dhcpopts.TestExtraDhcpOpt,
                               MidonetPluginV2TestCase):

    pass


class TestMidonetL3NatExtraRoute(test_ext_route.ExtraRouteDBIntTestCase,
                                 MidonetPluginV2TestCase):

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


class TestMidonetDataState(testlib_api.SqlTestCase):

    def setUp(self):
        super(TestMidonetDataState, self).setUp()
        self.session = self.get_session()
        self.session.add(data_state_db.DataState(
            updated_at=datetime.datetime.utcnow(),
            readonly=False))

    def get_session(self):
        engine = db_api.get_engine()
        Session = sessionmaker(bind=engine)
        return Session()

    def test_data_show(self):
        ds = data_state_db.get_data_state(self.session)
        self.assertTrue(ds.id is not None)

    def test_data_state_readonly(self):
        data_state_db.set_readonly(self.session)
        ds = data_state_db.get_data_state(self.session)
        self.assertTrue(ds.readonly)
        # TODO(Joe) - creating tasks should fail here. Implement
        # with further task_db changes coming in data sync
        data_state_db.set_readwrite(self.session)
        ds = data_state_db.get_data_state(self.session)
        self.assertTrue(not ds.readonly)


class TestMidonetAgent(MidonetPluginV2TestCase,
                       test_agent.AgentDBTestMixIn):

    def setUp(self):
        super(TestMidonetAgent, self).setUp()
        self.adminContext = context.get_admin_context()
        ext_mgr = test_agent.AgentTestExtensionManager()
        self.ext_api = test_extensions.setup_extensions_middleware(ext_mgr)

    def test_list_agents_including_midonet_agents(self):
        agents = self._register_agent_states()
        agent1 = {
            'id': uuidutils.generate_uuid(),
            'binary': 'midolman',
            'admin_state_up': True,
            'host': 'midohostA',
            'agent_type': 'Midonet Agent'}

        agent2 = {
            'id': uuidutils.generate_uuid(),
            'binary': 'midolman',
            'admin_state_up': False,
            'host': 'midohostB',
            'agent_type': 'Midonet Agent'}

        self.client_mock.get_agents.return_value = [agent1, agent2]

        res = self._list('agents')
        agent_ids = [ag['id'] for ag in res['agents']]

        self.assertEqual(len(agents) + 2, len(res['agents']))
        self.assertIn(agent1['id'], agent_ids)
        self.assertIn(agent2['id'], agent_ids)

    def test_show_midonet_agent(self):
        self._register_agent_states()

        agent_id = uuidutils.generate_uuid()
        self.client_mock.get_agent.return_value = {
            'id': agent_id,
            'binary': 'midolman',
            'admin_state_up': True,
            'host': 'midohostA',
            'agent_type': 'Midonet Agent'}

        agent = self._show('agents', agent_id)
        self.assertEqual(agent_id, agent['agent']['id'])

    def test_show_non_existent_midonet_agent(self):
        self._register_agent_states()

        self.client_mock.get_agent.return_value = None

        self._show('agents', uuidutils.generate_uuid(),
                   expected_code=exc.HTTPNotFound.code)


class TestMidonetDataVersion(testlib_api.SqlTestCase):

    def get_session(self):
        engine = db_api.get_engine()
        Session = sessionmaker(bind=engine)
        return Session()

    def test_create_version(self):
        session = self.get_session()
        dv_db.create_data_version(session)
        version = dv_db.get_last_version(session)
        self.assertEqual(1, version.id)
        self.assertEqual(dv_db.STARTED, version.sync_tasks_status)

    def _test_version_status(self, version_update_func, status):
        session = self.get_session()
        dv_db.create_data_version(session)
        version = dv_db.get_last_version(session)
        self.assertEqual(dv_db.STARTED, version.sync_tasks_status)
        version_update_func(session)
        version = dv_db.get_last_version(session)
        self.assertEqual(status, version.sync_tasks_status)

    def test_update_version_status_completed(self):
        self._test_version_status(dv_db.complete_last_version,
                                  dv_db.COMPLETED)

    def test_update_version_status_error(self):
        self._test_version_status(dv_db.error_last_version,
                                  dv_db.ERROR)

    def test_update_version_status_aborted(self):
        self._test_version_status(dv_db.abort_last_version,
                                  dv_db.ABORTED)


class TestMidonetProviderNet(MidonetPluginV2TestCase):

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
        keys = [(pnet.NETWORK_TYPE, m_const.TYPE_UPLINK),
                ('name', 'name1')]
        with self.provider_net() as net:
            for k, v in keys:
                self.assertEqual(v, net['network'][k])

    def test_create_provider_net_with_bogus_type(self):
        # Create with a bogus network type
        with testtools.ExpectedException(exc.HTTPClientError), \
            self.provider_net(net_type="random"):
            pass

    def test_create_provider_net_with_local(self):
        # We map well-known types to the default value
        # REVISIT(yamamoto): Clean this up once horizon is fixed
        with self.provider_net(net_type=p_const.TYPE_LOCAL) as net:
            self.assertNotIn(pnet.NETWORK_TYPE, net['network'])

    def test_create_provider_net_with_flat(self):
        with testtools.ExpectedException(exc.HTTPClientError), \
            self.provider_net(net_type=p_const.TYPE_FLAT):
            pass

    def test_create_provider_net_with_gre(self):
        with testtools.ExpectedException(exc.HTTPClientError), \
            self.provider_net(net_type=p_const.TYPE_GRE):
            pass

    def test_create_provider_net_with_vlan(self):
        with testtools.ExpectedException(exc.HTTPClientError), \
            self.provider_net(net_type=p_const.TYPE_VLAN):
            pass

    def test_create_provider_net_with_vxlan(self):
        with testtools.ExpectedException(exc.HTTPClientError), \
            self.provider_net(net_type=p_const.TYPE_VXLAN):
            pass

    def test_create_provider_net_with_geneve(self):
        with testtools.ExpectedException(exc.HTTPClientError), \
            self.provider_net(net_type=p_const.TYPE_GENEVE):
            pass

    def test_create_provider_net_with_midonet(self):
        with self.provider_net(net_type=m_const.TYPE_MIDONET) as net:
            self.assertNotIn(pnet.NETWORK_TYPE, net['network'])

    def test_create_provider_net_without_type(self):
        args = {'network': {'tenant_id': 'admin'}}
        req = self.new_create_request('networks', args, self.fmt)
        res = req.get_response(self.api)
        self.assertEqual(201, res.status_int)
        net_res = self.deserialize(self.fmt, res)
        self.assertNotIn(pnet.NETWORK_TYPE, net_res['network'])

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


class TestMidonetAllowedAddressPair(test_addr.TestAllowedAddressPairs,
                                    MidonetPluginV2TestCase):
    pass


class TestMidonetPortSecurity(test_psec.TestPortSecurity,
                              MidonetPluginV2TestCase):
    pass


class TestMidonetPortSecurityKludge(MidonetPluginV2TestCase):
    # Ensure that a lack of portsecurity db row is considered as
    # the API default. (true)

    scenarios = testscenarios.multiply_scenarios(
        [
            ('have port psec row',
             dict(mock_port=False)),
            ('no port psec row',
             dict(mock_port=True)),
        ], [
            ('have network psec row',
             dict(mock_network=False)),
            ('no network psec row',
             dict(mock_network=True)),
        ]
    )

    @contextlib.contextmanager
    def _do_mock(self, plugin):
        port_mock = mock.patch.object(plugin,
            '_process_port_port_security_create',
            auto_spec=True,
            return_value={})
        network_mock = mock.patch.object(plugin,
            '_process_network_port_security_create',
            auto_spec=True,
            return_value={})
        if self.mock_port:
            port_mock.start()
        if self.mock_network:
            network_mock.start()
        yield (port_mock, network_mock)
        if self.mock_network:
            network_mock.stop()
        if self.mock_port:
            port_mock.stop()

    def test_get_network(self):
        ctx = context.get_admin_context()
        plugin = manager.NeutronManager.get_plugin()
        with self._do_mock(plugin), self.network() as net:
            pass
        net2 = plugin.get_network(ctx, net['network']['id'])
        self.assertTrue(net2[psec.PORTSECURITY])

    def test_get_port(self):
        ctx = context.get_admin_context()
        plugin = manager.NeutronManager.get_plugin()
        with self._do_mock(plugin), self.port() as port:
            pass
        port2 = plugin.get_port(ctx, port['port']['id'])
        self.assertTrue(port2[psec.PORTSECURITY])

    def test_update_network(self):
        ctx = context.get_admin_context()
        plugin = manager.NeutronManager.get_plugin()
        with self._do_mock(plugin), self.port() as port:
            pass
        net2 = plugin.update_network(ctx, port['port']['network_id'],
                                     {'network': {psec.PORTSECURITY: False}})
        self.assertFalse(net2[psec.PORTSECURITY])
        net3 = plugin.get_network(ctx, port['port']['network_id'])
        self.assertFalse(net3[psec.PORTSECURITY])

    def test_update_port(self):
        ctx = context.get_admin_context()
        plugin = manager.NeutronManager.get_plugin()
        with self._do_mock(plugin), self.port() as port:
            pass
        port2 = plugin.update_port(ctx, port['port']['id'],
                                   {'port': {psec.PORTSECURITY: False,
                                             sg.SECURITYGROUPS: []}})
        self.assertFalse(port2[psec.PORTSECURITY])
        port3 = plugin.get_port(ctx, port['port']['id'])
        self.assertFalse(port3[psec.PORTSECURITY])
