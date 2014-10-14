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
#
# @author: Jaume Devesa, Midokura SARL

import abc

import six

from neutron.api import extensions
from neutron.api.v2 import base
from neutron import manager

SYSTEM = 'system'
SYSTEMS = '%ss' % SYSTEM


RESOURCE_ATTRIBUTE_MAP = {
    SYSTEMS: {
        'state': {'allow_post': False, 'allow_put': True,
                  'validate': {'type:values': ['UPGRADE', 'ACTIVE']},
                  'is_visible': True, 'required_by_policy': True},
        'availability': {'allow_post': False, 'allow_put': True,
                         'validate': {
                             'type:values': [
                                 'READONLY',
                                 'READWRITE'
                             ]
                         },
                         'is_visible': True, 'default': 'READWRITE',
                         'required_by_policy': True},
        'write_version': {'allow_post': False, 'allow_put': True,
                          'validate': {'type:regex': '^(\d+\.\d+)$'},
                          'is_visible': True, 'required_by_policy': True}
    }
}


class System(object):

    @classmethod
    def get_name(cls):
        return "Midonet System Control"

    @classmethod
    def get_alias(cls):
        return "system"

    @classmethod
    def get_description(cls):
        return ("Control the system for maintenance and upgrades")

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/system/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2014-07-20T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        plugin = manager.NeutronManager.get_plugin()

        # system
        resource_name = SYSTEM
        collection_name = SYSTEMS
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        controller = base.create_resource(
            collection_name, resource_name, plugin, params)
        ex = extensions.ResourceExtension(collection_name, controller)

        return [ex]

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
class SystemPluginBase(object):

    @abc.abstractmethod
    def get_system(self, context, id, fields=None):
        pass

    @abc.abstractmethod
    def update_system(self, context, id, system):
        pass
