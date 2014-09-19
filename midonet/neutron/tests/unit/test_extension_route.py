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

from midonet.neutron.extensions import route

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path


class RouteExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    """Test the endpoints for the route extension."""
    fmt = "json"

    def setUp(self):
        super(RouteExtensionTestCase, self).setUp()
        plural_mappings = {'route': 'routes'}
        self._setUpExtension(
            'midonet.neutron.extensions.route.RoutePluginBase',
            None, route.RESOURCE_ATTRIBUTE_MAP,
            route.Route, '', plural_mappings=plural_mappings)

    def test_route_list(self):
        return_value = [{'id': _uuid(),
                         'src_cidr': '10.10.10.0/24',
                         'next_hop_port': _uuid()}]

        instance = self.plugin.return_value
        instance.get_routes.return_value = return_value

        res = self.api.get(_get_path('routes', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_routes.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('routes', res)
        self.assertEqual(1, len(res['routes']))

    def test_route_show(self):
        route_id = _uuid()
        return_value = {'id': route_id,
                        'src_cidr': '10.10.10.0/24',
                        'next_hop_port': _uuid()}

        instance = self.plugin.return_value
        instance.get_route.return_value = return_value

        res = self.api.get(_get_path('routes/%s' % route_id, fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_route.assert_called_once_with(
            mock.ANY, unicode(route_id), fields=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('route', res)

    def test_route_update(self):
        route_id = _uuid()
        return_value = {'id': route_id,
                        'src_cidr': '10.10.10.0/24',
                        'next_hop_port': _uuid()}
        update_data = {'route': {'src_cidr': '10.10.11.0/24'}}

        instance = self.plugin.return_value
        instance.update_route.return_value = return_value

        res = self.api.put(_get_path('routes', id=route_id, fmt=self.fmt),
                           self.serialize(update_data))

        instance.update_route.assert_called_once_with(
            mock.ANY, route_id, route=update_data)
        self.assertEqual(exc.HTTPOk.code, res.status_int)

    def test_route_delete(self):
        route_id = _uuid()

        instance = self.plugin.return_value

        res = self.api.delete(_get_path('routes', id=route_id))

        instance.delete_route.assert_called_once_with(mock.ANY, route_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)


class RouteExtensionTestCaseXml(RouteExtensionTestCase):

    fmt = "xml"
