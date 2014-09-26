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

from midonet.neutron.extensions import routing_table

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path


class RoutingTableExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    """Test the endpoints for the routing_table extension."""
    fmt = "json"

    def setUp(self):
        super(RoutingTableExtensionTestCase, self).setUp()
        plural_mappings = {'routing_table': 'routing_tables'}
        self._setUpExtension(
            'midonet.neutron.extensions.routing_table.RoutingTablePluginBase',
            None, routing_table.RESOURCE_ATTRIBUTE_MAP,
            routing_table.Routing_table, '', plural_mappings=plural_mappings)

    def test_routing_table_list(self):
        return_value = [{'id': _uuid(),
                         'src_cidr': '10.10.10.0/24',
                         'next_hop_port': _uuid()}]

        instance = self.plugin.return_value
        instance.get_routing_tables.return_value = return_value

        res = self.api.get(_get_path('routing_tables', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_routing_tables.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('routing_tables', res)
        self.assertEqual(1, len(res['routing_tables']))

    def test_routing_table_show(self):
        routing_table_id = _uuid()
        return_value = {'id': routing_table_id,
                        'src_cidr': '10.10.10.0/24',
                        'next_hop_port': _uuid()}

        instance = self.plugin.return_value
        instance.get_routing_table.return_value = return_value

        res = self.api.get(_get_path('routing_tables/%s' % routing_table_id,
                                     fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_routing_table.assert_called_once_with(
            mock.ANY, unicode(routing_table_id), fields=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('routing_table', res)

    def test_routing_table_update(self):
        routing_table_id = _uuid()
        return_value = {'id': routing_table_id,
                        'src_cidr': '10.10.10.0/24',
                        'next_hop_port': _uuid()}
        update_data = {'routing_table': {'src_cidr': '10.10.11.0/24'}}

        instance = self.plugin.return_value
        instance.update_routing_table.return_value = return_value

        res = self.api.put(_get_path('routing_tables', id=routing_table_id,
                                     fmt=self.fmt),
                           self.serialize(update_data))

        instance.update_routing_table.assert_called_once_with(
            mock.ANY, routing_table_id, routing_table=update_data)
        self.assertEqual(exc.HTTPOk.code, res.status_int)

    def test_routing_table_delete(self):
        routing_table_id = _uuid()

        instance = self.plugin.return_value

        res = self.api.delete(_get_path('routing_tables', id=routing_table_id))

        instance.delete_routing_table.assert_called_once_with(mock.ANY,
            routing_table_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)


class RoutingTableExtensionTestCaseXml(RoutingTableExtensionTestCase):

    fmt = "xml"
