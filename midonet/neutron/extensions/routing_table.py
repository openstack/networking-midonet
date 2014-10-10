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

ROUTE = 'routing_table'
ROUTES = '%ss' % ROUTE

RESOURCE_ATTRIBUTE_MAP = {
    ROUTES: {
        'attributes': {'allow_post': True, 'allow_put': True,
                       'validate': {'type:string_or_none': None},
                       'is_visible': True, 'default': None},
        'dst_cidr': {'allow_post': True, 'allow_put': True,
                     'validate': {'type:subnet': None},
                     'is_visible': True, 'required_by_policy': True},
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True},
        'next_hop_gateway': {'allow_post': True, 'allow_put': True,
                             'validate': {'type:ip_address': None},
                             'is_visible': True, 'required_by_policy': True},
        'next_hop_port': {'allow_post': True, 'allow_put': True,
                          'validate': {'type:uuid': None},
                          'is_visible': True, 'required_by_policy': True},
        'router_id': {'allow_post': True, 'allow_put': True,
                      'validate': {'type:uuid': None},
                      'is_visible': True},
        'src_cidr': {'allow_post': True, 'allow_put': True,
                     'validate': {'type:subnet': None},
                     'is_visible': True, 'required_by_policy': True},
        'type': {'allow_post': True, 'allow_put': True,
                 'validate': {
                     'type:values': ['Normal', 'BlackHole', 'Reject']
                 },
                 'is_visible': True},
        'weight': {'allow_post': True, 'allow_put': True,
                   'validate': {'type:non_negative': None},
                   'is_visible': True, 'required_by_policy': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:uuid': None},
                      'is_visible': True}
    }
}


class Routing_table(object):
    """Routing Table extension."""

    @classmethod
    def get_name(cls):
        return "Midonet RoutingTable Extension"

    @classmethod
    def get_alias(cls):
        return "routing-table"

    @classmethod
    def get_description(cls):
        return ("RoutingTable abstraction for basic routing_table-related"
                " features")

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/routing_table/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2014-07-20T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        exts = []
        plugin = manager.NeutronManager.get_plugin()

        resource_name = ROUTE
        collection_name = ROUTES
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        controller_host = base.create_resource(collection_name,
                                               resource_name,
                                               plugin,
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
class RoutingTablePluginBase(object):

    @abc.abstractmethod
    def get_routing_table(self, context, id, fields=None):
        pass

    @abc.abstractmethod
    def get_routing_tables(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def create_routing_table(self, context, routing_table):
        pass

    @abc.abstractmethod
    def update_routing_table(self, context, id, routing_table):
        pass

    @abc.abstractmethod
    def delete_routing_table(self, context, id):
        pass
