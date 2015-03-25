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

import datetime
import functools

from midonet.neutron.db import agent_membership_db  # noqa
from midonet.neutron.db import data_state_db  # noqa
from midonet.neutron.db import data_version_db as dv_db
from midonet.neutron.db import port_binding_db as pb_db
from midonet.neutron.db import routedserviceinsertion_db  # noqa
from midonet.neutron.db import task_db  # noqa
import mock
from neutron import context
from neutron.db import api as db_api
from neutron.extensions import portbindings
from neutron.tests.unit import _test_extension_portbindings as test_bindings
import neutron.tests.unit.test_agent_ext_plugin as test_agent
import neutron.tests.unit.test_db_plugin as test_plugin
import neutron.tests.unit.test_extension_ext_gw_mode as test_gw_mode
from neutron.tests.unit import test_extension_extradhcpopts as test_dhcpopts
from neutron.tests.unit import test_extension_extraroute as test_ext_route
import neutron.tests.unit.test_extension_security_group as sg
from neutron.tests.unit import test_extensions
import neutron.tests.unit.test_l3_plugin as test_l3_plugin
from neutron.tests.unit import testlib_api
from neutron_lbaas.db.loadbalancer import loadbalancer_db as lb_db  # noqa
from sqlalchemy.orm import sessionmaker
from webob import exc

import sys
sys.modules["midonetclient"] = mock.Mock()
sys.modules["midonetclient.topology"] = mock.Mock()
from midonet.neutron.rpc import topology_client as top  # noqa


PLUGIN_NAME = 'neutron.plugins.midonet.plugin.MidonetPluginV2'


class MidonetPluginConf(object):
    """Plugin configuration shared across the unit and functional tests.
    """

    plugin_name = PLUGIN_NAME

    @staticmethod
    def setUp(test_case, parent_setup=None):
        """Perform additional configuration around the parent's setUp."""
        if parent_setup:
            parent_setup()


class MidonetPluginV2TestCase(test_plugin.NeutronDbPluginV2TestCase):

    def setup_parent(self):
        # Ensure that the parent setup can be called without arguments
        # by the common configuration setUp.
        parent_setup = functools.partial(
            super(MidonetPluginV2TestCase, self).setUp,
            plugin=MidonetPluginConf.plugin_name,
        )
        MidonetPluginConf.setUp(self, parent_setup)

    def setUp(self):
        self.setup_parent()


class TestMidonetNetworksV2(MidonetPluginV2TestCase,
                            test_plugin.TestNetworksV2):

    def setUp(self, plugin=None):
        super(TestMidonetNetworksV2, self).setUp()


class TestMidonetL3NatTestCase(MidonetPluginV2TestCase,
                               test_l3_plugin.L3NatDBIntTestCase):

    def setUp(self):
        super(TestMidonetL3NatTestCase, self).setUp()

    def test_floatingip_with_invalid_create_port(self):
        self._test_floatingip_with_invalid_create_port(PLUGIN_NAME)


class TestMidonetSecurityGroup(MidonetPluginV2TestCase,
                               sg.TestSecurityGroups):

    def setUp(self):
        super(TestMidonetSecurityGroup, self).setUp()


class TestMidonetSubnetsV2(MidonetPluginV2TestCase,
                           test_plugin.TestSubnetsV2):

    def setUp(self):
        super(TestMidonetSubnetsV2, self).setUp()


class TestMidonetPortsV2(MidonetPluginV2TestCase,
                         test_plugin.TestPortsV2):

    def setUp(self):
        super(TestMidonetPortsV2, self).setUp()

    def test_vif_port_binding(self):
        with self.port(name='myname') as port:
            self.assertEqual('midonet', port['port']['binding:vif_type'])
            self.assertTrue(port['port']['admin_state_up'])

    def test_profile_port_binding(self):
        profile_arg = {portbindings.PROFILE: {'interface_name':
                                              'test_if_name'},
                       portbindings.HOST_ID: 'test_host'}
        engine = db_api.get_engine()
        session = sessionmaker(bind=engine)()
        with self.port(arg_list=(portbindings.PROFILE, portbindings.HOST_ID,),
                       **profile_arg) as port:
            if_name = port['port'][portbindings.PROFILE]['interface_name']
            self.assertEqual('test_if_name', if_name)
            bindings = session.query(pb_db.PortBindingInfo)
            binding = bindings.filter(
                pb_db.PortBindingInfo.port_id == port['port']['id']).one()
            self.assertEqual('test_if_name', binding.interface_name)
            self._delete('ports', port['port']['id'])
        bindings = session.query(pb_db.PortBindingInfo)
        bindings = bindings.filter(
            pb_db.PortBindingInfo.port_id == port['port']['id']).all()
        self.assertEqual(0, len(bindings))

    def test_profile_port_binding_validation(self):
        profile_arg = {portbindings.PROFILE: {'interface_name':
                                              'test_if_name'},
                       portbindings.HOST_ID: 'test_host'}
        engine = db_api.get_engine()
        session = sessionmaker(bind=engine)()
        with self.port(arg_list=(portbindings.PROFILE, portbindings.HOST_ID,),
                       **profile_arg) as port:
            bindings = session.query(pb_db.PortBindingInfo)
            bindings.filter(
                pb_db.PortBindingInfo.port_id == port['port']['id']).one()
            self._delete('ports', port['port']['id'])

    def test_profile_port_binding_validation_no_profile(self):
        profile_arg = {portbindings.HOST_ID: 'test_host'}
        with self.port(arg_list=(portbindings.PROFILE, ),
                       **profile_arg) as port:
            self._delete('ports', port['port']['id'])

    def test_profile_port_binding_validation_ho_host(self):
        profile_arg = {portbindings.PROFILE: {'interface_name':
                                              'test_if_name'}}
        try:
            with self.port(arg_list=(portbindings.PROFILE,), **profile_arg):
                self.assertTrue(False)
        except exc.HTTPClientError:
            pass


