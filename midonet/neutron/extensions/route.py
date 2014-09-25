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

ROUTE = 'route'
ROUTES = '%ss' % ROUTE

RESOURCE_ATTRIBUTE_MAP = {
    ROUTES: {
        'attributes': {'allow_post': True, 'allow_put': True,
            'validate': {'type:string': None},
            'is_visible': True},
        'dst_cidr': {'allow_post': True, 'allow_put': True,
            'validate': {'type:string': None},
            'is_visible': True},
        'id': {'allow_post': True, 'allow_put': True,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'next_hop_gateway': {'allow_post': True, 'allow_put': True,
            'validate': {'type:string': None},
            'is_visible': True},
        'next_hop_port': {'allow_post': True, 'allow_put': True,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'router_id': {'allow_post': True, 'allow_put': True,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'src_cidr': {'allow_post': True, 'allow_put': True,
            'validate': {'type:string': None},
            'is_visible': True},
        'type': {'allow_post': True, 'allow_put': True,
            'validate': {'type:values': ['Normal', 'BlackHole', 'Reject']},
            'is_visible': True},
        'weight': {'allow_post': True, 'allow_put': True,
            'is_visible': True},
    }
}


class Route(object):
    """Route extension."""

    @classmethod
    def get_name(cls):
        return "Midonet Route Extension"

    @classmethod
    def get_alias(cls):
        return "route"

    @classmethod
    def get_description(cls):
        return ("Route abstraction for basic route-related features")

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/route/api/v1.0"

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
class RoutePluginBase(object):

    def get_plugin_name(self):
        return "route plugin"

    def get_plugin_type(self):
        return "route"

    def get_plugin_description(self):
        return "route extension base plugin"

    @abc.abstractmethod
    def create_route(self, context, id, route):
        pass

    @abc.abstractmethod
    def update_route(self, context, id, route):
        pass

    @abc.abstractmethod
    def get_route(self, context, route, fields=None):
        pass

    @abc.abstractmethod
    def delete_route(self, context, id):
        pass

    @abc.abstractmethod
    def get_routes(self, context, filters=None, fields=None):
        pass
