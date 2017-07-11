# Copyright (C) 2015 Midokura SARL
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

import abc

from neutron_lib.api import extensions as api_extensions
from neutron_lib.api import validators
from neutron_lib.db import constants as db_const
from neutron_lib import exceptions as nexception
from neutron_lib.plugins import directory
from oslo_log import log as logging
import six

from neutron.api import extensions
from neutron.api.v2 import base
from neutron.api.v2 import resource_helper

from midonet.neutron._i18n import _
from midonet.neutron.common import constants


class GatewayDeviceNotFound(nexception.NotFound):
    message = _("Gateway device %(id)s does not exist")


class RemoteMacEntryNotFound(nexception.NotFound):
    message = _("Remote MAC entry %(id)s does not exist")


class RemoteMacEntryWrongGatewayDevice(nexception.InvalidInput):
    message = _("Remote MAC entry %(id)s does not belong to gateway "
                "device %(gateway_device_id)s")


class ResourceNotFound(nexception.NotFound):
    message = _("specified resource %(resource_id)s does not exist")


class HwVtepTypeInvalid(nexception.InvalidInput):
    message = _("Gateway device %(type)s must be specified with "
                "management_port and management_ip")


class RouterVtepTypeInvalid(nexception.InvalidInput):
    message = _("Gateway device %(type)s must be specified with "
                "resource_id")


class NetworkVlanTypeInvalid(nexception.InvalidInput):
    message = _("Gateway device %(type)s must be specified with "
                "resource_id")


class DuplicateRemoteMacEntry(nexception.InUse):
    message = _("Request contains duplicate remote mac address entry: "
                "mac_address %(mac_address)s.")


class GatewayDeviceParamDuplicate(nexception.InUse):
    message = _("%(param_name)s %(param_value)s %(reason)s")

    def __init__(self, **kwargs):
        if 'reason' not in kwargs:
            kwargs['reason'] = "is already used"
        super(GatewayDeviceParamDuplicate, self).__init__(**kwargs)


class GatewayDeviceInUse(nexception.InUse):
    message = _("Gateway device %(id)s %(reason)s")

    def __init__(self, **kwargs):
        if 'reason' not in kwargs:
            kwargs['reason'] = "is in use by l2 gateway"
        super(GatewayDeviceInUse, self).__init__(**kwargs)


class DeviceInUseByGatewayDevice(nexception.InUse):
    message = _("device %(resource_id)s (%(resource_type)s) %(reason)s")

    def __init__(self, **kwargs):
        if 'reason' not in kwargs:
            kwargs['reason'] = "is in use by gateway device"
        super(DeviceInUseByGatewayDevice, self).__init__(**kwargs)


class TunnelIPsExhausted(nexception.BadRequest):
    message = _("Unable to complete operation for Gateway Device. "
                "The number of tunnel ips exceeds the maximum 1.")


class TunnelIPsRequired(nexception.BadRequest):
    message = _("Unable to complete operation for Gateway Device. "
                "The tunnel ips are required for %(gw_type)s type.")


class OperationRemoteMacEntryNotSupported(nexception.Conflict):
    message = _("Unable to operate remote_mac_entry for gateway device "
                "%(type)s type.")


def _validate_port_or_none(data, valid_values=None):
    if data is None:
        return
    return validators.validate_range(data, [0, 65535])


validators.add_validator('_midonet_port_or_none', _validate_port_or_none)


GATEWAY_DEVICE = 'gateway_device'
GATEWAY_DEVICES = '%ss' % GATEWAY_DEVICE

HW_VTEP_TYPE = 'hw_vtep'
ROUTER_DEVICE_TYPE = 'router_vtep'
NETWORK_VLAN_TYPE = 'network_vlan'
gateway_device_valid_types = [HW_VTEP_TYPE, ROUTER_DEVICE_TYPE,
                              NETWORK_VLAN_TYPE]

OVSDB = 'ovsdb'
gateway_device_valid_protocols = [OVSDB]

GATEWAY_DEVICE_PREFIX = '/gw'
PLURAL_IES = 'ies'

LOG = logging.getLogger(__name__)

# Attribute Map
RESOURCE_ATTRIBUTE_MAP = {
    'gateway_devices': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': db_const.NAME_FIELD_SIZE},
                 'default': "",
                 'is_visible': True},
        'type': {'allow_post': True, 'allow_put': False,
                 'validate': {'type:values': gateway_device_valid_types},
                 'default': HW_VTEP_TYPE,
                 'is_visible': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'required_by_policy': True,
                      'validate': {
                          'type:string': db_const.PROJECT_ID_FIELD_SIZE
                      },
                      'is_visible': True},
        'management_ip': {'allow_post': True, 'allow_put': False,
                          'default': None,
                          'validate': {'type:ip_address_or_none': None},
                          'is_visible': True},
        'management_port': {'allow_post': True, 'allow_put': False,
                            'validate': {'type:_midonet_port_or_none': None},
                            'default': None, 'is_visible': True},
        'management_protocol': {'allow_post': True, 'allow_put': False,
                                'is_visible': True, 'default': None},
        'resource_id': {'allow_post': True, 'allow_put': False,
                        'validate': {
                            'type:string': db_const.DEVICE_ID_FIELD_SIZE},
                        'is_visible': True, 'required_by_policy': True,
                        'default': ""},
        'tunnel_ips': {'allow_post': True, 'allow_put': True,
                       'is_visible': True, 'default': ''},
        'remote_mac_entries': {'allow_post': False, 'allow_put': False,
                               'default': None,
                               'is_visible': True}
    }
}

