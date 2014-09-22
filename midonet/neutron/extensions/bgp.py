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

BGP = 'bgp'
BGPS = '%ss' % BGP

ADROUTE = 'ad_route'
ADROUTES = '%ss' % ADROUTE

RESOURCE_ATTRIBUTE_MAP = {
    BGP: {
        'id': {'allow_post': True, 'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'local_as': {'allow_post': True, 'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True},
        'peer_as': {'allow_post': False, 'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True},
        'peer_addr': {'allow_post': True, 'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True},
    },
    ADROUTE: {
        'id': {'allow_post': True, 'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'nw_prefix': {'allow_post': True, 'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True},
        'prefix_length': {'allow_post': True, 'allow_put': False,
            'validate': {'type:range': [0, 32]},
            'is_visible': True},
    }
}


class Bgp(object):
    """Bgp extension."""

    @classmethod
    def get_name(cls):
        return "Midonet Bgp Extension"

    @classmethod
    def get_alias(cls):
        return "bgp"

    @classmethod
    def get_description(cls):
        return ("Bgp abstraction for basic bgp-related features")

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/bgp/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2014-07-20T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        exts = []
        plugin = manager.NeutronManager.get_plugin()

        # Bgp
        collection_name = BGPS
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        controller_host = base.create_resource(collection_name, BGP, plugin,
                                               params)

        ex = extensions.ResourceExtension(collection_name, controller_host)
        exts.append(ex)

        # AdRoute
        collection_name = ADROUTES
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        controller_host = base.create_resource(collection_name, ADROUTE, plugin,
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
class BgpPluginBase(object):

    def get_plugin_name(self):
        return "bgp plugin"

    def get_plugin_type(self):
        return "bgp"

    def get_plugin_description(self):
        return "bgp extension base plugin"

    @abc.abstractmethod
    def create_bgp(self, context, id, bgp):
        pass

    @abc.abstractmethod
    def get_bgp(self, context, bgp, fields=None):
        pass

    @abc.abstractmethod
    def delete_bgp(self, context, id):
        pass

    @abc.abstractmethod
    def get_bgps(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def get_ad_route(self, context, ad_route, fields=None):
        pass

    @abc.abstractmethod
    def delete_ad_route(self, context, id):
        pass

    @abc.abstractmethod
    def get_ad_routes(self, context, filters=None, fields=None):
        pass
