# Copyright 2014 OpenStack Foundation
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

import copy
import mock
from webob import exc

from neutron.openstack.common import uuidutils
from neutron.tests.unit import test_api_v2
from neutron.tests.unit import test_api_v2_extension

from midonet.neutron.extensions import chain_rule

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path


class ChainExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    """Test the endpoints for the chain and rule extension."""
    fmt = "json"

    def setUp(self):
        super(ChainExtensionTestCase, self).setUp()
        plural_mappings = {'chain': 'chains'}
        self._setUpExtension(
            'midonet.neutron.extensions.chain_rule.ChainPluginBase',
            None, chain_rule.RESOURCE_ATTRIBUTE_MAP,
            chain_rule.Chain_rule, '', plural_mappings=plural_mappings)

    def test_chain_list(self):
        return_value = [{'id': _uuid(),
                         'name': 'dummy_chain',
                         'tenant_id': _uuid()}]

        instance = self.plugin.return_value
        instance.get_chains.return_value = return_value

        res = self.api.get(_get_path('chains', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_chains.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('chains', res)
        self.assertEqual(1, len(res['chains']))

    def test_chain_show(self):
        chain_id = _uuid()
        return_value = {'id': _uuid(),
                        'name': 'dummy_chain',
                        'tenant_id': _uuid()}

        instance = self.plugin.return_value
        instance.get_chain.return_value = return_value

        res = self.api.get(_get_path('chains/%s' % chain_id, fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_chain.assert_called_once_with(
            mock.ANY, unicode(chain_id), fields=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('chain', res)

    def test_chain_create(self):
        chain_id = _uuid()
        data = {'chain': {'name': 'dummy_chain',
                          'tenant_id': _uuid()}}
        return_value = copy.deepcopy(data['chain'])
        return_value.update({'id': chain_id})
        instance = self.plugin.return_value
        instance.create_chain.return_value = return_value

        res = self.api.post(_get_path('chains', fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        instance.create_chain.assert_called_once_with(
            mock.ANY, chain=data)
        res = self.deserialize(res)
        self.assertIn('chain', res)
        self.assertEqual(res['chain'], return_value)

    def test_chain_update(self):
        chain_id = _uuid()
        return_value = {'id': _uuid(),
                        'name': 'dummy_chain',
                        'tenant_id': _uuid()}
        update_data = {'chain': {'name': 'updated_name'}}

        instance = self.plugin.return_value
        instance.update_chain.return_value = return_value

        res = self.api.put(_get_path('chains', id=chain_id, fmt=self.fmt),
                           self.serialize(update_data))

        instance.update_chain.assert_called_once_with(
            mock.ANY, chain_id, chain=update_data)
        self.assertEqual(exc.HTTPOk.code, res.status_int)

    def test_chain_delete(self):
        chain_id = _uuid()

        instance = self.plugin.return_value

        res = self.api.delete(_get_path('chains', id=chain_id))

        instance.delete_chain.assert_called_once_with(mock.ANY, chain_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)


class RuleExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    """Test the endpoints for the rule extension."""
    fmt = "json"

    def setUp(self):
        super(RuleExtensionTestCase, self).setUp()
        plural_mappings = {'rule': 'rules'}
        self._setUpExtension(
            'midonet.neutron.extensions.chain_rule.RulePluginBase',
            None, chain_rule.RESOURCE_ATTRIBUTE_MAP,
            chain_rule.Chain_rule, '', plural_mappings=plural_mappings)

    def test_rule_list(self):
        return_value = [{'id': _uuid(),
                         'chain_id': _uuid(),
                         'tenant_id': _uuid()}]

        instance = self.plugin.return_value
        instance.get_rules.return_value = return_value

        res = self.api.get(_get_path('rules', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_rules.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('rules', res)
        self.assertEqual(1, len(res['rules']))

    def test_rule_show(self):
        rule_id = _uuid()
        return_value = {'id': _uuid(),
                        'chain_id': _uuid(),
                        'tenant_id': _uuid()}

        instance = self.plugin.return_value
        instance.get_rule.return_value = return_value

        res = self.api.get(_get_path('rules/%s' % rule_id, fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_rule.assert_called_once_with(
            mock.ANY, unicode(rule_id), fields=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('rule', res)

    def test_rule_create(self):
        rule_id = _uuid()
        data = {'rule': {'chain_id': _uuid(),
                         'tenant_id': _uuid(),
                         'cond_invert': False,
                         'dl_dst': None,
                         'dl_dst_mask': None,
                         'dl_src': None,
                         'dl_src_mask': None,
                         'dlType': None,
                         'flow_action': None,
                         'fragment_policy': None,
                         'in_ports': None,
                         'inv_dl_dst': False,
                         'inv_dl_src': False,
                         'inv_dlType': False,
                         'inv_in_ports': False,
                         'inv_ip_addr_group_dst': False,
                         'inv_ip_addr_group_src': False,
                         'inv_nw_dst': False,
                         'inv_nw_proto': False,
                         'inv_nw_src': False,
                         'inv_nw_tos': False,
                         'inv_out_ports': False,
                         'inv_port_group': False,
                         'inv_tp_dst': False,
                         'inv_tp_src': False,
                         'ip_addr_group_dst': None,
                         'ip_addr_group_src': None,
                         'jump_chain_id': None,
                         'jump_chainName': None,
                         'match_forward_flow': False,
                         'match_return_flow': False,
                         'nat_targets': None,
                         'nw_dst_cidr': None,
                         'nw_proto': None,
                         'nw_src_cidr': None,
                         'nw_tos': None,
                         'out_ports': None,
                         'port_group': None,
                         'position': None,
                         'properties': None,
                         'tp_dst': None,
                         'tp_src': None,
                         'type': 'accept'}}
        return_value = copy.deepcopy(data['rule'])
        return_value.update({'id': rule_id})
        instance = self.plugin.return_value
        instance.create_rule.return_value = return_value

        res = self.api.post(_get_path('rules', fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        instance.create_rule.assert_called_once_with(
            mock.ANY, rule=data)
        res = self.deserialize(res)
        self.assertIn('rule', res)
        self.assertEqual(res['rule'], return_value)

    def test_rule_delete(self):
        rule_id = _uuid()

        instance = self.plugin.return_value

        res = self.api.delete(_get_path('rules', id=rule_id))

        instance.delete_rule.assert_called_once_with(mock.ANY, rule_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)
