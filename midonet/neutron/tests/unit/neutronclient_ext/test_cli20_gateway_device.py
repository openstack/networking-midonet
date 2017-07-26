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
from midonet.neutronclient.gateway_device_extension import _gateway_device


class CLITestV20GatewayDeviceJSON(test_cli20.CLIExtTestV20Base):

    def setUp(self):
        gw_device = ("gateway_device", _gateway_device)
        self._mock_load_extensions(gw_device)
        super(CLITestV20GatewayDeviceJSON,
              self).setUp(plurals={'gateway_devices': 'gateway_device'})
        self.register_non_admin_status_resource('gateway_device')

    def test_gateway_device_cmd_loaded(self):
        neutron_shell = shell.NeutronShell('2.0')
        gw_device_cmd = {'gateway-device-list':
                         _gateway_device.GatewayDeviceList,
                         'gateway-device-create':
                         _gateway_device.GatewayDeviceCreate,
                         'gateway-device-update':
                         _gateway_device.GatewayDeviceUpdate,
                         'gateway-device-delete':
                         _gateway_device.GatewayDeviceDelete,
                         'gateway-device-show':
                         _gateway_device.GatewayDeviceShow
                         }
        for cmd_name, cmd_class in gw_device_cmd.items():
            found = neutron_shell.command_manager.find_command([cmd_name])
            self.assertEqual(cmd_class, found[0])

    def _create_gateway_device(self, name, args,
                               position_names, position_values):
        resource = 'gateway_device'
        cmd = _gateway_device.GatewayDeviceCreate(
            test_cli20.MyApp(sys.stdout), None)
        self._test_create_resource(resource, cmd, name, 'myid',
                                   args, position_names, position_values)

    def _update_gateway_device(self, args, values):
        resource = 'gateway_device'
        cmd = _gateway_device.GatewayDeviceUpdate(
            test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(resource, cmd, 'myid', args, values)

    def test_create_gateway_device_for_hw_vtep_mandatory_params(self):
        name = 'hw-vtep-mandatory'
        gw_type = 'hw_vtep'
        mng_ip = '10.0.0.100'
        mng_port = '22'
        mng_protocol = 'ovsdb'
        args = ['--type', gw_type,
                '--management-ip', mng_ip,
                '--management-port', mng_port,
                '--management-protocol', mng_protocol]
        position_names = ['type', 'management_ip',
                          'management_port', 'management_protocol']
        position_values = [gw_type, mng_ip, mng_port, mng_protocol]
        self._create_gateway_device(name, args,
                                    position_names, position_values)

    def test_create_gateway_device_for_hw_vtep_with_optional_params(self):
        name = 'hw-vtep-optional'
        tenant_id = 'my_tenant'
        gw_type = 'hw_vtep'
        mng_ip = '10.0.0.100'
        mng_port = '22'
        mng_protocol = 'ovsdb'
        tunnel_ip = '200.200.200.4'
        args = ['--tenant-id', tenant_id,
                '--type', gw_type,
                '--management-ip', mng_ip,
                '--management-port', mng_port,
                '--management-protocol', mng_protocol,
                '--name', name,
                '--tunnel-ip', tunnel_ip]
        position_names = ['type', 'management_ip', 'management_port',
                          'management_protocol', 'tenant_id',
                          'name', 'tunnel_ips']
        position_values = [gw_type, mng_ip, mng_port, mng_protocol,
                           tenant_id, name, [tunnel_ip]]
        self._create_gateway_device(name, args,
                                    position_names, position_values)

    def test_create_gateway_device_for_router_vtep_with_mandatory_params(self):
        name = 'router-vtep-mandatory'
        gw_type = 'router_vtep'
        resource_id = 'my_router_id'
        args = ['--type', gw_type, '--resource-id', resource_id]
        position_names = ['type', 'resource_id']
        position_values = [gw_type, resource_id]
        self._create_gateway_device(name, args,
                                    position_names, position_values)

    def test_create_gateway_device_for_router_vtep_with_optional_params(self):
        name = 'router-vtep-optional'
        tenant_id = 'my_tenant'
        gw_type = 'router_vtep'
        resource_id = 'my_router_id'
        tunnel_ip = '200.200.200.4'
        args = ['--tenant-id', tenant_id,
                '--type', gw_type,
                '--resource-id', resource_id,
                '--name', name,
                '--tunnel-ip', tunnel_ip]
        position_names = ['type', 'resource_id',
                          'tenant_id', 'name', 'tunnel_ips']
        position_values = [gw_type, resource_id,
                           tenant_id, name, [tunnel_ip]]
        self._create_gateway_device(name, args,
                                    position_names, position_values)

    def test_create_gateway_device_for_network_vlan_with_mandatory_params(
            self):
        name = 'network_vlan-mandatory'
        gw_type = 'network_vlan'
        resource_id = 'my_network_id'
        args = ['--type', gw_type, '--resource-id', resource_id]
        position_names = ['type', 'resource_id']
        position_values = [gw_type, resource_id]
        self._create_gateway_device(name, args,
                                    position_names, position_values)

    def test_create_gateway_device_for_network_vlan_with_optional_params(self):
        name = 'network_vlan-optional'
        tenant_id = 'my_tenant'
        gw_type = 'network_vlan'
        resource_id = 'my_network_id'
        args = ['--tenant-id', tenant_id,
                '--type', gw_type,
                '--resource-id', resource_id,
                '--name', name]
        position_names = ['type', 'resource_id',
                          'tenant_id', 'name']
        position_values = [gw_type, resource_id,
                           tenant_id, name]
        self._create_gateway_device(name, args,
                                    position_names, position_values)

    def test_update_gateway_device_with_name(self):
        args = ['myid', '--name', 'name_updated']
        values = {'name': 'name_updated'}
        self._update_gateway_device(args, values)

    def test_update_gateway_device_with_tunnel_ip(self):
        args = ['myid', '--tunnel-ip', '200.200.200.4']
        values = {'tunnel_ips': ['200.200.200.4']}
        self._update_gateway_device(args, values)

    def test_update_gateway_device_with_tunnel_ips(self):
        args = ['myid', '--tunnel-ip', '200.200.200.4',
                '--tunnel-ip', '200.200.200.10']
        values = {'tunnel_ips': ['200.200.200.4',
                                 '200.200.200.10']}
        self._update_gateway_device(args, values)

    def test_delete_gateway_device(self):
        resource = 'gateway_device'
        cmd = _gateway_device.GatewayDeviceDelete(
            test_cli20.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(resource, cmd, my_id, args)

    def test_list_gateway_devices(self):
        resources = 'gateway_devices'
        cmd = _gateway_device.GatewayDeviceList(
            test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd)

    def test_list_gateway_devices_with_pagination(self):
        resources = 'gateway_devices'
        cmd = _gateway_device.GatewayDeviceList(
            test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources_with_pagination(resources, cmd)

    def test_list_gateway_device_with_remote_mac_entries(self):
        resources = 'gateway_devices'
        cmd = _gateway_device.GatewayDeviceList(
            test_cli20.MyApp(sys.stdout), None)
        rme = [
            {"segmentation_id": 100,
             "vtep_address": "192.168.100.1",
             "id": "remote_mac_entry_id1",
             "mac_address": "fa:16:3e:db:79:80"},
            {"segmentation_id": 100,
             "vtep_address": "192.168.100.50",
             "id": "remote_mac_entry_id1",
             "mac_address": "fa:16:3e:df:79:80"},
        ]
        response = {'gateway_devices': [{"id": 'myid',
                                         "name": 'gw_device',
                                         "type": "router_vtep",
                                         "resource_id": "router_id",
                                         "tunnel_ips": [],
                                         "remote_mac_entries": rme}]}
        args = ['-c', 'id', '-c', 'remote_mac_entries']
        self._test_list_columns(cmd, resources, response, args)

    def test_show_gateway_device(self):
        resource = 'gateway_device'
        cmd = _gateway_device.GatewayDeviceShow(
            test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args,
                                 ['id', 'name'])
