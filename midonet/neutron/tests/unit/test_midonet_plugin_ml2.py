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

from midonet.neutron.common import config  # noqa
from midonet.neutron.db import agent_membership_db  # noqa
from midonet.neutron.db import port_binding_db  # noqa
from midonet.neutron.db import provider_network_db  # noqa
from midonet.neutron.db import task_db  # noqa
from midonet.neutron.tests.unit import test_midonet_plugin as test_mn_plugin
from neutron.tests.unit.db import test_db_base_plugin_v2 as test_plugin
from neutron.tests.unit.extensions import test_securitygroup as test_sg

from oslo_config import cfg

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
                              ['midonet'],
                              group='ml2')
        cfg.CONF.set_override('mechanism_drivers',
                              ['midonet'],
                              group='ml2')
        cfg.CONF.set_override('tenant_network_types',
                              ['midonet'],
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
    pass


class TestMidonetPortsML2(MidonetPluginML2TestCase,
                          test_plugin.TestPortsV2):
    pass
