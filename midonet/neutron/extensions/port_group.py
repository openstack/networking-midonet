# Copyright (C) 2014 Midokura SARL
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

import six

from neutron.api import extensions
from neutron.api.v2 import base
from neutron import manager

PORT_GROUP = 'port_group'
PORT_GROUPS = '%ss' % PORT_GROUP

PORT_GROUP_PORT = 'port_group_port'
PORT_GROUP_PORTS = '%ss' % PORT_GROUP_PORT

RESOURCE_ATTRIBUTE_MAP = {
    PORT_GROUP: {
        'id': {'allow_post': True, 'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
            'validate': {'type:string': None},
            'is_visible': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True},
        'stateful': {'allow_post': True, 'allow_put': True,
            'validate': {'type:boolean': None},
            'is_visible': True},
    },
    PORT_GROUP_PORT: {
        'port_id': {'allow_post': True, 'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'port_group_id': {'allow_post': True, 'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True},
    }
}


class Port_group(object):
    """Port Group extension."""

    @classmethod
    def get_name(cls):
        return "Midonet Port Group Extension"

    @classmethod
    def get_alias(cls):
        return "port-group"

    @classmethod
    def get_description(cls):
        return ("Port Group abstraction for basic port group-related features")

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/port-group/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2014-07-20T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        exts = []
        plugin = manager.NeutronManager.get_plugin()

        # Port Groups
        collection_name = PORT_GROUPS
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        controller_host = base.create_resource(collection_name, PORT_GROUP,
                                               plugin, params)

        ex = extensions.ResourceExtension(collection_name, controller_host)
        exts.append(ex)

        # Port Group Ports
        collection_name = PORT_GROUP_PORTS
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        controller_host = base.create_resource(collection_name,
                                               PORT_GROUP_PORT, plugin,
                                               params)

        ex = extensions.ResourceExtension(collection_name, controller_host)
        exts.append(ex)

        return exts

    def update_attributes_map(self, attributes):
        for resource_map, attrs in RESOURCE_ATTRIBUTE_MAP.iteritems():
            extended_attrs = attributes.get(resource_map)
            if extended_attrs:
                attrs.update(extended_attrs)

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


@six.add_metaclass(abc.ABCMeta)
class PortGroupPluginBase(object):

    def get_plugin_name(self):
        return "port-group plugin"

    def get_plugin_type(self):
        return "port-group"

    def get_plugin_description(self):
        return "port-group extension base plugin"

    @abc.abstractmethod
    def create_port_group(self, context, id, port_group):
        pass

    @abc.abstractmethod
    def get_port_group(self, context, port_group, fields=None):
        pass

    @abc.abstractmethod
    def delete_port_group(self, context, id):
        pass

    @abc.abstractmethod
    def get_port_groups(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def create_port_group_port(self, context, id, port_group_port):
        pass

    @abc.abstractmethod
    def get_port_group_port(self, context, port_group_port, fields=None):
        pass

    @abc.abstractmethod
    def delete_port_group_port(self, context, id):
        pass

    @abc.abstractmethod
    def get_port_group_ports(self, context, filters=None, fields=None):
        pass
