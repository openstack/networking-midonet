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

from neutronclient.common import extension
from neutronclient.neutron import v2_0 as gw_deviceV20

from midonet.neutron._i18n import _


def _get_gateway_device_id(client, gw_device_id_or_name):
    return gw_deviceV20.find_resourceid_by_name_or_id(client, 'gateway_device',
                                                      gw_device_id_or_name)


class RemoteMacEntry(extension.NeutronClientExtension):
    parent_resource = 'gateway_devices'
    resource = 'remote_mac_entry'
    resource_plural = 'remote_mac_entries'
    object_path = '/gw/%s/%%s/%s' % (parent_resource, resource_plural)
    resource_path = '/gw/%s/%%s/%s/%%%%s' % (parent_resource, resource_plural)
    versions = ['2.0']

    def add_known_arguments(self, parser):
        super(RemoteMacEntry, self).add_known_arguments(parser)
        parser.add_argument(
            'gateway_device', metavar='GATEWAY_DEVICE',
            help=_('ID of the gateway device.'))

    def set_extra_attrs(self, parsed_args):
        self.parent_id = _get_gateway_device_id(self.get_client(),
                                                parsed_args.gateway_device)


class RemoteMacEntryCreate(extension.ClientExtensionCreate, RemoteMacEntry):
    """Create Gateway Device Remote Mac Entry information."""

    shell_command = 'gateway-device-remote-mac-entry-create'

    def add_known_arguments(self, parser):
        super(RemoteMacEntryCreate, self).add_known_arguments(parser)
        parser.add_argument(
            '--mac-address', dest='mac_address',
            required=True,
            help=_('Remote MAC address'))
        parser.add_argument(
            '--vtep-address', dest='vtep_address',
            required=True,
            help=_('Remote VTEP Tunnel IP'))
        parser.add_argument(
            '--segmentation-id', dest='segmentation_id',
            required=True,
            help=_('VNI to be used'))

    def args2body(self, args):
        body = {}
        attributes = ['mac_address', 'vtep_address', 'segmentation_id']
        gw_deviceV20.update_dict(args, body, attributes)
        return {'remote_mac_entry': body}


class RemoteMacEntryList(extension.ClientExtensionList, RemoteMacEntry):
    """List Gateway Device Remote Mac Entries."""

    shell_command = 'gateway-device-remote-mac-entry-list'
    list_columns = ['id', 'mac_address', 'vtep_address', 'segmentation_id']
    pagination_support = True
    sorting_support = True


class RemoteMacEntryShow(extension.ClientExtensionShow, RemoteMacEntry):
    """Show information of a given gateway-device-remote-mac-entry."""

    shell_command = 'gateway-device-remote-mac-entry-show'
    allow_names = False


class RemoteMacEntryDelete(extension.ClientExtensionDelete, RemoteMacEntry):
    """Delete a given gateway-device-remote-mac-entry."""

    shell_command = 'gateway-device-remote-mac-entry-delete'
    allow_names = False
