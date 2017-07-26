# Copyright (C) 2016 Midokura SARL
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import sys

from neutronclient import shell

from midonet.neutron.extensions import logging_resource as log_res_ext
from midonet.neutron.tests.unit.neutronclient_ext import test_cli20
from midonet.neutron.tests.unit import test_extension_logging_resource as telr
from midonet.neutronclient.logging_resource_extension import _firewall_log

RESOURCE = 'firewall_log'
RESOURCES = 'firewall_logs'
FAKE_LOGGING_RESOURCE_ID = 'my_logging_resource_id'
FAKE_FIREWALL_ID = 'my_firewall_id'
FAKE_FIREWALL_LOG_ID = 'my_firewall_log_id'


class CLITestV20FirewallLogJSON(test_cli20.CLIExtTestV20Base):

    def setUp(self):
        firewall_log = ("firewall_log", _firewall_log)
        self._mock_load_extensions(firewall_log)
        super(CLITestV20FirewallLogJSON,
              self).setUp(plurals={'firewall_logs': 'firewall_log'})
        self.register_non_admin_status_resource('firewall_log')

    def test_firewall_log_cmd_loaded(self):
        neutron_shell = shell.NeutronShell('2.0')
        firewall_log_cmd = {'logging-firewall-list':
                            _firewall_log.FirewallLogList,
                            'logging-firewall-create':
                            _firewall_log.FirewallLogCreate,
                            'logging-firewall-update':
                            _firewall_log.FirewallLogUpdate,
                            'logging-firewall-delete':
                            _firewall_log.FirewallLogDelete,
                            'logging-firewall-show':
                            _firewall_log.FirewallLogShow}
        for cmd_name, cmd_class in firewall_log_cmd.items():
            found = neutron_shell.command_manager.find_command([cmd_name])
            self.assertEqual(cmd_class, found[0])

    def _create_firewall_log(self, args, position_names,
                             position_values, parent_id=None):
        cmd = _firewall_log.FirewallLogCreate(
            test_cli20.MyApp(sys.stdout), None)
        self._test_create_resource(RESOURCE, cmd, None, FAKE_FIREWALL_LOG_ID,
                                   args, position_names, position_values,
                                   parent_id=parent_id)

    def _update_firewall_log(self, args, values, parent_id=None):
        cmd = _firewall_log.FirewallLogUpdate(
            test_cli20.MyApp(sys.stdout), None)
        self._test_update_ext_resource(RESOURCE, cmd, FAKE_FIREWALL_LOG_ID,
                                       args, values, parent_id=parent_id)

    def test_create_firewall_log(self):
        args = ['--description', telr.FAKE_FW_LOG_DESC,
                '--fw-event', log_res_ext.FW_EVENT_DROP,
                '--firewall-id', FAKE_FIREWALL_ID,
                FAKE_LOGGING_RESOURCE_ID]
        position_names = ['description', 'fw_event', 'firewall_id']
        position_values = [telr.FAKE_FW_LOG_DESC, log_res_ext.FW_EVENT_DROP,
                           FAKE_FIREWALL_ID]
        self._create_firewall_log(args, position_names,
                                  position_values,
                                  parent_id=FAKE_LOGGING_RESOURCE_ID)

    def test_create_firewall_log_with_missing_logging_resource_id(self):
        args = ['--description', telr.FAKE_FW_LOG_DESC,
                '--fw-event', log_res_ext.FW_EVENT_DROP,
                '--firewall-id', FAKE_FIREWALL_ID]
        position_names = []
        position_values = []
        self.assertRaises(SystemExit, self._create_firewall_log,
                          args, position_names, position_values)

    def test_create_firewall_log_with_missing_firewall_id(self):
        args = ['--description', telr.FAKE_FW_LOG_DESC,
                '--fw-event', log_res_ext.FW_EVENT_DROP,
                FAKE_LOGGING_RESOURCE_ID]
        position_names = []
        position_values = []
        self.assertRaises(SystemExit, self._create_firewall_log,
                          args, position_names, position_values,
                          parent_id=FAKE_LOGGING_RESOURCE_ID)

    def test_update_firewall_log_with_description(self):
        args = [FAKE_FIREWALL_LOG_ID, FAKE_LOGGING_RESOURCE_ID,
                '--description', telr.NEW_FW_LOG_DESC]
        values = {'description': telr.NEW_FW_LOG_DESC}
        self._update_firewall_log(args, values,
                                  parent_id=FAKE_LOGGING_RESOURCE_ID)

    def test_update_firewall_log_with_fw_event(self):
        args = [FAKE_FIREWALL_LOG_ID, FAKE_LOGGING_RESOURCE_ID,
                '--fw-event', log_res_ext.FW_EVENT_ACCEPT]
        values = {'fw_event': log_res_ext.FW_EVENT_ACCEPT}
        self._update_firewall_log(args, values,
                                  parent_id=FAKE_LOGGING_RESOURCE_ID)

    def test_delete_firewall_log(self):
        cmd = _firewall_log.FirewallLogDelete(
            test_cli20.MyApp(sys.stdout), None)
        args = [FAKE_FIREWALL_LOG_ID, FAKE_LOGGING_RESOURCE_ID]
        self._test_delete_ext_resource(RESOURCE, cmd,
                                       FAKE_FIREWALL_LOG_ID, args,
                                       parent_id=FAKE_LOGGING_RESOURCE_ID)

    def test_list_firewall_logs(self):
        cmd = _firewall_log.FirewallLogList(
            test_cli20.MyApp(sys.stdout), None)
        args = [FAKE_LOGGING_RESOURCE_ID]
        self._test_list_resources(RESOURCES, cmd, base_args=args,
                                  parent_id=FAKE_LOGGING_RESOURCE_ID)

    def test_show_firewall_log(self):
        cmd = _firewall_log.FirewallLogShow(
            test_cli20.MyApp(sys.stdout), None)
        args = [FAKE_FIREWALL_LOG_ID, FAKE_LOGGING_RESOURCE_ID]
        self._test_show_ext_resource(RESOURCE, cmd,
                                     FAKE_FIREWALL_LOG_ID, args,
                                     parent_id=FAKE_LOGGING_RESOURCE_ID)
