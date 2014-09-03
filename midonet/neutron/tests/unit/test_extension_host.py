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

from midonet.neutron.extensions import host

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path


class HostExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    """Test the endpoints for the host."""
    fmt = "json"

    def setUp(self):
        super(HostExtensionTestCase, self).setUp()
        plural_mappings = {'host': 'hosts'}
        self._setUpExtension(
            'midonet.neutron.extensions.host.HostPluginBase',
            host.HOST, host.RESOURCE_ATTRIBUTE_MAP,
            host.Host, '', plural_mappings=plural_mappings)

    def test_host_list(self):
        return_value = [{'id': _uuid(),
                         'name': 'dummy_host',
                         'alive': True,
                         'addresses': ['88.75.32.2'],
                         'version': 1.6,
                         'host_interfaces': 'foo'}]

        instance = self.plugin.return_value
        instance.get_hosts.return_value = return_value

        res = self.api.get(_get_path('hosts', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_hosts.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('hosts', res)
        self.assertEqual(1, len(res['hosts']))

    def test_host_show(self):
        host_id = _uuid()
        return_value = {'id': host_id,
                        'name': 'dummy_host',
                        'alive': True,
                        'addresses': ['88.75.32.2'],
                        'version': 1.6,
                        'host_interfaces': [
                            {'host_id': host_id,
                             'name': 'dummy_interface',
                             'mac': '00:00:01:23:43:FE',
                             'status': 'UP',
                             'type': 'eth1',
                             'addresses': ['88.75.32.2'],
                             'version': 1.6}]
                        }

        instance = self.plugin.return_value
        instance.get_host.return_value = return_value

        res = self.api.get(_get_path('hosts/%s' % host_id, fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_host.assert_called_once_with(
            mock.ANY, unicode(host_id), fields=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('host', res)

    def test_host_update(self):
        host_id = _uuid()
        return_value = {'id': host_id,
                        'name': 'updated_name',
                        'alive': True,
                        'addresses': ['88.75.32.2'],
                        'version': 1.6}
        update_data = {'host': {'name': 'updated_name'}}

        instance = self.plugin.return_value
        instance.update_host.return_value = return_value

        res = self.api.put(_get_path('hosts', id=host_id, fmt=self.fmt),
                           self.serialize(update_data))

        instance.update_host.assert_called_once_with(
            mock.ANY, host_id, host=update_data)
        self.assertEqual(exc.HTTPOk.code, res.status_int)

    def test_host_delete(self):
        host_id = _uuid()

        instance = self.plugin.return_value

        res = self.api.delete(_get_path('hosts', id=host_id))

        instance.delete_host.assert_called_once_with(mock.ANY, host_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)


class HostExtensionTestCaseXml(HostExtensionTestCase):

    fmt = "xml"
