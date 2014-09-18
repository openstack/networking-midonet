# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright (C) 2014 Midokura SARL.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy

import mock
from webob import exc

from neutron.openstack.common import uuidutils
from neutron.tests.unit import test_api_v2
from neutron.tests.unit import test_api_v2_extension

from midonet.neutron.extensions import tunnelzone

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path


class TunnelzoneTestCase(test_api_v2_extension.ExtensionTestCase):
    """Test the endpoints for the tunnel zones and tunnel zone hosts."""

    fmt = 'json'

    def setUp(self):
        super(TunnelzoneTestCase, self).setUp()
        plural_mappings = {'tunnelzone': 'tunnelzones',
                           'tunnelzonehost': 'tunnelzonehosts'}
        self._setUpExtension(
            'midonet.neutron.plugin.MidonetPluginV2',
            tunnelzone.TUNNELZONE, tunnelzone.RESOURCE_ATTRIBUTE_MAP,
            tunnelzone.Tunnelzone, '', plural_mappings=plural_mappings)

    def test_get_tunnelzones(self):
        return_value = [{'id': _uuid(),
                         'name': 'example_name',
                         'type': 'GRE',
                         'tenant_id': _uuid()}]
        instance = self.plugin.return_value
        instance.get_tunnelzones.return_value = return_value

        res = self.api.get(_get_path('tunnelzones', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_tunnelzones.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)
        res = self.deserialize(res)
        self.assertIn('tunnelzones', res)

    def test_get_tunnelzone(self):
        tz_id = _uuid()
        return_value = {'id': tz_id,
                        'name': 'example_name',
                        'type': 'GRE',
                        'tenant_id': _uuid()}
        instance = self.plugin.return_value
        instance.get_tunnelzone.return_value = return_value

        res = self.api.get(_get_path('tunnelzones/%s' % tz_id, fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_tunnelzone.assert_called_once_with(
            mock.ANY, str(tz_id), fields=mock.ANY)
        res = self.deserialize(res)
        self.assertIn('tunnelzone', res)

    def test_create_tunnelzone(self):
        tz_id = _uuid()
        data = {'tunnelzone': {'name': 'example_name',
                               'type': 'GRE',
                               'tenant_id': _uuid()}}
        instance = self.plugin.return_value
        instance.create_tunnelzone.return_value = {}

        res = self.api.post(_get_path('tunnelzones', fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        instance.create_tunnelzone.assert_called_once_with(
            mock.ANY, tunnelzone=data)

        return_value = copy.deepcopy(data['tunnelzone'])
        return_value['id'] = tz_id
        instance.get_tunnelzone.return_value = return_value
        res = self.api.get(_get_path('tunnelzones/%s' % tz_id, fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        instance.get_tunnelzone.assert_called_once_with(
            mock.ANY, str(tz_id), fields=mock.ANY)

    def test_update_tunnelzone(self):
        tz_id = _uuid()
        data = {'tunnelzone': {'name': 'example_name',
                               'type': 'GRE'}}
        return_value = copy.deepcopy(data['tunnelzone'])
        return_value['id'] = tz_id
        instance = self.plugin.return_value
        instance.update_tunnelzone.return_value = {}
        res = self.api.put(_get_path('tunnelzones/%s' % tz_id, fmt=self.fmt),
                           self.serialize(data),
                           content_type='application/%s' % self.fmt)
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        instance.update_tunnelzone.assert_called_once_with(
            mock.ANY, str(tz_id), tunnelzone=data)

    def test_delete_tunnelzone(self):
        tz_id = _uuid()
        instance = self.plugin.return_value
        instance.delete_tunnelzone.return_value = {}
        res = self.api.delete(_get_path('tunnelzones/%s' % tz_id))
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)
        instance.delete_tunnelzone.assert_called_once_with(
            mock.ANY, str(tz_id))

    # Tunnelzone Host
    def test_get_tunnlzonehosts(self):
        tz_id = _uuid()
        return_value = [{'id': _uuid(),
                         'host_id': _uuid(),
                         'ip_address': '10.0.1.1',
                         'tenant_id': _uuid()}]
        instance = self.plugin.return_value
        instance.get_tunnelzone_tunnelzonehosts.return_value = return_value

        res = self.api.get(_get_path(
            'tunnelzones/%s/tunnelzonehosts' % tz_id, fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_tunnelzone_tunnelzonehosts.assert_called_once_with(
            mock.ANY, filters=mock.ANY, fields=mock.ANY,
            tunnelzone_id=str(tz_id))
        res = self.deserialize(res)
        self.assertIn('tunnelzonehosts', res)

    def test_get_tunnlzonehost(self):
        tz_id = _uuid()
        tz_host_id = _uuid()
        return_value = {'id': _uuid(),
                        'host_id': _uuid(),
                        'ip_address': '10.0.1.1',
                        'tenant_id': _uuid()}
        instance = self.plugin.return_value
        instance.get_tunnelzone_tunnelzonehost.return_value = return_value

        res = self.api.get(_get_path(
            'tunnelzones/%s/tunnelzonehosts/%s' % (tz_id, tz_host_id),
            fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_tunnelzone_tunnelzonehost.assert_called_once_with(
            mock.ANY, str(tz_host_id), fields=mock.ANY,
            tunnelzone_id=str(tz_id))
        res = self.deserialize(res)
        self.assertIn('tunnelzonehost', res)

    def test_create_tunnlzonehost(self):
        tz_id = _uuid()
        tz_host_id = _uuid()
        data = {'tunnelzonehost': {'host_id': _uuid(),
                                   'ip_address': '10.0.1.1',
                                   'tenant_id': _uuid()}}
        instance = self.plugin.return_value
        instance.create_tunnelzone_tunnelzonehost.return_value = {}

        res = self.api.post(_get_path(
            'tunnelzones/%s/tunnelzonehosts' % tz_id, fmt=self.fmt),
            self.serialize(data),
            content_type='application/%s' % self.fmt)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        instance.create_tunnelzone_tunnelzonehost.assert_called_once_with(
            mock.ANY, tunnelzone_id=str(tz_id), tunnelzonehost=data)

        return_value = copy.deepcopy(data['tunnelzonehost'])
        return_value['id'] = tz_host_id
        instance.get_tunnelzone_tunnelzonehost.return_value = return_value
        res = self.api.get(_get_path(
            'tunnelzones/%s/tunnelzonehosts/%s' % (tz_id, tz_host_id),
            fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        instance.get_tunnelzone_tunnelzonehost.assert_called_once_with(
            mock.ANY, str(tz_host_id), tunnelzone_id=str(tz_id),
            fields=mock.ANY)

    def test_update_tunnelzonehost(self):
        tz_id = _uuid()
        tz_host_id = _uuid()
        data = {'tunnelzonehost': {'host_id': _uuid(),
                                   'ip_address': '10.0.1.1'}}
        return_value = copy.deepcopy(data['tunnelzonehost'])
        return_value['id'] = tz_host_id
        instance = self.plugin.return_value
        instance.update_tunnelzone_tunnelzonehost.return_value = {}
        tz_host_uri = _get_path(
            'tunnelzones/%s/tunnelzonehosts/%s' % (tz_id, tz_host_id),
            fmt=self.fmt)
        res = self.api.put(tz_host_uri, self.serialize(data),
            content_type='application/%s' % self.fmt)
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        instance.update_tunnelzone_tunnelzonehost.assert_called_once_with(
            mock.ANY, str(tz_host_id), tunnelzone_id=str(tz_id),
            tunnelzonehost=data)

    def test_delete_tunnelzonehost(self):
        tz_id = _uuid()
        tz_host_id = _uuid()
        instance = self.plugin.return_value
        instance.delete_tunnelzone_tunnelzonehost.return_value = {}
        res = self.api.delete(_get_path(
            'tunnelzones/%s/tunnelzonehosts/%s' % (tz_id, tz_host_id)))
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)
        instance.delete_tunnelzone_tunnelzonehost.assert_called_once_with(
            mock.ANY, str(tz_host_id), tunnelzone_id=str(tz_id))


class TunnelzoneTestCaseXml(TunnelzoneTestCase):
    fmt = 'xml'
