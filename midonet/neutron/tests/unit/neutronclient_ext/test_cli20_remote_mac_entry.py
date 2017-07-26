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

from midonet.neutron.tests.unit.neutronclient_ext import test_cli20
from midonet.neutronclient.gateway_device_extension import _remote_mac_entry


class CLITestV20RemoteMacEntryJSON(test_cli20.CLIExtTestV20Base):

    def setUp(self):
        remote_mac_entry = ("remote_mac_entry", _remote_mac_entry)
        self._mock_load_extensions(remote_mac_entry)
        super(CLITestV20RemoteMacEntryJSON,
              self).setUp(plurals={'remote_mac_entries': 'remote_mac_entry'})
        self.register_non_admin_status_resource('remote_mac_entry')

    def test_remote_mac_entry_cmd_loaded(self):
        neutron_shell = shell.NeutronShell('2.0')
        remote_mac_entry_cmd = {'gateway-device-remote-mac-entry-list':
                                _remote_mac_entry.RemoteMacEntryList,
                                'gateway-device-remote-mac-entry-create':
                                _remote_mac_entry.RemoteMacEntryCreate,
                                'gateway-device-remote-mac-entry-delete':
                                _remote_mac_entry.RemoteMacEntryDelete,
                                'gateway-device-remote-mac-entry-show':
                                _remote_mac_entry.RemoteMacEntryShow}
        for cmd_name, cmd_class in remote_mac_entry_cmd.items():
            found = neutron_shell.command_manager.find_command([cmd_name])
            self.assertEqual(cmd_class, found[0])

    def _create_remote_mac_entry(self, args, position_names,
                                 position_values, parent_id=None):
        resource = 'remote_mac_entry'
        cmd = _remote_mac_entry.RemoteMacEntryCreate(
            test_cli20.MyApp(sys.stdout), None)
        self._test_create_resource(resource, cmd, None, 'myid',
                                   args, position_names, position_values,
                                   parent_id=parent_id)

    def test_create_remote_mac_entry(self):
        gw_device_id = 'my_gw_device'
        mac_addr = 'fa:16:3e:db:79:80'
        vtep_addr = '192.168.100.1'
        seg_id = '200'
        args = ['--mac-address', mac_addr, '--vtep-address', vtep_addr,
                '--segmentation-id', seg_id, gw_device_id]
        position_names = ['mac_address', 'vtep_address', 'segmentation_id']
        position_values = [mac_addr, vtep_addr, seg_id]
        self._create_remote_mac_entry(args, position_names,
                                      position_values, parent_id=gw_device_id)

    def test_create_remote_mac_entry_with_missing_gw_device_id(self):
        mac_addr = ''
        vtep_addr = ''
        seg_id = '200'
        args = ['--mac-address', mac_addr,
                '--vtep-address', vtep_addr, '--segmentation-id', seg_id]
        position_names = []
        position_values = []
        self.assertRaises(SystemExit, self._create_remote_mac_entry,
                          args, position_names, position_values)

    def test_create_remote_mac_entry_with_missing_seg_id(self):
        gw_device_id = 'my_gw_device'
        mac_addr = ''
        vtep_addr = ''
        args = ['--mac-address', mac_addr, '--vtep-address', vtep_addr,
                gw_device_id]
        position_names = []
        position_values = []
        self.assertRaises(SystemExit, self._create_remote_mac_entry,
                          args, position_names, position_values,
                          parent_id=gw_device_id)

    def test_delete_remote_mac_entry(self):
        resource = 'remote_mac_entry'
        cmd = _remote_mac_entry.RemoteMacEntryDelete(
            test_cli20.MyApp(sys.stdout), None)
        gw_device_id = 'my_gw_device'
        my_id = 'myid'
        args = [my_id, gw_device_id]
        self._test_delete_ext_resource(resource, cmd, my_id, args,
                                       parent_id=gw_device_id)

    def test_list_remote_mac_entries(self):
        resources = 'remote_mac_entries'
        cmd = _remote_mac_entry.RemoteMacEntryList(
            test_cli20.MyApp(sys.stdout), None)
        gw_device_id = 'my_gw_device'
        args = [gw_device_id]
        self._test_list_resources(resources, cmd, base_args=args,
                                  parent_id=gw_device_id)

    def test_show_remote_mac_entry(self):
        resource = 'remote_mac_entry'
        cmd = _remote_mac_entry.RemoteMacEntryShow(
            test_cli20.MyApp(sys.stdout), None)
        gw_device_id = 'my_gw_device'
        my_id = 'myid'
        args = [my_id, gw_device_id]
        self._test_show_ext_resource(resource, cmd, my_id, args,
                                     parent_id=gw_device_id)
