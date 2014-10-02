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

LICENSE = 'license'
LICENSES = '%ss' % LICENSE

RESOURCE_ATTRIBUTE_MAP = {
    LICENSES: {
        'description': {'allow_post': True, 'allow_put': True,
                        'validate': {'type:string': None},
                        'is_visible': True},
        'end_date': {'allow_post': True, 'allow_put': False,
                     'validate': {'type:string': None},
                     'is_visible': True},
        'extra': {'allow_post': True, 'allow_put': False,
                  'validate': {'type:string': None},
                  'is_visible': True},
        'holder_x500': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:string': None},
                        'is_visible': True},
        'id': {'allow_post': True, 'allow_put': False,
               'validate': {'type:string': None},
               'is_visible': True},
        'issue_date': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:string': None},
                       'is_visible': True},
        'issuer_x500': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:string': None},
                        'is_visible': True},
        'product': {'allow_post': True, 'allow_put': False,
                    'validate': {'type:string': None},
                    'is_visible': True},
        'start_date': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:string': None},
                       'is_visible': True},
        'valid': {'allow_post': True, 'allow_put': False,
                  'validate': {'type:boolean': None},
                  'is_visible': True},
    }
}


class License(object):
    """License extension."""

    @classmethod
    def get_name(cls):
        return "Midonet License Extension"

    @classmethod
    def get_alias(cls):
        return "license"

    @classmethod
    def get_description(cls):
        return "License abstraction for basic license-related features"

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/license/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2014-07-20T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        exts = []
        plugin = manager.NeutronManager.get_plugin()

        resource_name = LICENSE
        collection_name = LICENSES
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
class LicensePluginBase(object):

    @abc.abstractmethod
    def update_license(self, context, id, license):
        pass

    @abc.abstractmethod
    def get_license(self, context, license, fields=None):
        pass

    @abc.abstractmethod
    def delete_license(self, context, id):
        pass

    @abc.abstractmethod
    def get_licenses(self, context, filters=None, fields=None):
        pass
