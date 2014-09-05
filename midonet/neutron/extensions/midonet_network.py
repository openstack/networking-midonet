# Copyright 2014 Midokura SARL
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# @author Jaume Devesa

from neutron.api import extensions

INBOUND_FILTER_ID = 'midonet:inbound_filter_id'
OUTBOUND_FILTER_ID = 'midonet:outbound_filter_id'
VXLAN_PORT_ID = 'midonet:vxlan_port_id'

EXTENDED_ATTRIBUTES = {
    'networks': {
        INBOUND_FILTER_ID: {'allow_post': True, 'allow_put': True,
                            'validate': {'type:uuid_or_none': None},
                            'is_visible': True, 'default': None},
        OUTBOUND_FILTER_ID: {'allow_post': True, 'allow_put': True,
                             'validate': {'type:uuid_or_none': None},
                             'is_visible': True, 'default': None},
        VXLAN_PORT_ID: {'allow_post': False, 'allow_put': False,
                        'is_visible': True}
    }
}


class Midonet_network(extensions.ExtensionDescriptor):

    @classmethod
    def get_name(cls):
        return "Midonet Network (Bridge)"

    @classmethod
    def get_alias(cls):
        return "midonet-network"

    @classmethod
    def get_description(cls):
        return ("Neutron network with midonet extensions")

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/midonet-network/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2014-07-20T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        return []

    @classmethod
    def get_extended_resources(cls, version):
        if version == "2.0":
            return dict(EXTENDED_ATTRIBUTES.items())
        else:
            return {}
