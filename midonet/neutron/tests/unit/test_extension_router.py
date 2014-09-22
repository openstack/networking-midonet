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

from midonet.neutron.extensions import router

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path

class RouterExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    fmt = "json"

    def setUp(self):
        super(RouterExtensionTestCase, self).setUp()
        plural_mappings = {'midonet_router': 'midonet_routers'}
        self._setUpExtension(
            'midonet.neutron.extensions.router.MidonetRouterPluginBase',
            router.ROUTER, router.RESOURCE_ATTRIBUTE_MAP,
            router.Router, '', plural_mappings=plural_mappings)

    def test_router_list(self):
        return_value = [{'id': _uuid(),
                         'name': 'BLAH BLAH',
                         'inbound_filter_id': _uuid(),
                         'outbound_filter_id': _uuid(),
                         'tenant_id': _uuid()}]

        instance = self.plugin.return_value
        instance.get_routers.return_value = return_value

        res = self.api.get(_get_path('routers', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_routers.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('routers', res)
        self.assertEqual(1, len(res['routers']))

    def test_router_show(self):
        router_id = _uuid()
        return_value = {'id': router_id,
                        'name': 'BLAH BLAH',
                        'inbound_filter_id': _uuid(),
                        'outbound_filter_id': _uuid(),
                        'tenant_id': _uuid()}

        instance = self.plugin.return_value
        instance.get_router.return_value = return_value

        res = self.api.get(_get_path('routers/%s' % router_id,
                           fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_router.assert_called_once_with(
            mock.ANY, unicode(router_id), fields=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('router', res)

    def test_router_update(self):
        router_id = _uuid()
        return_value = {'id': router_id,
                        'name': 'BLAH BLAH',
                        'inbound_filter_id': _uuid(),
                        'outbound_filter_id': _uuid(),
                        'tenant_id': _uuid()}

        update_data = {'router': {'name': 'ladeeda'}}

        instance = self.plugin.return_value
        instance.update_router.return_value = return_value

        res = self.api.put(_get_path('routers', id=router_id,
                           fmt=self.fmt), self.serialize(update_data))

        instance.update_router.assert_called_once_with(
            mock.ANY, router_id, router=update_data)
        self.assertEqual(exc.HTTPOk.code, res.status_int)

    def test_router_delete(self):
        router_id = _uuid()

        instance = self.plugin.return_value

        res = self.api.delete(_get_path('routers', id=router_id))

        instance.delete_router.assert_called_once_with(mock.ANY, router_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)


class RouterExtensionTestCaseXml(RouterExtensionTestCase):

    fmt = "xml"
