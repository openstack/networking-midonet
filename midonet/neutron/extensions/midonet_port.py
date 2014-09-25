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

PORT = 'midonet_port'
PORTS = '%ss' % PORT

RESOURCE_ATTRIBUTE_MAP = {
    PORTS: {
        'device_id': {'allow_post': True, 'allow_put': True,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'host_id': {'allow_post': True, 'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'id': {'allow_post': True, 'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'inbound_filter_id': {'allow_post': True, 'allow_put': True,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'interface_name': {'allow_post': True, 'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True},
        'network_cidr': {'allow_post': True, 'allow_put': True,
            'validate': {'type:subnet': None},
            'is_visible': True},
        'outbound_filter_id': {'allow_post': True, 'allow_put': True,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'peer_id': {'allow_post': True, 'allow_put': True,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'port_address': {'allow_post': True, 'allow_put': True,
            'validate': {'type:string': None},
            'is_visible': True},
        'port_mac': {'allow_post': True, 'allow_put': True,
            'validate': {'type:mac_address': None},
            'is_visible': True},
        'type': {'allow_post': True, 'allow_put': True,
            'validate': {'type:string': None},
            'is_visible': True},
        'vif_id': {'allow_post': True, 'allow_put': True,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'vlan_id': {'allow_post': True, 'allow_put': True,
            'validate': {'type:range': [0, 65335]},
            'is_visible': True},
        'vni': {'allow_post': True, 'allow_put': True,
            'is_visible': True},
    }
}


class Midonet_port(object):
    """Port extension."""

    @classmethod
    def get_name(cls):
        return "Midonet Port Extension"

    @classmethod
    def get_alias(cls):
        return "midonet-port"

    @classmethod
    def get_description(cls):
        return ("Port abstraction for basic port-related features")

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/midonet-port/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2014-07-20T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        exts = []
        plugin = manager.NeutronManager.get_plugin()

        resource_name = PORT
        collection_name = PORTS
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        controller = base.create_resource(collection_name,
                                          resource_name,
                                          plugin,
                                          params)

        ex = extensions.ResourceExtension(collection_name, controller)
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
class PortPluginBase(object):

    def get_plugin_name(self):
        return "Port plugin"

    def get_plugin_type(self):
        return "midonet-port"

    def get_plugin_description(self):
        return "Port extension base plugin"

    @abc.abstractmethod
    def update_midonet_port(self, context, id, midonet_port):
        pass

    @abc.abstractmethod
    def get_midonet_port(self, context, midonet_port, fields=None):
        pass

    @abc.abstractmethod
    def delete_midonet_port(self, context, id):
        pass

    @abc.abstractmethod
    def get_midonet_ports(self, context, filters=None, fields=None):
        pass
