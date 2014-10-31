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

import abc

import six

from neutron.api import extensions
from neutron.api.v2 import attributes as attr
from neutron.api.v2 import base
from neutron import manager
from neutron.openstack.common import log as logging

LOG = logging.getLogger(__name__)

DHCP_HOST = 'dhcp_host'
DHCP_HOSTS = '%ss' % DHCP_HOST

SUBNET = 'midonet_subnet'
SUBNETS = '%ss' % SUBNET


# Monkey patches to add validations.
def _validate_non_negative_or_none(data, valid_values=None):
    if data is not None:
        attr._validate_non_negative(data, valid_values)


def _validate_range_or_none(data, valid_values=None):
    if data is not None:
        attr._validate_range(data, valid_values)


attr.validators['type:non_negative_or_none'] = _validate_non_negative_or_none
attr.validators['type:range_or_none'] = _validate_range_or_none


RESOURCE_ATTRIBUTE_MAP = {
    SUBNETS: {
        'default_gateway': {'allow_post': True, 'allow_put': True,
                            'validate': {'type:ip_address_or_none': None},
                            'is_visible': True, 'default': None},
        'enabled': {'allow_post': True, 'allow_put': True,
                    'validate': {'type:boolean': None},
                    'is_visible': True, 'default': True},
        'server_addr': {'allow_post': True, 'allow_put': True,
                        'validate': {'type:ip_address_or_none': None},
                        'is_visible': True, 'default': None},
        'dns_server_addrs': {'allow_post': True, 'allow_put': True,
                             'validate': {'type:ip_address_or_none': None},
                             'is_visible': True, 'default': None},
        'subnet_prefix': {'allow_post': True, 'allow_put': True,
                          'validate': {'type:ip_address_or_none': None},
                          'is_visible': True, 'default': None},
        'subnet_length': {'allow_post': True, 'allow_put': True,
                          'validate': {'type:range_or_none': [0, 32]},
                          'is_visible': True, 'default': None},
        'interface_mtu': {'allow_post': True, 'allow_put': True,
                          'validate': {'type:non_negative_or_none': None},
                          'is_visible': True, 'default': None},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'required_by_policy': True,
                      'validate': {'type:uuid': None},
                      'is_visible': True},
    },
    DHCP_HOSTS: {
        'ip_address': {'allow_post': True, 'allow_put': True,
                       'validate': {'type:ip_address': None},
                       'is_visible': True, 'required_by_policy': True},
        'mac_address': {'allow_post': True, 'allow_put': True,
                        'validate': {'type:mac_address': None},
                        'is_visible': True, 'required_by_policy': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'required_by_policy': True,
                      'validate': {'type:string': None},
                      'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True}
    }
}


class Subnet(extensions.ExtensionDescriptor):

    @classmethod
    def get_name(cls):
        return "Midonet Subnet (DHCP Subnet)"

    @classmethod
    def get_alias(cls):
        return "midonet-subnet"

    @classmethod
    def get_description(cls):
        return "Neutron subnet with midonet extensions"

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/midonet_subnet/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2014-07-20T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        exts = []
        plugin = manager.NeutronManager.get_plugin()

        # subnets
        collection_name = SUBNETS
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        subnet_controller = base.create_resource(
            collection_name, SUBNET, plugin, params, allow_bulk=True)
        ex = extensions.ResourceExtension(collection_name, subnet_controller)
        exts.append(ex)

        # hosts
        parent = dict(member_name=SUBNET,
                      collection_name=SUBNETS)
        collection_name = DHCP_HOSTS
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        host_controller = base.create_resource(
            collection_name, DHCP_HOST, plugin, params,
            parent=parent, allow_bulk=True)
        ex = extensions.ResourceExtension(
            collection_name, host_controller, parent=parent)
        exts.append(ex)

        return exts

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


@six.add_metaclass(abc.ABCMeta)
class SubnetPluginBase(object):

    @abc.abstractmethod
    def create_midonet_subnet(self, context, midonet_subnet):
        pass

    @abc.abstractmethod
    def update_midonet_subnet(self, context, id, midonet_subnet):
        pass

    @abc.abstractmethod
    def get_midonet_subnet(self, context, midonet_subnet, fields=None):
        pass

    @abc.abstractmethod
    def delete_midonet_subnet(self, context, id):
        pass

    @abc.abstractmethod
    def get_midonet_subnets(self, context, filters=None, fields=None):
        pass


@six.add_metaclass(abc.ABCMeta)
class SubnetDhcpHostPluginBase(object):

    @abc.abstractmethod
    def get_midonet_subnet_dhcp_host(self, context, id, midonet_subnet_id,
                                     fields=None):
        pass

    @abc.abstractmethod
    def update_midonet_subnet_dhcp_host(self, context, id, midonet_subnet_id,
                                        dhcp_host):
        pass

    @abc.abstractmethod
    def delete_midonet_subnet_dhcp_host(self, context, id, midonet_subnet_id):
        pass

    @abc.abstractmethod
    def get_midonet_subnet_dhcp_hosts(self, context, midonet_subnet_id,
                                      filters=None, fields=None):
        pass

    @abc.abstractmethod
    def create_midonet_subnet_dhcp_host(self, context, midonet_subnet_id,
                                        dhcp_host):
        pass
