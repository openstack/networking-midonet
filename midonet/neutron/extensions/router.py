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

import abc

import six

from neutron.api import extensions
from neutron.api.v2 import base
from neutron import manager

ROUTER = 'midonet_router'
ROUTERS = '%ss' % ROUTER

RESOURCE_ATTRIBUTE_MAP = {
    ROUTERS: {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True, 'default': None},
        'inbound_filter_id': {'allow_post': True, 'allow_put': True,
                              'validate': {'type:uuid_or_none': None},
                              'is_visible': True, 'default': None},
        'load_balancer_id': {'allow_post': True, 'allow_put': True,
                             'validate': {'type:uuid_or_none': None},
                             'is_visible': True, 'default': None},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': ''},
        'outbound_filter_id': {'allow_post': True, 'allow_put': True,
                               'validate': {'type:uuid_or_none': None},
                               'is_visible': True, 'default': None},
        'tenant_id': {'allow_post': True, 'allow_put': True,
                      'validate': {'type:uuid': None},
                      'is_visible': True, 'default': None},
        'vxlan_port_id': {'allow_post': False, 'allow_put': False,
                          'validate': {'type:uuid_or_none': None},
                          'is_visible': True, 'default': None}
    }
}


class Router(extensions.ExtensionDescriptor):
    """Router extension."""

    @classmethod
    def get_name(cls):
        return "Midonet Router"

    @classmethod
    def get_alias(cls):
        return "midonet-router"

    @classmethod
    def get_description(cls):
        return ("midonet router extension")

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/midonet-router/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2014-07-20T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        exts = []
        plugin = manager.NeutronManager.get_plugin()
        collection_name = ROUTERS
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        controller_host = base.create_resource(collection_name, ROUTER, plugin,
                                               params)

        ex = extensions.ResourceExtension(collection_name, controller_host)
        exts.append(ex)
        return exts

    def update_attributes_map(self, attributes):
        for resource_map, attrs in RESOURCE_ATTRIBUTE_MAP.iteritems():
            extended_attrs = attributes.get(resource_map)
            if extended_attrs:
                attrs.update(extended_attrs)

    @classmethod
    def get_extended_resources(cls, version):
        if version == "2.0":
            return dict(RESOURCE_ATTRIBUTE_MAP.items())
        else:
            return {}


@six.add_metaclass(abc.ABCMeta)
class RouterPluginBase(object):

    @abc.abstractmethod
    def get_midonet_routers(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def get_midonet_router(self, context, id, fields=None):
        pass

    @abc.abstractmethod
    def create_midonet_router(self, context, midonet_router):
        pass

    @abc.abstractmethod
    def update_midonet_router(self, context, id, midonet_router):
        pass

    @abc.abstractmethod
    def delete_midonet_router(self, context, id):
        pass
