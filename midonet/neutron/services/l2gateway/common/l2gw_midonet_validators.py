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

from midonet.neutron.common import constants
from neutron.api.v2 import attributes
from neutron.common import exceptions


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
            err_msg = attributes._validate_dict(device, None)
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


def is_valid_vxlan_id(seg_id):
    try:
        int_seg_id = int(seg_id)
    except ValueError:
        msg = _("Segmentation id must be a valid integer")
        raise exceptions.InvalidInput(error_message=msg)
    if int_seg_id < 0 or int_seg_id >= constants.MAX_VXLAN_VNI:
        msg = _("Segmentation id is out of range")
        raise exceptions.InvalidInput(error_message=msg)
