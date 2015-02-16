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

from midonet.neutron.extensions import bgp

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path


class BgpExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    fmt = "json"

    def setUp(self):
        super(BgpExtensionTestCase, self).setUp()
        plural_mappings = {'bgp': 'bgps', 'ad_route': 'ad_routes'}
        self._setUpExtension(
            'neutron.plugins.midonet.plugin.MidonetPluginV2',
            None, bgp.RESOURCE_ATTRIBUTE_MAP,
            bgp.Bgp, '', plural_mappings=plural_mappings)

    def test_bgp_list(self):
        return_value = [{'id': _uuid(),
                         'local_as': 65,
                         'peer_as': 68}]

        instance = self.plugin.return_value
        instance.get_bgps.return_value = return_value

        res = self.api.get(_get_path('bgps', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_bgps.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('bgps', res)
        self.assertEqual(1, len(res['bgps']))

    def test_bgp_show(self):
        bgp_id = _uuid()
        return_value = {'id': _uuid(),
                        'local_as': 65,
                        'peer_as': 68}

        instance = self.plugin.return_value
        instance.get_bgp.return_value = return_value

        res = self.api.get(_get_path('bgps', id=bgp_id, fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_bgp.assert_called_once_with(
            mock.ANY, str(bgp_id), fields=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('bgp', res)

    def test_bgp_create(self):
        bgp_id = _uuid()
        data = {'bgp': {'local_as': 12345,
                        'peer_as': 12345,
                        'peer_addr': '10.0.1.1',
                        'tenant_id': _uuid()}}
        instance = self.plugin.return_value
        instance.create_bgp.return_value = {}

        res = self.api.post(_get_path('bgps'),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        instance.create_bgp.assert_called_once_with(
            mock.ANY, bgp=data)

        return_value = copy.deepcopy(data['bgp'])
        return_value['id'] = bgp_id
        instance = self.plugin.return_value
        instance.get_bgp.return_value = return_value
        res = self.api.get(_get_path('bgps', id=bgp_id, fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        instance.get_bgp.assert_called_once_with(
            mock.ANY, str(bgp_id), fields=mock.ANY)
        self.assertIn('bgp', res)

    def test_bgp_delete(self):
        bgp_id = _uuid()

        instance = self.plugin.return_value

        res = self.api.delete(_get_path('bgps', id=bgp_id))

        instance.delete_bgp.assert_called_once_with(mock.ANY, bgp_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)

    def test_ad_route_list(self):
        return_value = [{'id': _uuid(),
                         'nw_prefix': "10.0.0.0",
                         'prefix_length': 24}]

        instance = self.plugin.return_value
        instance.get_ad_routes.return_value = return_value

        res = self.api.get(_get_path('ad_routes', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_ad_routes.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('ad_routes', res)
        self.assertEqual(1, len(res['ad_routes']))

    def test_ad_route_show(self):
        ad_route_id = _uuid()
        return_value = {'id': _uuid(),
                        'nw_prefix': "10.0.0.0",
                        'prefix_length': 24}

        instance = self.plugin.return_value
        instance.get_ad_route.return_value = return_value

        res = self.api.get(_get_path('ad_routes', id=ad_route_id,
                                     fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_ad_route.assert_called_once_with(
            mock.ANY, str(ad_route_id), fields=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('ad_route', res)

    def test_ad_route_create(self):
        ad_route_id = _uuid()
        data = {'ad_route': {'nw_prefix': '10.0.0.1',
                             'prefix_length': 24,
                             'tenant_id': _uuid()}}
        instance = self.plugin.return_value

        res = self.api.post(_get_path('ad_routes', fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        instance.create_ad_route.assert_called_once_with(
            mock.ANY, ad_route=data)

        return_value = copy.deepcopy(data['ad_route'])
        return_value['id'] = ad_route_id
        instance = self.plugin.return_value
        instance.get_ad_route.return_value = return_value
        res = self.api.get(_get_path('ad_routes', id=ad_route_id,
                                     fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        instance.get_ad_route.assert_called_once_with(
            mock.ANY, str(ad_route_id), fields=mock.ANY)
        self.assertIn('ad_route', res)

    def test_ad_route_delete(self):
        ad_route_id = _uuid()

        instance = self.plugin.return_value
        instance.delete_ad_route.return_value = {}

        res = self.api.delete(_get_path('ad_routes', id=ad_route_id))

        instance.delete_ad_route.assert_called_once_with(mock.ANY, ad_route_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)
