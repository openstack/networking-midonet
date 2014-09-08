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
from neutron.openstack.common import log as logging

LOG = logging.getLogger(__name__)

DHCP_SERVER_IP = 'midonet:dhcp_server_ip'
INTERFACE_MTU = 'midonet:interface_mtu'
DHCP_HOSTS = 'midonet:dhcp_hosts'

DHCP = 'dhcp_host'
DHCPS = '%ss' % DHCP

EXTENDED_ATTRIBUTES = {
    'subnets': {
        DHCP_SERVER_IP: {'allow_post': True, 'allow_put': False,
                         'default': None,
                         'validate': {'type:ip_address_or_none': None},
                         'is_visible': True},
        INTERFACE_MTU: {'allow_post': True, 'allow_put': False,
                        'default': 1500,
                        'validate': {'type:non_negative': None},
                        'is_visible': True}
    }
}

RESOURCE_ATTRIBUTE_MAP = {

    DHCPS: {
        'ip_address': {'allow_post': True, 'allow_put': True,
                       'validate': {'type:ip_address': None},
                       'is_visible': True},
        'mac_address': {'allow_post': True, 'allow_put': True,
                        'validate': {'type:mac_address': None},
                        'is_visible': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'required_by_policy': True,
                      'validate': {'type:string': None},
                      'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True}
    }
}


class Midonet_subnet(extensions.ExtensionDescriptor):

    @classmethod
    def get_name(cls):
        return "Midonet Subnet (DHCP Subnet)"

    @classmethod
    def get_alias(cls):
        return "midonet-subnet"

    @classmethod
    def get_description(cls):
        return ("Neutron subnet with midonet extensions")

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/midonet_subnet/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2014-07-20T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        plugin = manager.NeutronManager.get_plugin()

        # hosts
        parent = dict(member_name="subnet",
                      collection_name="subnets")
        resource_name = DHCP
        collection_name = DHCPS
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        controller_host = base.create_resource(collection_name,
                                               resource_name,
                                               plugin,
                                               params,
                                               parent=parent,
                                               allow_bulk=True)

        ex = extensions.ResourceExtension(collection_name,
                                          controller_host,
                                          parent=parent)

        return [ex]

    def get_extended_resources(self, version):
        if version == "2.0":
            return EXTENDED_ATTRIBUTES
        else:
            return {}


@six.add_metaclass(abc.ABCMeta)
class DhcpHostsPluginBase(object):

    __native_bulk_support = True

    def get_plugin_name(self):
        return "DHCP Host Plugin"

    def get_plugin_type(self):
        return "dhcp-host"

    def get_plugin_description(self):
        return "Base plugin for DHCP Host extension"

    @abc.abstractmethod
    def get_subnet_dhcp_host(self, context, id,
                             subnet_id, fields=None):
        pass

    @abc.abstractmethod
    def update_subnet_dhcp_host(self, context, id, subnet_id, dhcp_host):
        pass

    @abc.abstractmethod
    def delete_subnet_dhcp_host(self, context, id, subnet_id):
        pass

    @abc.abstractmethod
    def get_subnet_dhcp_hosts(self, context, subnet_id,
                              filters=None, fields=None):
        pass

    @abc.abstractmethod
    def create_subnet_dhcp_host(self, context, subnet_id, dhcp_host):
        pass
