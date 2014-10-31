# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from neutron.openstack.common import log as logging

LOG = logging.getLogger(__name__)

HOST = 'host'
HOSTS = '%ss' % HOST
HOST_INTERFACE = 'host_interfaces'
HOST_INTERFACES = '%ss' % HOST_INTERFACE

HOST_INTERFACE_ATTRIBUTE_MAP = {
    'host_id': {'allow_post': False, 'allow_put': False,
                'validate': {'type:uuid': None},
                'is_visible': True, 'primary_key': True},
    'name': {'allow_post': False, 'allow_put': False,
             'validate': {'type:string': None},
             'is_visible': True, 'default': ''},
    'mac': {'allow_post': False, 'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True, 'default': ''},
    'mtu': {'allow_post': False, 'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True, 'default': ''},
    'status': {'allow_post': False, 'allow_put': False,
               'validate': {'type:string': None},
               'is_visible': True, 'default': ''},
    'type': {'allow_post': False, 'allow_put': False,
             'validate': {'type:string': None},
             'is_visible': True, 'default': ''},
    'endpoint': {'allow_post': False, 'allow_put': False,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': ''},
    'port_type': {'allow_post': False, 'allow_put': False,
                  'validate': {'type:string': None},
                  'is_visible': True, 'default': ''},
    'addresses': {'allow_post': False, 'allow_put': False,
                  'validate': {'type:string': None},
                  'is_visible': True, 'default': ''},
}

RESOURCE_ATTRIBUTE_MAP = {
    HOSTS: {
        'id': {'allow_post': False, 'allow_put': False,
               'is_visible': True,
               'primary_key': True},
        'name': {'allow_post': False, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': ''},
        'addresses': {'allow_post': False, 'allow_put': True,
                      'validate': {'type:string': None},
                      'is_visible': True, 'default': ''},
        'alive': {'allow_post': False, 'allow_put': False,
                  'validate': {'type:string': None},
                  'is_visible': True, 'default': False},
        'flooding_proxy_weight': {'allow_post': False, 'allow_put': False,
                                  'is_visible': True, 'default': False},
        'version': {'allow_post': False, 'allow_put': False,
                    'is_visible': True},
        'host_interfaces': {'allow_post': False, 'allow_put': False,
                            'is_visible': True, 'default': [],
                            'type:list_of_host_interfaces_or_none':
                            HOST_INTERFACE_ATTRIBUTE_MAP}
    }
}


def _validate_host_interfaces(data, valid_values):
    if not isinstance(data, list):
        msg = _("Invalid data format host_interfaces: '%s'") % data
        return msg

    for host_interface in data:
        attr.validate_dict(data, valid_values)


attr.validators['type:list_of_host_interfaces'] = (_validate_host_interfaces)


class Host(object):
    """Host extension."""

    @classmethod
    def get_name(cls):
        return "Midonet Host Extension"

    @classmethod
    def get_alias(cls):
        return "host"

    @classmethod
    def get_description(cls):
        return ("Host abstraction for basic host-related features")

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/host/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2014-07-20T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        plugin = manager.NeutronManager.get_plugin()

        # hosts
        resource_name = HOST
        collection_name = HOSTS
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        controller_host = base.create_resource(collection_name,
                                               resource_name,
                                               plugin,
                                               params)

        ex = extensions.ResourceExtension(collection_name, controller_host)

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
class HostPluginBase(object):

    @abc.abstractmethod
    def update_host(self, context, id, host):
        pass

    @abc.abstractmethod
    def get_host(self, context, host, fields=None):
        pass

    @abc.abstractmethod
    def delete_host(self, context, id):
        pass

    @abc.abstractmethod
    def get_hosts(self, context, filters=None, fields=None):
        pass
