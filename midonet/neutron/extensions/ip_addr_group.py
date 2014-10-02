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

IP_ADDR_GROUP = 'ip_addr_group'
IP_ADDR_GROUPS = '%ss' % IP_ADDR_GROUP

IP_ADDR_GROUP_ADDR = 'ip_addr_group_addr'
IP_ADDR_GROUP_ADDRS = '%ss' % IP_ADDR_GROUP_ADDR

RESOURCE_ATTRIBUTE_MAP = {
    IP_ADDR_GROUPS: {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:uuid': None},
                      'is_visible': True}
    },
    IP_ADDR_GROUP_ADDRS: {
        'ip_addr_group_id': {'allow_post': True, 'allow_put': False,
                             'validate': {'type:uuid': None},
                             'is_visible': True},
        'addr': {'allow_post': True, 'allow_put': False,
                 'validate': {'type:ip_address': None},
                 'is_visible': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:uuid': None},
                      'is_visible': True}
    }
}


class Ip_addr_group(object):
    """Ip Addr Group extension."""

    @classmethod
    def get_name(cls):
        return "Midonet Ip Addr Group Extension"

    @classmethod
    def get_alias(cls):
        return "ip-addr-group"

    @classmethod
    def get_description(cls):
        return ("Ip Addr Group abstraction for basic "
                "ip addr group-related features")

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/ip-addr-group/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2014-07-20T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        exts = []
        plugin = manager.NeutronManager.get_plugin()

        # IP Addr Groups
        collection_name = IP_ADDR_GROUPS
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        ip_addr_group_controller = base.create_resource(
            collection_name, IP_ADDR_GROUP, plugin, params)
        ex = extensions.ResourceExtension(
            collection_name, ip_addr_group_controller)
        exts.append(ex)

        # IP Addr Group Addrs
        collection_name = IP_ADDR_GROUP_ADDRS
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        ip_addr_group_addr_controller = base.create_resource(
            collection_name, IP_ADDR_GROUP_ADDR, plugin, params)
        ex = extensions.ResourceExtension(
            collection_name, ip_addr_group_addr_controller)
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
class IpAddrGroupPluginBase(object):

    @abc.abstractmethod
    def create_ip_addr_group(self, context, ip_addr_group):
        pass

    @abc.abstractmethod
    def get_ip_addr_group(self, context, ip_addr_group, fields=None):
        pass

    @abc.abstractmethod
    def delete_ip_addr_group(self, context, id):
        pass

    @abc.abstractmethod
    def get_ip_addr_groups(self, context, filters=None, fields=None):
        pass


@six.add_metaclass(abc.ABCMeta)
class IpAddrGroupAddrPluginBase(object):

    @abc.abstractmethod
    def create_ip_addr_group_addr(self, context, ip_addr_group_addr):
        pass

    @abc.abstractmethod
    def get_ip_addr_group_addr(self, context, ip_addr_group_addr, fields=None):
        pass

    @abc.abstractmethod
    def delete_ip_addr_group_addr(self, context, id):
        pass

    @abc.abstractmethod
    def get_ip_addr_group_addrs(self, context, filters=None, fields=None):
        pass
