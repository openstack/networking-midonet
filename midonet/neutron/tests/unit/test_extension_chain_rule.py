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
import mock
from webob import exc

from neutron.openstack.common import uuidutils
from neutron.tests.unit import test_api_v2
from neutron.tests.unit import test_api_v2_extension

from midonet.neutron.extensions import chain_rule

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path


class ChainRuleExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    """Test the endpoints for the chain and rule extension."""
    fmt = "json"

    def setUp(self):
        super(ChainRuleExtensionTestCase, self).setUp()
        plural_mappings = {'chain': 'chains', 'rule': 'rules'}
        self._setUpExtension(
            'midonet.neutron.extensions.chain_rule.ChainRulePluginBase',
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

    def test_rule_delete(self):
        rule_id = _uuid()

        instance = self.plugin.return_value

        res = self.api.delete(_get_path('rules', id=rule_id))

        instance.delete_rule.assert_called_once_with(mock.ANY, rule_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)


class ChainRuleExtensionTestCaseXml(ChainRuleExtensionTestCase):

    fmt = "xml"
