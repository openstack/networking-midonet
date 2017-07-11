# Copyright 2015 OpenStack Foundation
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from neutron_lib.api import validators
from neutron_lib import exceptions

from networking_l2gw.services.l2gateway.common import constants as l2gw_const
from networking_l2gw.services.l2gateway.common import l2gw_validators

from midonet.neutron._i18n import _
from midonet.neutron.common import constants
from midonet.neutron.extensions import gateway_device


def validate_gwdevice_list(data, valid_values=None):
    """Validate the list of devices."""

    if not data:
        # Devices must be provided
        msg = _("Cannot create a gateway with an empty device list")
        return msg

    if len(data) > 1:
        # The number of devices must be exactly one
        msg = _("Exactly one device must be specified to create a gateway")
        return msg

    try:
        for device in data:
            err_msg = validators.validate_dict(device, None)
            if err_msg:
                return err_msg

            device_id = device.get('device_id')
            if not device_id:
                msg = _("Cannot create a gateway with an empty device_id")
                return msg

            # Don't accept any interface.  However, when supporting HW VTEPs
            # this must be supported.
            # TODO(RYU): Allow setting segmentation ID in some way
            if device.get('interfaces'):
                msg = _("Interfaces are not allowed in MidoNet L2GW")
                return msg
            device['interfaces'] = []
    except TypeError:
        return (_("%s: provided data are not iterable") %
                validate_gwdevice_list.__name__)


def validate_network_mapping_list_without_seg_id_validation(network_mapping,
                                                            check_vlan):
    """Validate network mapping list in connection."""
    if network_mapping.get('segmentation_id'):
        if check_vlan:
            raise exceptions.InvalidInput(
                error_message=_("default segmentation_id should not be"
                                " provided when segmentation_id is assigned"
                                " during l2gateway creation"))
        # This method doen't check segmentation id range.

    if not network_mapping.get('segmentation_id'):
        if check_vlan is False:
            raise exceptions.InvalidInput(
                error_message=_("Segmentation id must be specified in create "
                                "l2gateway connections"))
    network_id = network_mapping.get(l2gw_const.NETWORK_ID)
    if not network_id:
        raise exceptions.InvalidInput(
            error_message=_("A valid network identifier must be specified "
                            "when connecting a network to a network "
                            "gateway. Unable to complete operation"))
    connection_attrs = set(network_mapping.keys())
    if not connection_attrs.issubset(l2gw_validators.
                                     ALLOWED_CONNECTION_ATTRIBUTES):
        raise exceptions.InvalidInput(
            error_message=(_("Invalid keys found among the ones provided "
                             "in request : %(connection_attrs)s."),
                           connection_attrs))
    return network_id


def is_valid_segmentaion_id(gw_type, seg_id):
    if (gw_type == gateway_device.ROUTER_DEVICE_TYPE):
        is_valid_vxlan_id(seg_id)
    elif gw_type == gateway_device.NETWORK_VLAN_TYPE:
        l2gw_validators.is_valid_vlan_id(seg_id)


def is_valid_vxlan_id(seg_id):
    try:
        int_seg_id = int(seg_id)
    except ValueError:
        msg = _("Segmentation id must be a valid integer")
        raise exceptions.InvalidInput(error_message=msg)
    if int_seg_id < 0 or int_seg_id >= constants.MAX_VXLAN_VNI:
        msg = _("Segmentation id is out of range")
        raise exceptions.InvalidInput(error_message=msg)
