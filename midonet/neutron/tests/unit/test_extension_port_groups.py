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

from midonet.neutron.extensions import port_group

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path


class PortGroupExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    """Test the endpoints for the port_group and port_group_port extension."""
    fmt = "json"

    def setUp(self):
        super(PortGroupExtensionTestCase, self).setUp()
        plural_mappings = {'port_group': 'port_groups'}
        self._setUpExtension(
            'midonet.neutron.extensions.port_group.PortGroupPluginBase',
            None, port_group.RESOURCE_ATTRIBUTE_MAP,
            port_group.Port_group, '', plural_mappings=plural_mappings)

    def test_port_group_list(self):
        return_value = [{'id': _uuid(),
                         'name': 'dummy_port_group',
                         'tenant_id': _uuid()}]
        instance = self.plugin.return_value
        instance.get_port_groups.return_value = return_value

        res = self.api.get(_get_path('port_groups', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        instance.get_port_groups.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)
        res = self.deserialize(res)
        self.assertIn('port_groups', res)
        self.assertEqual(1, len(res['port_groups']))

    def test_port_group_show(self):
        port_group_id = _uuid()
        return_value = {'id': port_group_id,
                        'name': 'dummy_port_group',
                        'tenant_id': _uuid()}

        instance = self.plugin.return_value
        instance.get_port_group.return_value = return_value

        res = self.api.get(_get_path('port_groups/%s' % port_group_id,
                                     fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_port_group.assert_called_once_with(
            mock.ANY, unicode(port_group_id), fields=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('port_group', res)

    def test_port_group_create(self):
        port_group_id = _uuid()
        data = {'port_group': {'name': 'dummy_port_group',
                               'stateful': False,
                               'tenant_id': _uuid()}}
        return_value = copy.deepcopy(data['port_group'])
        return_value.update({'id': port_group_id})
        instance = self.plugin.return_value
        instance.create_port_group.return_value = return_value
        res = self.api.post(_get_path('port_groups', fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        instance.create_port_group.assert_called_once_with(
            mock.ANY, port_group=data)
        res = self.deserialize(res)
        self.assertIn('port_group', res)
        self.assertEqual(res['port_group'], return_value)

    def test_port_group_update(self):
        port_group_id = _uuid()
        return_value = {'id': port_group_id,
                        'name': 'dummy_port_group',
                        'stateful': False,
                        'tenant_id': _uuid()}
        update_data = {'port_group': {'name': 'updated_dummy_port_group'}}
        instance = self.plugin.return_value
        instance.update_port_group.return_value = return_value

        res = self.api.put(
            _get_path('port_groups', id=port_group_id, fmt=self.fmt),
            self.serialize(update_data))
        instance.update_port_group.assert_called_once_with(
            mock.ANY, port_group_id, port_group=update_data)
        self.assertEqual(exc.HTTPOk.code, res.status_int)

    def test_port_group_delete(self):
        port_group_id = _uuid()
        instance = self.plugin.return_value

        res = self.api.delete(_get_path('port_groups', id=port_group_id))

        instance.delete_port_group.assert_called_once_with(
            mock.ANY, port_group_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)


class PortGroupExtensionTestCaseXml(PortGroupExtensionTestCase):
    fmt = "xml"


class PortGroupPortExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    """Test the endpoints for the port_group and port_group_port extension."""
    fmt = "json"

    def setUp(self):
        super(PortGroupPortExtensionTestCase, self).setUp()
        plural_mappings = {'port_group_port': 'port_group_ports'}
        self._setUpExtension(
            'midonet.neutron.extensions.port_group.PortGroupPortPluginBase',
            None, port_group.RESOURCE_ATTRIBUTE_MAP,
            port_group.Port_group, '', plural_mappings=plural_mappings)

    def test_port_group_port_list(self):
        return_value = [{'port_id': _uuid(),
                         'port_group_id': _uuid()}]

        instance = self.plugin.return_value
        instance.get_port_group_ports.return_value = return_value

        res = self.api.get(_get_path('port_group_ports', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_port_group_ports.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('port_group_ports', res)
        self.assertEqual(1, len(res['port_group_ports']))

    def test_port_group_port_show(self):
        port_group_port_id = _uuid()
        return_value = {'port_id': _uuid(),
                        'port_group_id': _uuid()}

        instance = self.plugin.return_value
        instance.get_port_group_port.return_value = return_value

        res = self.api.get(
            _get_path('port_group_ports/%s' % port_group_port_id,
                      fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        instance.get_port_group_port.assert_called_once_with(
            mock.ANY, unicode(port_group_port_id), fields=mock.ANY)
        res = self.deserialize(res)
        self.assertIn('port_group_port', res)

    def test_port_group_port_create(self):
        data = {'port_group_port': {'port_id': _uuid(),
                                    'port_group_id': _uuid(),
                                    'tenant_id': _uuid()}}
        return_value = data['port_group_port']
        instance = self.plugin.return_value
        instance.create_port_group_port.return_value = return_value

        res = self.api.post(_get_path('port_group_ports', fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        instance.create_port_group_port.assert_called_once_with(
            mock.ANY, port_group_port=data)
        res = self.deserialize(res)
        self.assertIn('port_group_port', res)
        self.assertEqual(res['port_group_port'], return_value)

    def test_port_group_port_delete(self):
        port_group_port_id = _uuid()

        instance = self.plugin.return_value

        res = self.api.delete(_get_path('port_group_ports',
                                        id=port_group_port_id))

        instance.delete_port_group_port.assert_called_once_with(
            mock.ANY, port_group_port_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)


class PortGroupPortExtensionTestCaseXml(PortGroupPortExtensionTestCase):
    fmt = "xml"
