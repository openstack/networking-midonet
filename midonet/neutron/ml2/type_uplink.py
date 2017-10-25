# Copyright (c) 2015 Midokura SARL
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from neutron_lib import exceptions as exc
from neutron_lib.plugins.ml2 import api
from oslo_log import log

from midonet.neutron.common import constants as const

LOG = log.getLogger(__name__)


class UplinkTypeDriver(api.ML2TypeDriver):
    """Type driver for Uplink networks

    This type driver differentiates uplinks networks from other types.
    """

    def __init__(self):
        LOG.info("ML2 UplinkTypeDriver initialization complete")

    def initialize(self):
        pass

    def get_type(self):
        return const.TYPE_UPLINK

    def is_partial_segment(self, segment):
        return False

    def validate_provider_segment(self, segment):
        for key, value in segment.items():
            if value and key != api.NETWORK_TYPE:
                msg = _("%s prohibited for uplink provider network") % key
                raise exc.InvalidInput(error_message=msg)

    def reserve_provider_segment(self, context, segment):
        return segment

    def allocate_tenant_segment(self, context):
        return {api.NETWORK_TYPE: const.TYPE_UPLINK}

    def release_segment(self, context, segment):
        pass

    def get_mtu(self, physical):
        pass
