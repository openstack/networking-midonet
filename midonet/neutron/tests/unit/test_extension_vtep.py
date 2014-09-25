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

from midonet.neutron.extensions import vtep

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path


class VtepExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    """Test the endpoints for the vtep extension."""
    fmt = "json"

    def setUp(self):
        super(VtepExtensionTestCase, self).setUp()
        plural_mappings = {'vtep': 'vteps',
                           'vtep_port': 'vtep_ports',
                           'vtep_binding': 'vtep_bindings',
                           'vxlan_port': 'vxlan_ports'}
        self._setUpExtension(
            'midonet.neutron.extensions.vtep.VtepPluginBase',
            None, vtep.RESOURCE_ATTRIBUTE_MAP,
            vtep.Vtep, '', plural_mappings=plural_mappings)

    def test_vtep_list(self):
        return_value = [{'management_ip': "1.1.1.1",
                         'name': 'dummy_vtep',
                         'tunnel_zone_id': _uuid()}]

        instance = self.plugin.return_value
        instance.get_vteps.return_value = return_value

        res = self.api.get(_get_path('vteps', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_vteps.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('vteps', res)
        self.assertEqual(1, len(res['vteps']))

    def test_vtep_show(self):
        vtep_ip = "1.1.1.1"
        return_value = {'management_ip': vtep_ip,
                        'name': 'dummy_vtep',
                        'tunnel_zone_id': _uuid()}

        instance = self.plugin.return_value
        instance.get_vtep.return_value = return_value

        res = self.api.get(_get_path('vteps/%s' % vtep_ip, fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_vtep.assert_called_once_with(
            mock.ANY, vtep_ip, fields=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('vtep', res)

    def test_vtep_create(self):

        vtep_ip = "1.1.1.1"
        data = {'vtep': {'management_ip': vtep_ip,
                        'management_port': 4,
                        'description': "bank holiday",
                        'tenant_id': _uuid(),
                        'name': 'dummy_vtep',
                        'connection_state': "DISCONNECTED",
                        'tunnel_ip_addrs': None,
                        'tunnel_zone_id': _uuid()}}
        return_value = copy.deepcopy(data['vtep'])
        instance = self.plugin.return_value
        instance.create_vtep.return_value = return_value

        res = self.api.post(_get_path('vteps', fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)

        instance.create_vtep.assert_called_once_with(mock.ANY, vtep=mock.ANY)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('vtep', res)
        self.assertIn(vtep_ip, res['vtep']['management_ip'])


class VtepExtensionTestCaseXml(VtepExtensionTestCase):

    fmt = "xml"
