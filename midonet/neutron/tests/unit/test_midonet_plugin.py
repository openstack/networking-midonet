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
from midonet.neutron.db import routedserviceinsertion_db  # noqa
from midonet.neutron.db import task_db  # noqa
from neutron.db import api as db_api
from neutron.extensions import portbindings
from neutron.tests.unit import _test_extension_portbindings as test_bindings
import neutron.tests.unit.test_db_plugin as test_plugin
import neutron.tests.unit.test_extension_ext_gw_mode as test_gw_mode
from neutron.tests.unit import test_extension_extradhcpopts as test_dhcpopts
from neutron.tests.unit import test_extension_extraroute as test_ext_route
import neutron.tests.unit.test_extension_security_group as sg
import neutron.tests.unit.test_l3_plugin as test_l3_plugin
from neutron.tests.unit import testlib_api
from neutron_lbaas.db.loadbalancer import loadbalancer_db as lb_db  # noqa
from sqlalchemy.orm import sessionmaker

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