SUB_RESOURCE_ATTRIBUTE_MAP = {
    'remote_mac_entries': {
        'parent': {'collection_name': 'gateway_devices',
                   'member_name': 'gateway_device'},
        'parameters': {'id': {
            'allow_post': False, 'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True,
            'primary_key': True},
            'vtep_address': {
                'allow_post': True, 'allow_put': False,
                'is_visible': True, 'default': None,
                'validate': {'type:ip_address': None}},
            'mac_address': {
                'allow_post': True, 'allow_put': False,
                'is_visible': True,
                'validate': {'type:mac_address': None}},
            'segmentation_id': {
                'allow_post': True, 'allow_put': False,
                'is_visible': True,
                'validate': {'type:non_negative': None}},
            # FIXME(kengo): Workaround to avoid 400 error
            # when issue creation request without tenant_id.
            # We will address with one of following solution this
            # after discussion with neutron.
            # 1. delete this definition if neutron core is modified.
            # 2. add DB column and remain this definition
            #    if neutron core is not modified.
            'tenant_id': {
                'allow_post': True,
                'allow_put': False,
                'required_by_policy': True,
                'validate': {'type:string': db_const.PROJECT_ID_FIELD_SIZE},
                'is_visible': False}
        }
    }
}


class Gateway_device(api_extensions.ExtensionDescriptor):
    """Gateway device extension."""

    @classmethod
    def get_name(cls):
        return "Midonet Gateway Device Extension"

    @classmethod
    def get_alias(cls):
        return "gateway-device"

    @classmethod
    def get_description(cls):
        return "The gateway device extension."

    @classmethod
    def get_updated(cls):
        return "2015-11-11T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""

        plural_mappings = resource_helper.build_plural_mappings(
            {}, RESOURCE_ATTRIBUTE_MAP)

        resources = resource_helper.build_resource_info(
            plural_mappings,
            RESOURCE_ATTRIBUTE_MAP,
            constants.GATEWAY_DEVICE)
        plugin = directory.get_plugin(constants.GATEWAY_DEVICE)

        for collection_name in SUB_RESOURCE_ATTRIBUTE_MAP:
            # Special handling needed for sub-resources with 'y' ending
            # (e.g. proxies -> proxy)
            if collection_name[-3:] == PLURAL_IES:
                resource_name = collection_name[:-3] + 'y'
            else:
                resource_name = collection_name[:-1]
            parent = SUB_RESOURCE_ATTRIBUTE_MAP[collection_name].get('parent')
            params = SUB_RESOURCE_ATTRIBUTE_MAP[collection_name].get(
                'parameters')

            controller = base.create_resource(collection_name, resource_name,
                                              plugin, params,
                                              allow_bulk=True,
                                              parent=parent)

            resource = extensions.ResourceExtension(
                collection_name,
                controller, parent,
                path_prefix=GATEWAY_DEVICE_PREFIX,
                attr_map=params)
            resources.append(resource)

        return resources

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


@six.add_metaclass(abc.ABCMeta)
class GwDevicePluginBase(object):

    path_prefix = GATEWAY_DEVICE_PREFIX

    @abc.abstractmethod
    def create_gateway_device(self, context, gw_dev):
        pass

    @abc.abstractmethod
    def update_gateway_device(self, context, id, gw_dev):
        pass

    @abc.abstractmethod
    def delete_gateway_device(self, context, id):
        pass

    @abc.abstractmethod
    def get_gateway_devices(self, context, filters=None, fields=None,
                            sorts=None, limit=None, marker=None,
                            page_reverse=False):
        pass

    @abc.abstractmethod
    def get_gateway_device(self, context, id, fields=None):
        pass

    @abc.abstractmethod
    def create_gateway_device_remote_mac_entry(self, context,
                                               gateway_device_id,
                                               remote_mac_entry):
        pass

    @abc.abstractmethod
    def delete_gateway_device_remote_mac_entry(self, context,
                                               id, gateway_device_id):
        pass

    @abc.abstractmethod
    def get_gateway_device_remote_mac_entries(self, context, gateway_device_id,
                                              filters=None, fields=None,
                                              sorts=None, limit=None,
                                              marker=None, page_reverse=False):
        pass

    @abc.abstractmethod
    def get_gateway_device_remote_mac_entry(self, context, id,
                                            gateway_device_id, fields=None):
        pass
