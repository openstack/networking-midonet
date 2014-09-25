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

from midonet.neutron.extensions import bridge

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path


class BridgeExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    fmt = "json"

    def setUp(self):
        super(BridgeExtensionTestCase, self).setUp()
        plural_mappings = {'bridge': 'bridges'}
        self._setUpExtension(
            'midonet.neutron.extensions.bridge.BridgePluginBase',
            bridge.BRIDGE, bridge.RESOURCE_ATTRIBUTE_MAP,
            bridge.Bridge, '', plural_mappings=plural_mappings)

    def test_bridge_list(self):
        return_value = [{'id': _uuid(),
                         'name': 'BLAH BLAH',
                         'inbound_filter_id': _uuid(),
                         'outbound_filter_id': _uuid(),
                         'tenant_id': _uuid()}]

        instance = self.plugin.return_value
        instance.get_bridges.return_value = return_value

        res = self.api.get(_get_path('bridges', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_bridges.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('bridges', res)
        self.assertEqual(1, len(res['bridges']))

    def test_bridge_show(self):
        bridge_id = _uuid()
        return_value = {'id': bridge_id,
                        'name': 'BLAH BLAH',
                        'inbound_filter_id': _uuid(),
                        'outbound_filter_id': _uuid(),
                        'tenant_id': _uuid()}

        instance = self.plugin.return_value
        instance.get_bridge.return_value = return_value

        res = self.api.get(_get_path('bridges/%s' % bridge_id,
                           fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_bridge.assert_called_once_with(
            mock.ANY, unicode(bridge_id), fields=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('bridge', res)

    def test_bridge_update(self):
        bridge_id = _uuid()
        return_value = {'id': bridge_id,
                        'name': 'BLAH BLAH',
                        'inbound_filter_id': _uuid(),
                        'outbound_filter_id': _uuid(),
                        'tenant_id': _uuid()}

        update_data = {'bridge': {'name': 'ladeeda'}}

        instance = self.plugin.return_value
        instance.update_bridge.return_value = return_value

        res = self.api.put(_get_path('bridges', id=bridge_id,
                           fmt=self.fmt), self.serialize(update_data))

        instance.update_bridge.assert_called_once_with(
            mock.ANY, bridge_id, bridge=update_data)
        self.assertEqual(exc.HTTPOk.code, res.status_int)

    def test_bridge_delete(self):
        bridge_id = _uuid()

        instance = self.plugin.return_value

        res = self.api.delete(_get_path('bridges', id=bridge_id))

        instance.delete_bridge.assert_called_once_with(mock.ANY, bridge_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)


class BridgeExtensionTestCaseXml(BridgeExtensionTestCase):

    fmt = "xml"
