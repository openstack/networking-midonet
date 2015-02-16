# Copyright 2014 Midokura SARL
# All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import copy
import mock
from webob import exc

from neutron.openstack.common import uuidutils
from neutron.tests.unit import test_api_v2
from neutron.tests.unit import test_api_v2_extension

from midonet.neutron.extensions import subnet

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path

MIDOKURA_EXT_PATH = "midonet.neutron.extensions"


class SubnetExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    """Test the endpoints for the host."""

    fmt = "json"

    def setUp(self):
        super(SubnetExtensionTestCase, self).setUp()
        plural_mappings = {'midonet_subnet': 'midonet_subnets'}
        self._setUpExtension(
            'midonet.neutron.extensions.subnet.SubnetPluginBase',
            None, subnet.RESOURCE_ATTRIBUTE_MAP,
            subnet.Subnet, '', plural_mappings=plural_mappings)

    def test_list_subnet(self):
        return_value = [{'default_gateway': '10.0.0.1',
                         'enabled': True,
                         'server_addr': '88.123.43.1',
                         'subnet_prefix': "10.0.0.0",
                         'dns_server_addrs': None,
                         'tenant_id': _uuid(),
                         'interface_mtu': 400,
                         'subnet_length': 24}]
        instance = self.plugin.return_value
        instance.get_midonet_subnets.return_value = return_value

        res = self.api.get(_get_path('midonet_subnets', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        instance.get_midonet_subnets.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)
        res = self.deserialize(res)
        self.assertIn('midonet_subnets', res)
        self.assertEqual(1, len(res['midonet_subnets']))

    def test_show_subnet(self):
        subnet_id = _uuid()
        return_value = {'id': subnet_id,
                        'enabled': True,
                        'default_gateway': '10.0.0.1',
                        'server_addr': '88.123.43.1',
                        'subnet_prefix': "10.0.0.0",
                        'dns_server_addrs': None,
                        'tenant_id': _uuid(),
                        'interface_mtu': 400,
                        'subnet_length': 24}
        instance = self.plugin.return_value
        instance.get_midonet_subnets.return_value = return_value

        res = self.api.get(
            _get_path('midonet_subnets', id=subnet_id, fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        instance.get_midonet_subnet.assert_called_once_with(
            mock.ANY, str(subnet_id), fields=mock.ANY)
        res = self.deserialize(res)
        self.assertIn('midonet_subnet', res)

    def test_create_subnet(self):
        default_gateway = '10.0.0.1'
        data = {'midonet_subnet': {'default_gateway': default_gateway,
                                   'enabled': True,
                                   'server_addr': '88.123.43.1',
                                   'subnet_prefix': "10.0.0.0",
                                   'dns_server_addrs': None,
                                   'tenant_id': _uuid(),
                                   'interface_mtu': 400,
                                   'subnet_length': 24}}

        return_value = copy.deepcopy(data['midonet_subnet'])
        instance = self.plugin.return_value
        instance.create_midonet_subnet.return_value = return_value

        res = self.api.post(_get_path('midonet_subnets', fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        instance.create_midonet_subnet.assert_called_once_with(
            mock.ANY, midonet_subnet=data)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('midonet_subnet', res)
        result = res['midonet_subnet']['default_gateway']
        self.assertIn(default_gateway, result)

    def test_update_subnet(self):
        subnet_id = _uuid()
        return_value = {'id': subnet_id,
                        'default_gateway': '10.0.0.1',
                        'enabled': True,
                        'server_addr': '88.123.43.1',
                        'subnet_prefix': "10.0.0.0",
                        'dns_server_addrs': None,
                        'tenant_id': _uuid(),
                        'interface_mtu': 400,
                        'subnet_length': 24}
        update_data = {'midonet_subnet': {'interface_mtu': 500}}
        instance = self.plugin.return_value
        instance.update_midonet_subnet.return_value = return_value

        res = self.api.put(
            _get_path('midonet_subnets', id=subnet_id, fmt=self.fmt),
            self.serialize(update_data))
        instance.update_midonet_subnet.assert_called_once_with(
            mock.ANY, subnet_id, midonet_subnet=update_data)
        self.assertEqual(exc.HTTPOk.code, res.status_int)

    def test_delete_subnet(self):
        subnet_id = _uuid()
        instance = self.plugin.return_value

        res = self.api.delete(_get_path('midonet_subnets', id=subnet_id))
        instance.delete_midonet_subnet.assert_called_once_with(
            mock.ANY, subnet_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)


class DhcpHostExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    """Test the endpoints for the host."""

    fmt = "json"

    def setUp(self):
        super(DhcpHostExtensionTestCase, self).setUp()
        plural_mappings = {'dhcp_host': 'dhcp_hosts'}
        self._setUpExtension(
            'midonet.neutron.extensions.subnet.SubnetDhcpHostPluginBase',
            None, subnet.RESOURCE_ATTRIBUTE_MAP,
            subnet.Subnet, '', plural_mappings=plural_mappings)

    def test_create_dhcp_host(self):

        subnet_id = _uuid()
        data = {'dhcp_host': {'ip_address': '88.123.43.2',
                              'mac_address': '01:02:03:04:05:06',
                              'name': 'name',
                              'tenant_id': _uuid()}}
        return_value = copy.deepcopy(data['dhcp_host'])
        return_value.update({'id': _uuid()})
        instance = self.plugin.return_value
        instance.create_midonet_subnet_dhcp_host.return_value = return_value

        path = 'midonet_subnets/%s/dhcp_hosts' % subnet_id,
        res = self.api.post(_get_path(path, fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)

        instance.create_midonet_subnet_dhcp_host.assert_called_once_with(
            mock.ANY, midonet_subnet_id=subnet_id, dhcp_host=data)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('dhcp_host', res)

    def test_get_dhcp_hosts(self):
        subnet_id = _uuid()
        return_value = [{'ip_address': '88.123.43.2',
                         'mac_address': '01:02:03:04:05:06',
                         'name': 'name',
                         'tenant_id': _uuid()}]

        instance = self.plugin.return_value
        instance.get_midonet_subnet_dhcp_hosts.return_value = return_value

        path = 'midonet_subnets/%s/dhcp_hosts' % subnet_id,
        res = self.api.get(_get_path(path, fmt=self.fmt))

        self.assertEqual(exc.HTTPOk.code, res.status_int)
        instance.get_midonet_subnet_dhcp_hosts.assert_called_once_with(
            mock.ANY, midonet_subnet_id=subnet_id, fields=[], filters={})
        res = self.deserialize(res)
        self.assertIn('dhcp_hosts', res)

    def test_get_dhcp_host(self):
        subnet_id = _uuid()
        mac_address = '01:02:03:04:05:06'
        return_value = {'ip_address': '88.123.43.2',
                        'mac_address': '01:02:03:04:05:06',
                        'name': 'name',
                        'tenant_id': _uuid()}

        instance = self.plugin.return_value
        instance.get_midonet_subnet_dhcp_host.return_value = return_value

        path = 'midonet_subnets/%s/dhcp_hosts' % subnet_id,
        res = self.api.get(_get_path(path, id=mac_address, fmt=self.fmt))

        self.assertEqual(exc.HTTPOk.code, res.status_int)
        instance.get_midonet_subnet_dhcp_host.assert_called_once_with(
            mock.ANY, mac_address, midonet_subnet_id=subnet_id, fields=[])
        res = self.deserialize(res)
        self.assertIn('dhcp_host', res)

    def test_delete_dhcp_host(self):
        mac_address = '01:02:03:04:05:06'
        subnet_id = _uuid()

        instance = self.plugin.return_value

        path = 'midonet_subnets/%s/dhcp_hosts' % subnet_id,
        res = self.api.delete(_get_path(path, id=mac_address, fmt=self.fmt))

        instance.delete_midonet_subnet_dhcp_host.assert_called_once_with(
            mock.ANY, mac_address, midonet_subnet_id=subnet_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)

    def test_update_dhcp_host(self):
        mac_address = '01:02:03:04:05:06'
        subnet_id = _uuid()
        return_value = {'ip_address': '88.123.43.2',
                        'mac_address': '01:02:03:04:05:06',
                        'name': 'name',
                        'tenant_id': _uuid()}
        update_data = {'dhcp_host': {'ip_address': '88.123.43.2'}}

        instance = self.plugin.return_value
        instance.update_midonet_subnet_dhcp_host.return_value = return_value

        path = 'midonet_subnets/%s/dhcp_hosts' % subnet_id,
        res = self.api.put(_get_path(path, id=mac_address, fmt=self.fmt),
                           self.serialize(update_data))

        call = instance.update_midonet_subnet_dhcp_host
        call.assert_called_once_with(mock.ANY, mac_address,
                                     midonet_subnet_id=subnet_id,
                                     dhcp_host=update_data)

        self.assertEqual(exc.HTTPOk.code, res.status_int)
