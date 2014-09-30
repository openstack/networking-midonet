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

CHAIN = 'chain'
CHAINS = '%ss' % CHAIN

RULE = 'rule'
RULES = '%ss' % RULE


# Monkey patches to add validations.
def _validate_non_negative_or_none(data, valid_values=None):
    if data is not None:
        attr._validate_non_negative_or_none(data, valid_values)


def _validate_range_or_none(data, valid_values=None):
    if data is not None:
        attr._validate_range(data, valid_values)


attr.validators['type:non_negative_or_none'] = _validate_non_negative_or_none
attr.validators['type:range_or_none'] = _validate_range_or_none


RESOURCE_ATTRIBUTE_MAP = {
    CHAINS: {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True},
        'rules': {'allow_post': False, 'allow_put': False,
                  'validate': {
                      'type:list_or_empty': {
                          'value': {'type:uuid': None}
                      }
                  },
                  'is_visible': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:uuid': None},
                      'is_visible': True}
    },
    RULES: {
        'chain_id': {'allow_post': True, 'allow_put': False,
                     'validate': {'type:uuid': None},
                     'is_visible': True},
        'cond_invert': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:boolean': None},
                        'is_visible': True, 'default': None},
        'dl_dst': {'allow_post': True, 'allow_put': False,
                   'validate': {'type:mac_address_or_none': None},
                   'is_visible': True, 'default': None},
        'dl_dst_mask': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:mac_address_or_none': None},
                        'is_visible': True, 'default': None},
        'dl_src': {'allow_post': True, 'allow_put': False,
                   'validate': {'type:mac_address_or_none': None},
                   'is_visible': True, 'default': None},
        'dl_src_mask': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:mac_address_or_none': None},
                        'is_visible': True, 'default': None},
        'dlType': {'allow_post': True, 'allow_put': False,
                   'validate': {'type:non_negative_or_none': None},
                   'is_visible': True, 'default': None},
        'flow_action': {'allow_post': True, 'allow_put': False,
                        'validate': {
                            'type:string_or_none': [
                                'accept',
                                'continue',
                                'return'
                            ]},
                        'default': None,
                        'is_visible': True},
        'fragment_policy': {'allow_post': True, 'allow_put': False,
                            'is_visible': True,
                            'validate': {
                                'type:string_or_none': [
                                    'any',
                                    'header',
                                    'nonheader',
                                    'unfragmented'
                                ]
                            },
                            'default': None},
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True},
        'in_ports': {'allow_post': True, 'allow_put': False,
                     'is_visible': True,
                     'validates': {
                         'type:list_or_none': {
                             'value': {'type:uuid': None}
                         }
                     }},
        'inv_dl_dst': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:boolean': None},
                       'is_visible': True, 'default': False},
        'inv_dl_src': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:boolean': None},
                       'is_visible': True, 'default': False},
        'inv_dlType': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:boolean': None},
                       'is_visible': True, 'default': False},
        'inv_in_ports': {'allow_post': True, 'allow_put': False,
                         'validate': {'type:boolean': None},
                         'is_visible': True, 'default': False},
        'inv_ip_addr_group_dst': {'allow_post': True, 'allow_put': False,
                                  'validate': {'type:boolean': None},
                                  'is_visible': True, 'default': False},
        'inv_ip_addr_group_src': {'allow_post': True, 'allow_put': False,
                                  'validate': {'type:boolean': None},
                                  'is_visible': True, 'default': False},
        'inv_nw_dst': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:boolean': None},
                       'is_visible': True, 'default': False},
        'inv_nw_proto': {'allow_post': True, 'allow_put': False,
                         'validate': {'type:boolean': None},
                         'is_visible': True, 'default': False},
        'inv_nw_src': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:boolean': None},
                       'is_visible': True, 'default': False},
        'inv_nw_tos': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:boolean': None},
                       'is_visible': True, 'default': False},
        'inv_out_ports': {'allow_post': True, 'allow_put': False,
                          'validate': {'type:boolean': None},
                          'is_visible': True, 'default': False},
        'inv_port_group': {'allow_post': True, 'allow_put': False,
                           'validate': {'type:boolean': None},
                           'is_visible': True, 'default': False},
        'inv_tp_dst': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:boolean': None},
                       'is_visible': True, 'default': False},
        'inv_tp_src': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:boolean': None},
                       'is_visible': True, 'default': False},
        'ip_addr_group_dst': {'allow_post': True, 'allow_put': False,
                              'validate': {'type:uuid_or_none': None},
                              'is_visible': True, 'default': None},
        'ip_addr_group_src': {'allow_post': True, 'allow_put': False,
                              'validate': {'type:uuid_or_none': None},
                              'is_visible': True, 'default': None},
        'jump_chain_id': {'allow_post': True, 'allow_put': False,
                          'validate': {'type:uuid_or_none': None},
                          'is_visible': True, 'default': None},
        'jump_chainName': {'allow_post': True, 'allow_put': False,
                           'validate': {'type:string_or_none': None},
                           'is_visible': True, 'default': None},
        'match_forward_flow': {'allow_post': True, 'allow_put': False,
                               'validate': {'type:boolean': None},
                               'is_visible': True, 'default': False},
        'match_return_flow': {'allow_post': True, 'allow_put': False,
                              'validate': {'type:boolean': None},
                              'is_visible': True, 'default': False},
        'nat_targets': {'allow_post': True, 'allow_put': False,
                        'is_visible': True,
                        'validate': {
                            'type:list_of_dict_or_none': {
                                'addressFrom': {'type:ip_address': None,
                                                'required': True},
                                'addressTo': {'type:ip_address': None,
                                              'required': True},
                                'portFrom': {'type:range_or_none': [0, 65535],
                                             'required': True,
                                             'default': None},
                                'portTo': {'type:range_or_none': [0, 65535],
                                           'required': True,
                                           'default': None}
                            }
                        },
                        'default': None},
        'nw_dst_cidr': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:subnet_or_none': None},
                        'is_visible': True, 'default': None},
        'nw_proto': {'allow_post': True, 'allow_put': False,
                     'is_visible': True,
                     'validate': {'type:range_or_none': [0, 255]},
                     'default': None},
        'nw_src_cidr': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:subnet_or_none': None},
                        'is_visible': True, 'default': None},
        'nw_tos': {'allow_post': True, 'allow_put': False,
                   'validate': {'type:range_or_none': [0, 255]},
                   'is_visible': True, 'default': None},
        'out_ports': {'allow_post': True, 'allow_put': False,
                      'is_visible': True,
                      'validates': {
                          'type:list_or_none': {
                              'value': {'type:uuid': None}
                          }
                      },
                      'default': None},
        'port_group': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:uuid_or_none': None},
                       'is_visible': True, 'default': None},
        'position': {'allow_post': True, 'allow_put': False,
                     'validate': {'type:range_or_none': [0, 65335]},
                     'is_visible': True, 'default': None},
        'properties': {'allow_post': True, 'allow_put': False,
                       'is_visible': True, 'default': None},
        'tenant_id': {'allow_post': True, 'allow_put': True,
                      'validate': {'type:uuid': None},
                      'is_visible': True, 'default': None},
        'tp_dst': {'allow_post': True, 'allow_put': False,
                   'validate': {'type:range_or_none': [0, 65335]},
                   'is_visible': True, 'default': None},
        'tp_src': {'allow_post': True, 'allow_put': False,
                   'validate': {'type:range_or_none': [0, 65335]},
                   'is_visible': True, 'default': None},
        'type': {'allow_post': True, 'allow_put': False,
                 'validate': {'type:string': [
                     'accept',
                     'dnat',
                     'drop',
                     'jump',
                     'rev_dnat',
                     'rev_snat',
                     'reject',
                     'return',
                     'snat'
                 ]},
                 'is_visible': True,
                 'default': None}
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
        return "Chain abstraction for basic chain-related features"

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
        chain_controller = base.create_resource(
            collection_name, CHAIN, plugin, params)
        ex = extensions.ResourceExtension(collection_name, chain_controller)
        exts.append(ex)

        # Rules
        collection_name = RULES
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        rule_controller = base.create_resource(
            collection_name, RULE, plugin, params)
        ex = extensions.ResourceExtension(collection_name, rule_controller)
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
class ChainPluginBase(object):

    @abc.abstractmethod
    def create_chain(self, context, chain):
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


@six.add_metaclass(abc.ABCMeta)
class RulePluginBase(object):

    @abc.abstractmethod
    def create_rule(self, context, rule):
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
