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

CHAIN = 'chain'
CHAINS = '%ss' % CHAIN

RULE = 'rule'
RULES = '%ss' % RULE

RESOURCE_ATTRIBUTE_MAP = {
    CHAINS: {
        'id': {'allow_post': True, 'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
            'validate': {'type:string': None},
            'is_visible': True},
        'rules': {'allow_post': False, 'allow_put': False,
            'is_visible': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True},
    },
    RULES: {
        'chain_id': {'allow_post': True, 'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'cond_invert': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'dl_dst': {'allow_post': True, 'allow_put': False,
            'validate': {'type:mac_address': None},
            'is_visible': True},
        'dl_dst_mask': {'allow_post': True, 'allow_put': False,
            'validate': {'type:mac_address': None},
            'is_visible': True},
        'dl_src': {'allow_post': True, 'allow_put': False,
            'validate': {'type:mac_address': None},
            'is_visible': True},
        'dl_src_mask': {'allow_post': True, 'allow_put': False,
            'validate': {'type:mac_address': None},
            'is_visible': True},
        'dlType': {'allow_post': True, 'allow_put': False,
            'validate': {'type:non_negative': None},
            'is_visible': True},
        'flow_action': {'allow_post': True, 'allow_put': False,
            'is_visible': True},
        'fragment_policy': {'allow_post': True, 'allow_put': False,
            'is_visible': True},
        'id': {'allow_post': True, 'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'in_ports': {'allow_post': True, 'allow_put': False,
            'is_visible': True},
        'inv_dl_dst': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'inv_dl_src': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'inv_dlType': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'inv_in_ports': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'inv_ip_addr_group_dst': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'inv_ip_addr_group_src': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'inv_nw_dst': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'inv_nw_proto': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'inv_nw_src': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'inv_nw_tos': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'inv_out_ports': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'inv_port_group': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'inv_tp_dst': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'inv_tp_src': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'ip_addr_group_dst': {'allow_post': True, 'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'ip_addr_group_src': {'allow_post': True, 'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'jump_chain_id': {'allow_post': True, 'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'jump_chainName': {'allow_post': True, 'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True},
        'match_forward_flow': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'match_return_flow': {'allow_post': True, 'allow_put': False,
            'validate': {'type:boolean': None},
            'is_visible': True},
        'nat_targets': {'allow_post': True, 'allow_put': False,
            'is_visible': True},
        'nw_dst_cidr': {'allow_post': True, 'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True},
        'nw_proto': {'allow_post': True, 'allow_put': False,
            'is_visible': True},
        'nw_src_cidr': {'allow_post': True, 'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True},
        'nw_tos': {'allow_post': True, 'allow_put': False,
            'validate': {'type:range': [0, 65335]},
            'is_visible': True},
        'out_ports': {'allow_post': True, 'allow_put': False,
            'is_visible': True},
        'port_group': {'allow_post': True, 'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True},
        'position': {'allow_post': True, 'allow_put': False,
            'validate': {'type:range': [0, 65335]},
            'is_visible': True},
        'properties': {'allow_post': True, 'allow_put': False,
            'is_visible': True},
        'tp_dst': {'allow_post': True, 'allow_put': False,
            'validate': {'type:range': [0, 65335]},
            'is_visible': True},
        'tp_src': {'allow_post': True, 'allow_put': False,
            'validate': {'type:range': [0, 65335]},
            'is_visible': True},
        'type': {'allow_post': True, 'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True},
    }
}


class Chain_rule(object):
    """ChainRule extension."""

    @classmethod
    def get_name(cls):
        return "Midonet ChainRule Extension"

    @classmethod
    def get_alias(cls):
        return "chain-rule"

    @classmethod
    def get_description(cls):
        return ("Chain abstraction for basic chain-related features")

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/chain/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2014-07-20T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        exts = []
        plugin = manager.NeutronManager.get_plugin()

        # Chains
        collection_name = CHAINS
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        controller_host = base.create_resource(collection_name, CHAIN, plugin,
                                               params)

        ex = extensions.ResourceExtension(collection_name, controller_host)
        exts.append(ex)

        # Rules
        collection_name = RULES
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        controller_host = base.create_resource(collection_name, RULE, plugin,
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
class ChainRulePluginBase(object):

    def get_plugin_name(self):
        return "chain-rule plugin"

    def get_plugin_type(self):
        return "chain-rule"

    def get_plugin_description(self):
        return "Chain-rule extension base plugin"

    @abc.abstractmethod
    def create_chain(self, context, id, chain):
        pass

    @abc.abstractmethod
    def update_chain(self, context, id, chain):
        pass

    @abc.abstractmethod
    def get_chain(self, context, chain, fields=None):
        pass

    @abc.abstractmethod
    def delete_chain(self, context, id):
        pass

    @abc.abstractmethod
    def get_chains(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def create_rule(self, context, id, rule):
        pass

    @abc.abstractmethod
    def get_rule(self, context, rule, fields=None):
        pass

    @abc.abstractmethod
    def delete_rule(self, context, id):
        pass

    @abc.abstractmethod
    def get_rules(self, context, filters=None, fields=None):
        pass
