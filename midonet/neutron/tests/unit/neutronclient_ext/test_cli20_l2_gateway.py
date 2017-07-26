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
from midonet.neutronclient.l2gateway_extension import _l2_gateway


class CLITestV20L2gatewayJSON(test_cli20.CLIExtTestV20Base):

    def setUp(self):
        l2_gateway = ("l2_gateway", _l2_gateway)
        self._mock_load_extensions(l2_gateway)
        super(CLITestV20L2gatewayJSON,
              self).setUp(plurals={'l2_gateways': 'l2_gateway'})
        self.register_non_admin_status_resource('l2_gateway')

    def test_midonet_l2gateway_cmd_loaded(self):
        neutron_shell = shell.NeutronShell('2.0')
        mido_l2gw_cmd = {'midonet-l2-gateway-create':
                         _l2_gateway.L2GatewayCreate,
                         }
        for cmd_name, cmd_class in mido_l2gw_cmd.items():
            found = neutron_shell.command_manager.find_command([cmd_name])
            self.assertEqual(cmd_class, found[0])

    def _create_l2gateway(self, name, args,
                          position_names, position_values):
        resource = 'l2_gateway'
        cmd = _l2_gateway.L2GatewayCreate(test_cli20.MyApp(sys.stdout), None)
        self._test_create_resource(resource, cmd, name, 'myid',
                                   args, position_names, position_values)

    def test_create_l2gateway(self):
        name = 'l2gateway1'
        args = [name, '--device',
                'device_id=my_device_id,segmentation_id=my_segmentation_id']
        position_names = ['name', 'devices']
        position_values = [name, [{"device_id": "my_device_id",
                                  "segmentation_id": "my_segmentation_id"}]]
        self._create_l2gateway(name, args,
                               position_names, position_values)

    def test_create_l2gateway_with_multiple_devices(self):
        name = 'l2gateway1'
        args = [name,
                '--device',
                'device_id=my_device_id1,segmentation_id=my_segmentation_id1',
                '--device',
                'device_id=my_device_id2,segmentation_id=my_segmentation_id2']
        position_names = ['name', 'devices']
        position_values = [name,
                           [{"device_id": "my_device_id1",
                             "segmentation_id": "my_segmentation_id1"},
                            {"device_id": "my_device_id2",
                             "segmentation_id": "my_segmentation_id2"}]]
        self._create_l2gateway(name, args,
                               position_names, position_values)

    def test_create_l2gateway_without_segmentation_id(self):
        name = 'l2gateway1'
        args = [name, '--device', 'device_id=my_device_id']
        position_names = ['name', 'devices']
        position_values = [name, [{"device_id": "my_device_id"}]]
        self._create_l2gateway(name, args,
                               position_names, position_values)
