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

from midonet.neutron.extensions import ip_addr_group

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path


class IpAddrGroupExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    """Test the endpoints for the ip_addr_group and ip_addr_group_addr extension."""
    fmt = "json"

    def setUp(self):
        super(IpAddrGroupExtensionTestCase, self).setUp()
        plural_mappings = {'ip_addr_group': 'ip_addr_groups',
                           'ip_addr_group_addr': 'ip_addr_group_addrs'}
        self._setUpExtension(
            'midonet.neutron.extensions.ip_addr_group.IpAddrGroupPluginBase',
            None, ip_addr_group.RESOURCE_ATTRIBUTE_MAP,
            ip_addr_group.Ip_addr_group, '', plural_mappings=plural_mappings)

    def test_ip_addr_group_list(self):
        return_value = [{'id': _uuid(),
                         'name': 'dummy_ip_addr_group'}]

        instance = self.plugin.return_value
        instance.get_ip_addr_groups.return_value = return_value

        res = self.api.get(_get_path('ip_addr_groups', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_ip_addr_groups.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('ip_addr_groups', res)
        self.assertEqual(1, len(res['ip_addr_groups']))

    def test_ip_addr_group_show(self):
        ip_addr_group_id = _uuid()
        return_value = {'id': ip_addr_group_id,
                        'name': 'dummy_ip_addr_group'}

        instance = self.plugin.return_value
        instance.get_ip_addr_group.return_value = return_value

        res = self.api.get(_get_path('ip_addr_groups/%s' % ip_addr_group_id, fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_ip_addr_group.assert_called_once_with(
            mock.ANY, unicode(ip_addr_group_id), fields=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('ip_addr_group', res)

    def test_ip_addr_group_delete(self):
        ip_addr_group_id = _uuid()

        instance = self.plugin.return_value

        res = self.api.delete(_get_path('ip_addr_groups', id=ip_addr_group_id))

        instance.delete_ip_addr_group.assert_called_once_with(mock.ANY, ip_addr_group_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)

    def test_ip_addr_group_addr_list(self):
        return_value = [{'addr': "10.0.0.0",
                         'ip_addr_group_id': _uuid()}]

        instance = self.plugin.return_value
        instance.get_ip_addr_group_addrs.return_value = return_value

        res = self.api.get(_get_path('ip_addr_group_addrs', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_ip_addr_group_addrs.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('ip_addr_group_addrs', res)
        self.assertEqual(1, len(res['ip_addr_group_addrs']))

    def test_ip_addr_group_addr_show(self):
        ip_addr_group_addr_id = _uuid()
        return_value = {'addr': "10.0.0.0",
                        'ip_addr_group_id': _uuid()}

        instance = self.plugin.return_value
        instance.get_ip_addr_group_addr.return_value = return_value

        res = self.api.get(
            _get_path('ip_addr_group_addrs/%s' % ip_addr_group_addr_id, fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_ip_addr_group_addr.assert_called_once_with(
            mock.ANY, unicode(ip_addr_group_addr_id), fields=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('ip_addr_group_addr', res)

    def test_ip_addr_group_addr_delete(self):
        ip_addr_group_addr_id = _uuid()

        instance = self.plugin.return_value

        res = self.api.delete(_get_path('ip_addr_group_addrs', 
                                        id=ip_addr_group_addr_id))

        instance.delete_ip_addr_group_addr.assert_called_once_with(mock.ANY,
            ip_addr_group_addr_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)

class IpAddrGroupExtensionTestCaseXml(IpAddrGroupExtensionTestCase):

    fmt = "xml"
