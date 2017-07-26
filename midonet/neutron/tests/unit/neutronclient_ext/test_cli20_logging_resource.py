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
from midonet.neutronclient.logging_resource_extension import _logging_resource

RESOURCE = 'logging_resource'
RESOURCES = 'logging_resources'
FAKE_TENANT_NAME = 'my_tenant_name'
FAKE_LOGGING_RESOURCE_ID = 'my_logging_resource_id'
FAKE_FIREWALL_LOG_ID1 = 'my_firewall_log_id1'
FAKE_FIREWALL_LOG_ID2 = 'my_firewall_log_id2'
FAKE_FIREWALL_ID1 = 'my_firewall_id1'
FAKE_FIREWALL_ID2 = 'my_firewall_id2'


class CLITestV20LoggingResourceJSON(test_cli20.CLIExtTestV20Base):

    def setUp(self):
        log_res = ("logging_resource", _logging_resource)
        self._mock_load_extensions(log_res)
        super(CLITestV20LoggingResourceJSON,
              self).setUp(plurals={'logging_resources': 'logging_resource'})
        self.register_non_admin_status_resource('logging_resource')

    def test_logging_resource_cmd_loaded(self):
        neutron_shell = shell.NeutronShell('2.0')
        log_res_cmd = {'logging-list':
                       _logging_resource.LoggingResourceList,
                       'logging-create':
                       _logging_resource.LoggingResourceCreate,
                       'logging-update':
                       _logging_resource.LoggingResourceUpdate,
                       'logging-delete':
                       _logging_resource.LoggingResourceDelete,
                       'logging-show':
                       _logging_resource.LoggingResourceShow
                       }
        for cmd_name, cmd_class in log_res_cmd.items():
            found = neutron_shell.command_manager.find_command([cmd_name])
            self.assertEqual(cmd_class, found[0])

    def _create_logging_resource(self, name, args,
                                 position_names, position_values):
        cmd = _logging_resource.LoggingResourceCreate(
            test_cli20.MyApp(sys.stdout), None)
        self._test_create_resource(RESOURCE, cmd, name,
                                   FAKE_LOGGING_RESOURCE_ID,
                                   args, position_names, position_values)

    def _update_logging_resource(self, args, values):
        cmd = _logging_resource.LoggingResourceUpdate(
            test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(RESOURCE, cmd, FAKE_LOGGING_RESOURCE_ID,
                                   args, values)

    def test_create_logging_resource(self):
        args = [telr.FAKE_LOG_RES_NAME,
                '--tenant_id', FAKE_TENANT_NAME,
                '--enabled', str(telr.ENABLED_TRUE),
                '--description', telr.FAKE_LOG_RES_DESC]
        position_names = ['name', 'tenant_id', 'enabled', 'description']
        position_values = [telr.FAKE_LOG_RES_NAME, FAKE_TENANT_NAME,
                           str(telr.ENABLED_TRUE), telr.FAKE_LOG_RES_DESC]
        self._create_logging_resource(telr.FAKE_LOG_RES_NAME, args,
                                      position_names, position_values)

    def test_update_logging_resource_with_name(self):
        args = [FAKE_LOGGING_RESOURCE_ID, '--name', telr.NEW_LOG_RES_NAME]
        values = {'name': telr.NEW_LOG_RES_NAME}
        self._update_logging_resource(args, values)

    def test_update_logging_resource_with_enabled(self):
        args = [FAKE_LOGGING_RESOURCE_ID, '--enabled', str(telr.ENABLED_FALSE)]
        values = {'enabled': str(telr.ENABLED_FALSE)}
        self._update_logging_resource(args, values)

    def test_delete_logging_resource(self):
        cmd = _logging_resource.LoggingResourceDelete(
            test_cli20.MyApp(sys.stdout), None)
        args = [FAKE_LOGGING_RESOURCE_ID]
        self._test_delete_resource(RESOURCE, cmd,
                                   FAKE_LOGGING_RESOURCE_ID, args)

    def test_list_logging_resources(self):
        cmd = _logging_resource.LoggingResourceList(
            test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(RESOURCES, cmd)

    def test_list_logging_resources_with_pagination(self):
        cmd = _logging_resource.LoggingResourceList(
            test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources_with_pagination(RESOURCES, cmd)

    def test_list_logging_resource_with_firewall_logs(self):
        cmd = _logging_resource.LoggingResourceList(
            test_cli20.MyApp(sys.stdout), None)
        fw_log = [{"firewall_id": FAKE_FIREWALL_ID1,
                   "description": telr.FAKE_FW_LOG_DESC,
                   "id": FAKE_FIREWALL_LOG_ID1,
                   "fw_event": log_res_ext.FW_EVENT_ALL},
                  {"firewall_id": FAKE_FIREWALL_ID2,
                   "description": telr.FAKE_FW_LOG_DESC,
                   "id": FAKE_FIREWALL_LOG_ID2,
                   "fw_event": log_res_ext.FW_EVENT_DROP}]
        response = {'logging_resources': [
            {"id": FAKE_LOGGING_RESOURCE_ID,
             "name": telr.FAKE_LOG_RES_NAME,
             "enabled": str(telr.ENABLED_TRUE),
             "description": telr.FAKE_LOG_RES_DESC,
             "firewall_logs": fw_log}]}
        args = ['-c', 'id', '-c', 'firewall_logs']
        self._test_list_columns(cmd, RESOURCES, response, args)

    def test_show_logging_resource(self):
        cmd = _logging_resource.LoggingResourceShow(
            test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(RESOURCE, cmd, self.test_id, args,
                                 ['id', 'name'])
