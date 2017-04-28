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

from neutron_lib.api import extensions
from neutron_lib import exceptions as nexception

from midonet.neutron._i18n import _
from midonet.neutron.common import constants as m_const


class MidonetBgpPeerInUse(nexception.InUse):
    message = _("bgp peer %(id)s %(reason)s")

    def __init__(self, **kwargs):
        if 'reason' not in kwargs:
            kwargs['reason'] = "is already associated with bgp speaker"
        super(MidonetBgpPeerInUse, self).__init__(**kwargs)


class NetworkTypeInvalid(nexception.InvalidInput):
    message = _("Only external network can be specified.")


class ExternalNetworkUnbound(nexception.BadRequest):
    message = _("Unable to complete operation for bgp speaker. "
                "External network must be associated with bgp speaker when "
                "logical_router is not specified in bgp speaker creation.")


class BgpSpeakerInUse(nexception.InUse):
    message = _("Bgp speaker %(id)s %(reason)s")

    def __init__(self, **kwargs):
        if 'reason' not in kwargs:
            kwargs['reason'] = "is still associated with bgp peers"
        super(BgpSpeakerInUse, self).__init__(**kwargs)


class NoSubnetInNetwork(nexception.InvalidInput):
    message = _("No subnets in the network: %(network_id)s.")


class NoGatewayIpOnSubnet(nexception.InvalidInput):
    message = _("No gateway ips on the subnet: %(subnet_id)s.")


class NoGatewayIpPortOnSubnet(nexception.InvalidInput):
    message = _("No ports have gateway ip on the subnet: %(subnet_id)s.")


EXTENDED_ATTRIBUTES_2_0 = {
    'bgp-speakers': {
        m_const.LOGICAL_ROUTER: {'allow_post': True, 'allow_put': False,
                                 'validate': {'type:uuid_or_none': None},
                                 'is_visible': True, 'default': None},
    }
}

BGP_ROUTER_EXT_ALIAS = "bgp-speaker-router-insertion"


class Bgp_speaker_router_insertion(extensions.ExtensionDescriptor):
    """Extension class supporting BgpSpeaker and Router association.

    """
    @classmethod
    def get_name(cls):
        return "BgpSpeakerRouterInsertion"

    @classmethod
    def get_alias(cls):
        return BGP_ROUTER_EXT_ALIAS

    @classmethod
    def get_description(cls):
        return "Bgp Speaker Router insertion on specified router"

    @classmethod
    def get_updated(cls):
        return "2016-04-17T10:00:00-00:00"

    def get_extended_resources(self, version):
        if version == "2.0":
            return EXTENDED_ATTRIBUTES_2_0
        else:
            return {}

    def get_required_extensions(self):
        return ["bgp"]
