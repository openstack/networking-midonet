# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2012 Midokura Japan K.K.
# Copyright (C) 2013 Midokura PTE LTD
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
#
# @author: Rossella Sblendido, Midokura Europe SARL
# @author: Ryu Ishimoto, Midokura Japan KK
# @author: Tomoe Sugihara, Midokura Japan KK

import mock

from neutron.extensions import portbindings
from neutron.tests.unit import _test_extension_portbindings as test_bindings
import neutron.tests.unit.test_db_plugin as test_plugin
import neutron.tests.unit.test_extension_ext_gw_mode as test_gw_mode
import neutron.tests.unit.test_extension_security_group as sg
import neutron.tests.unit.test_l3_plugin as test_l3_plugin


MIDOKURA_PKG_PATH = "midonet.neutron.plugin"
MIDONET_PLUGIN_NAME = ('%s.MidonetPluginV2' % MIDOKURA_PKG_PATH)


class MidonetPluginV2TestCase(test_plugin.NeutronDbPluginV2TestCase):

    def setUp(self,
              plugin=MIDONET_PLUGIN_NAME,
              ext_mgr=None,
              service_plugins=None):

        self.midoclient_mock = mock.MagicMock()
        self.midoclient_mock.midonetclient.neutron.client.return_value = True
        modules = {
            'midonetclient': self.midoclient_mock,
            'midonetclient.neutron': self.midoclient_mock.neutron,
            'midonetclient.neutron.client': self.midoclient_mock.client,
        }

        self.module_patcher = mock.patch.dict('sys.modules', modules)
        self.module_patcher.start()

        # import midonetclient here because it needs proper mock objects to be
        # assigned to this module first.  'midoclient_mock' object is the
        # mock object used for this module.
        from midonetclient.neutron.client import MidonetClient
        client_class = MidonetClient
        self.mock_class = client_class()

        super(MidonetPluginV2TestCase, self).setUp(plugin=plugin)

    def tearDown(self):
        super(MidonetPluginV2TestCase, self).tearDown()
        self.module_patcher.stop()


class TestMidonetNetworksV2(MidonetPluginV2TestCase,
                            test_plugin.TestNetworksV2):

    pass


class TestMidonetL3NatTestCase(MidonetPluginV2TestCase,
                               test_l3_plugin.L3NatDBIntTestCase):

    def test_floatingip_with_invalid_create_port(self):
        self._test_floatingip_with_invalid_create_port(MIDONET_PLUGIN_NAME)


class TestMidonetSecurityGroup(MidonetPluginV2TestCase,
                               sg.TestSecurityGroups):

    pass


class TestMidonetSubnetsV2(MidonetPluginV2TestCase,
                           test_plugin.TestSubnetsV2):

    pass


class TestMidonetPortsV2(MidonetPluginV2TestCase,
                         test_plugin.TestPortsV2):

    def test_vif_port_binding(self):
        with self.port(name='myname') as port:
            self.assertEqual('midonet', port['port']['binding:vif_type'])
            self.assertTrue(port['port']['admin_state_up'])


class TestMidonetPluginPortBinding(MidonetPluginV2TestCase,
                                   test_bindings.PortBindingsTestCase):

    VIF_TYPE = portbindings.VIF_TYPE_MIDONET
    HAS_PORT_FILTER = True


class TestExtGwMode(MidonetPluginV2TestCase,
                    test_gw_mode.ExtGwModeIntTestCase):

    pass
