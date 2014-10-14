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
#
# @author: Jaume Devesa, Midokura SARL

import copy

import mock
from webob import exc

from neutron.openstack.common import uuidutils
from neutron.tests.unit import test_api_v2
from neutron.tests.unit import test_api_v2_extension

from midonet.neutron.extensions import system

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path


class SystemTestCase(test_api_v2_extension.ExtensionTestCase):
    """Test the endpoints for the system state."""

    fmt = "json"

    def setUp(self):
        super(SystemTestCase, self).setUp()
        plural_mappings = {'system': 'systems'}
        self._setUpExtension(
            'midonet.neutron.extensions.system.SystemPluginBase',
            None, system.RESOURCE_ATTRIBUTE_MAP,
            system.System, '', plural_mappings=plural_mappings)

    def test_get_system_state(self):
        return_value = {'state': 'ACTIVE',
                        'availability': 'READWRITE',
                        'write_version': '1.0'}

        instance = self.plugin.return_value
        instance.get_system.return_value = return_value

        res = self.api.get(_get_path('systems/midonet', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_system.assert_called_once_with(mock.ANY, 'midonet',
                fields=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('system', res)

    def test_update_system_state(self):
        data = {'system': {'state': 'UPGRADE',
                           'availability': 'READONLY',
                           'write_version': '1.0'}}

        return_value = copy.deepcopy(data['system'])
        instance = self.plugin.return_value
        instance.update_system.return_value = return_value

        res = self.api.put(_get_path('systems/midonet', fmt=self.fmt),
                           self.serialize(data),
                           content_type='application/%s' % self.fmt)
        instance.update_system.assert_called_once_with(
            mock.ANY, 'midonet', system=data)
        self.assertEqual(exc.HTTPOk.code, res.status_int)


class SystemTestCaseXml(SystemTestCase):
    fmt = "xml"
