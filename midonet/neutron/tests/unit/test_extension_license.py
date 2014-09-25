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

from midonet.neutron.extensions import license

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path


class LicenseExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    """Test the endpoints for the license."""
    fmt = "json"

    def setUp(self):
        super(LicenseExtensionTestCase, self).setUp()
        plural_mappings = {'license': 'licenses'}
        self._setUpExtension(
            'midonet.neutron.extensions.license.LicensePluginBase',
            license.LICENSE, license.RESOURCE_ATTRIBUTE_MAP,
            license.License, '', plural_mappings=plural_mappings)

    def test_license_list(self):
        return_value = [{'id': _uuid(),
                         'description': 'whatevs'}]

        instance = self.plugin.return_value
        instance.get_licenses.return_value = return_value

        res = self.api.get(_get_path('licenses', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_licenses.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('licenses', res)
        self.assertEqual(1, len(res['licenses']))

    def test_license_show(self):
        license_id = _uuid()
        return_value = {'id': _uuid(),
                        'description': 'whatevs'}

        instance = self.plugin.return_value
        instance.get_license.return_value = return_value

        res = self.api.get(_get_path('licenses/%s' % license_id, fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_license.assert_called_once_with(
            mock.ANY, unicode(license_id), fields=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('license', res)

    def test_license_delete(self):
        license_id = _uuid()

        instance = self.plugin.return_value

        res = self.api.delete(_get_path('licenses', id=license_id))

        instance.delete_license.assert_called_once_with(mock.ANY, license_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)


class LicenseExtensionTestCaseXml(LicenseExtensionTestCase):

    fmt = "xml"