class TestMidonetPortBinding(MidonetPluginV2TestCase,
                             test_bindings.PortBindingsTestCase):

    def setUp(self):
        super(TestMidonetPortBinding, self).setUp()

    VIF_TYPE = portbindings.VIF_TYPE_MIDONET
    HAS_PORT_FILTER = True


class TestMidonetExtGwMode(MidonetPluginV2TestCase,
                           test_gw_mode.ExtGwModeIntTestCase):

    def setUp(self):
        super(TestMidonetExtGwMode, self).setUp()


class TestExtraDHCPOpts(MidonetPluginV2TestCase,
                        test_dhcpopts.TestExtraDhcpOpt):
    pass


class TestMidonetExtraRouteTestCase(MidonetPluginV2TestCase,
                                    test_ext_route.ExtraRouteDBIntTestCase):
    pass


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
        self.mh_id1 = '37c5bf38-c631-11e4-aa61-d35262f5c455'
        self.mh_id2 = '42c7543c-c631-11e4-a386-af39a501e275'
        self.mido_host1 = {'id': self.mh_id1,
                           'flooding_proxy_weight': 30}
        self.mido_host2 = {'id': self.mh_id2,
                           'flooding_proxy_weight': 20}

        def mock_hosts(ip, port):
            return [self.mido_host1, self.mido_host2]
        top.get_all_midonet_hosts = mock_hosts

    def test_list_mido_agent(self):
        agents = self._register_agent_states()
        res = self._list('agents')
        agent_ids = [agent['id'] for agent in res['agents']]
        for agt in res['agents']:
            self.assertTrue(agt['id'] in agent_ids)
        self.assertTrue(self.mh_id1 in agent_ids)
        self.assertTrue(self.mh_id2 in agent_ids)
        self.assertEqual(len(agent_ids), len(agents) + 2)

    def test_show_mido_agent(self):
        self._register_agent_states()
        agent = self._show('agents', self.mh_id1)
        self.assertEqual(
            agent['agent'],
            top.midonet_host_to_neutron_agent(self.mido_host1))

    def test_show_mido_agent_negative(self):
        self._register_agent_states()
        self._show('agents', 'c0adf9be-c951-11e4-91ea-53cfd0a23bf6',
                   expected_code=exc.HTTPNotFound.code)


class TestMidonetDataVersion(testlib_api.SqlTestCase):

    def setUp(self):
        super(TestMidonetDataVersion, self).setUp()

    def get_session(self):
        engine = db_api.get_engine()
        Session = sessionmaker(bind=engine)
        return Session()

    def test_create_version(self):
        session = self.get_session()
        dv_db.create_data_version(session)
        version = dv_db.get_last_version(session)
        self.assertEqual(version.id, 1)
        self.assertEqual(version.sync_tasks_status, dv_db.STARTED)

    def _test_version_status(self, version_update_func, status):
        session = self.get_session()
        dv_db.create_data_version(session)
        version = dv_db.get_last_version(session)
        self.assertEqual(version.sync_tasks_status, dv_db.STARTED)
        version_update_func(session)
        version = dv_db.get_last_version(session)
        self.assertEqual(version.sync_tasks_status, status)

    def test_update_version_status_completed(self):
        self._test_version_status(dv_db.complete_last_version,
                                  dv_db.COMPLETED)

    def test_update_version_status_error(self):
        self._test_version_status(dv_db.error_last_version,
                                  dv_db.ERROR)

    def test_update_version_status_aborted(self):
        self._test_version_status(dv_db.abort_last_version,
                                  dv_db.ABORTED)
