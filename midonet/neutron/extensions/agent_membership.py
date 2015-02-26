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

from neutron.api import extensions
from neutron.api.v2 import base
from neutron.common import exceptions as nexception
from neutron import manager
import six


class AgentMembershipNotFound(nexception.NotFound):
    message = _("Agent membership %(id)s does not exist")


AGENT_MEMBERSHIP = 'agent_membership'
AGENT_MEMBERSHIPS = '%ss' % AGENT_MEMBERSHIP

# Attribute Map
RESOURCE_ATTRIBUTE_MAP = {

    'agent_memberships': {
        'id': {'allow_post': True, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True,
               'required': True},
        'ip_address': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:ip_address': None},
                       'required': True,
                       'is_visible': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'required_by_policy': True,
                      'is_visible': False}

    }
}


class Agent_membership(extensions.ExtensionDescriptor):
    """Agent membership extension."""

    @classmethod
    def get_name(cls):
        return "Midonet Agent Membership Extension"

    @classmethod
    def get_alias(cls):
        return "agent-membership"

    @classmethod
    def get_description(cls):
        return "The agent memberships extension."

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/agent_membership/api/v2.0"

    @classmethod
    def get_updated(cls):
        return "2015-02-26T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        exts = []
        plugin = manager.NeutronManager.get_plugin()

        resource_name = AGENT_MEMBERSHIP
        collection_name = AGENT_MEMBERSHIPS
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        agent_membership_controller = base.create_resource(
            collection_name, resource_name, plugin, params)
        ex = extensions.ResourceExtension(collection_name,
                                          agent_membership_controller)
        exts.append(ex)

        return exts

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


@six.add_metaclass(abc.ABCMeta)
class AgentMembershipPluginBase(object):

    @abc.abstractmethod
    def create_agent_membership(self, context, agent_membership):
        pass

    @abc.abstractmethod
    def delete_agent_membership(self, context, id):
        pass

    @abc.abstractmethod
    def get_agent_memberships(self, context, filters=None, fields=None,
                              sorts=None, limit=None, marker=None,
                              page_reverse=False):
        pass

    @abc.abstractmethod
    def get_agent_membership(self, context, id, fields=None):
        pass
