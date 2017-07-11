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
#

from oslo_serialization import jsonutils

from neutronclient.common import extension
from neutronclient.neutron import v2_0 as gw_deviceV20

from midonet.neutron._i18n import _


def add_name_and_tunnel_ips_to_arguments(parser):
    parser.add_argument(
        '--name', dest='name',
        help=_('User defined device name.'))
    parser.add_argument(
        '--tunnel-ip', metavar='TUNNEL_IP',
        action='append', dest='tunnel_ips',
        help=_('IP address on which gateway device originates or '
               'terminates tunnel.'))


def _format_remote_mac_entries(gw_device):
    try:
        return '\n'.join([jsonutils.dumps(rm_entry) for rm_entry
                          in gw_device['remote_mac_entries']])
    except (TypeError, KeyError):
        return ''


class GatewayDevice(extension.NeutronClientExtension):
    resource = 'gateway_device'
    resource_plural = 'gateway_devices'
    path = 'gw/gateway_devices'
    object_path = '/%s' % path
    resource_path = '/%s/%%s' % path
    versions = ['2.0']


class GatewayDeviceCreate(extension.ClientExtensionCreate, GatewayDevice):
    """Create Gateway Device information."""

    shell_command = 'gateway-device-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--management-ip',
            dest='management_ip',
            help=_('Management IP to the device. Defaults to None.'))
        parser.add_argument(
            '--management-port',
            dest='management_port',
            help=_('Management port to the device. Defaults to None.'))
        parser.add_argument(
            '--management-protocol',
            dest='management_protocol',
            help=_('Management protocol to manage the device: ovsdb or none. '
                   'If management ip and port are specified, '
                   'defaults to ovsdb. Otherwise to none.'))
        parser.add_argument(
            '--type',
            metavar='<hw_vtep | router_vtep | network_vlan>',
            choices=['hw_vtep', 'router_vtep', 'network_vlan'],
            help=_('Type of the device: hw_vtep, router_vtep or network_vlan. '
                   'Defaults to hw_vtep'))
        parser.add_argument(
            '--resource-id',
            dest='resource_id',
            help=_('Resource UUID or None (for type router_vtep will '
                   'be router UUID and for type network_vlan will be network '
                   'UUID)'))
        add_name_and_tunnel_ips_to_arguments(parser)

        return parser

    def args2body(self, args):
        body = {}
        attributes = ['name', 'type', 'management_ip',
                      'management_port', 'management_protocol',
                      'resource_id', 'tenant_id', 'tunnel_ips']
        gw_deviceV20.update_dict(args, body, attributes)

        return {'gateway_device': body}


class GatewayDeviceList(extension.ClientExtensionList, GatewayDevice):
    """List Gateway Devices."""

    shell_command = 'gateway-device-list'
    list_columns = ['id', 'name', 'type', 'resource_id', 'tunnel_ips']
    pagination_support = True
    sorting_support = True

    _formatters = {'remote_mac_entries': _format_remote_mac_entries, }


class GatewayDeviceShow(extension.ClientExtensionShow, GatewayDevice):
    """Show information of a given gateway-device."""

    shell_command = 'gateway-device-show'


class GatewayDeviceDelete(extension.ClientExtensionDelete, GatewayDevice):
    """Delete a given gateway-device."""

    shell_command = 'gateway-device-delete'


class GatewayDeviceUpdate(extension.ClientExtensionUpdate, GatewayDevice):
    """Update a given gateway-device."""

    shell_command = 'gateway-device-update'

    def add_known_arguments(self, parser):
        add_name_and_tunnel_ips_to_arguments(parser)

    def args2body(self, args):
        body = {}
        attributes = ['name', 'tunnel_ips']
        gw_deviceV20.update_dict(args, body, attributes)

        return {'gateway_device': body}
