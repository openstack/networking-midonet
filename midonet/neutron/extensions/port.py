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
from neutron.api.v2 import attributes as attr
from neutron.api.v2 import base
from neutron import manager

PORT = 'midonet_port'
PORTS = '%ss' % PORT


# Monkey patches to add validations.
def _validate_non_negative_or_none(data, valid_values=None):
    if data is not None:
        attr._validate_non_negative_or_none(data, valid_values)


def _validate_range_or_none(data, valid_values=None):
    if data is not None:
        attr._validate_range(data, valid_values)


attr.validators['type:non_negative_or_none'] = _validate_non_negative_or_none
attr.validators['type:range_or_none'] = _validate_range_or_none


RESOURCE_ATTRIBUTE_MAP = {
    PORTS: {
        'device_id': {'allow_post': False, 'allow_put': False,
                      'validate': {'type:uuid': None},
                      'is_visible': True},
        'host_id': {'allow_post': False, 'allow_put': False,
                    'validate': {'type:uuid_or_none': None},
                    'is_visible': True, 'default': None},
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True},
        'inbound_filter_id': {'allow_post': True, 'allow_put': True,
                              'validate': {'type:uuid_or_none': None},
                              'is_visible': True, 'default': None},
        'interface_name': {'allow_post': True, 'allow_put': False,
                           'validate': {'type:string_or_none': None},
                           'is_visible': True, 'default': None},
        'network_cidr': {'allow_post': True, 'allow_put': True,
                         'validate': {'type:subnet_or_none': None},
                         'is_visible': True, 'default': None},
        'outbound_filter_id': {'allow_post': True, 'allow_put': True,
                               'validate': {'type:uuid_or_none': None},
                               'is_visible': True, 'default': None},
        'peer_id': {'allow_post': True, 'allow_put': True,
                    'validate': {'type:uuid_or_none': None},
                    'is_visible': True, 'default': None},
        'port_address': {'allow_post': True, 'allow_put': True,
                         'validate': {'type:ip_address_or_none': None},
                         'is_visible': True, 'default': None},
        'port_mac': {'allow_post': True, 'allow_put': True,
                     'validate': {'type:mac_address_or_none': None},
                     'is_visible': True, 'default': None},
        'type': {'allow_post': True, 'allow_put': True,
                 'validate': {
                     'type:values': [
                         'Bridge',
                         'Router',
                         'ExteriorBridge',
                         'ExteriorRouter',
                         'InteriorBridge',
                         'InteriorRouter',
                         'Vxlan'
                     ]
                 },
                 'is_visible': True},
        'vif_id': {'allow_post': True, 'allow_put': True,
                   'validate': {'type:uuid_or_none': None},
                   'is_visible': True, 'default': None},
        'vlan_id': {'allow_post': True, 'allow_put': True,
                    'validate': {'type:range_or_none': [0, 65335]},
                    'is_visible': True, 'default': None},
        'vni': {'allow_post': True, 'allow_put': True,
                'validate': {'type:non_negative_or_none': None},
                'is_visible': True, 'default': None},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'required_by_policy': True,
                      'validate': {'type:uuid': None},
                      'is_visible': True}
    }
}


class Port(object):
    """Port extension."""

    @classmethod
    def get_name(cls):
        return "Midonet Port Extension"

    @classmethod
    def get_alias(cls):
        return "midonet-port"

    @classmethod
    def get_description(cls):
        return "Port abstraction for basic port-related features"

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
        controller = base.create_resource(
            collection_name, resource_name, plugin, params)
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

    @abc.abstractmethod
    def get_midonet_port(self, context, midonet_port, fields=None):
        pass

    @abc.abstractmethod
    def get_midonet_ports(self, context, fields=None, filters=None):
        pass

    @abc.abstractmethod
    def create_midonet_port(self, context, midonet_port):
        pass

    @abc.abstractmethod
    def update_midonet_port(self, context, id, midonet_port):
        pass

    @abc.abstractmethod
    def delete_midonet_port(self, context, id):
        pass
