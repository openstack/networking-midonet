# Copyright 2014 Midokura SARL
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
# @author Jaume Devesa

import copy
import os

import mock
from neutron.db import db_base_plugin_v2 as base_db
from neutron import manager
from neutron.openstack.common import importutils
from neutron.openstack.common import uuidutils
from neutron.tests.unit import test_api_v2
from neutron.tests.unit import test_api_v2_extension
from neutron.tests.unit import test_db_plugin
from oslo.config import cfg
from webob import exc

from midonet.neutron.extensions import midonet_subnet

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path

MIDOKURA_EXT_PATH = "midonet.neutron.extensions"


class DhcpHostsExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    """Test the endpoints for the host."""
    fmt = "json"

    def setUp(self):
        super(DhcpHostsExtensionTestCase, self).setUp()
        plural_mappings = {'dhcp_host': 'dhcp_hosts'}
        self._setUpExtension(
            'midonet.neutron.extensions.midonet_subnet.DhcpHostsPluginBase',
            midonet_subnet.DHCP, midonet_subnet.RESOURCE_ATTRIBUTE_MAP,
            midonet_subnet.Midonet_subnet, '', plural_mappings=plural_mappings)

    def test_create_dhcp_host(self):

        subnet_id = _uuid()
        data = {'dhcp_host': {'ip_address': '88.123.43.2',
                              'mac_address': '01:02:03:04:05:06',
                              'name': 'name',
                              'tenant_id': _uuid()}}
        return_value = copy.deepcopy(data['dhcp_host'])
        return_value.update({'id': _uuid()})
        instance = self.plugin.return_value
        instance.create_subnet_dhcp_host.return_value = return_value

        res = self.api.post(_get_path('subnets/%s/dhcp_hosts' % subnet_id,
                                      fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)

        instance.create_subnet_dhcp_host.assert_called_once_with(
            mock.ANY, subnet_id=subnet_id, dhcp_host=data)
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
        instance.get_subnet_dhcp_hosts.return_value = return_value

        res = self.api.get(_get_path('subnets/%s/dhcp_hosts' % subnet_id,
                                     fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        instance.get_subnet_dhcp_hosts.assert_called_once_with(
            mock.ANY, subnet_id=subnet_id, fields=[], filters={})
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
        instance.get_subnet_dhcp_host.return_value = return_value

        res = self.api.get(_get_path('subnets/%s/dhcp_hosts' % subnet_id,
                                     id=mac_address,
                                     fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        instance.get_subnet_dhcp_host.assert_called_once_with(
            mock.ANY, mac_address, subnet_id=subnet_id, fields=[])
        res = self.deserialize(res)
        self.assertIn('dhcp_host', res)

    def test_delete_dhcp_host(self):
        mac_address = '01:02:03:04:05:06'
        subnet_id = _uuid()

        instance = self.plugin.return_value

        res = self.api.delete(_get_path('subnets/%s/dhcp_hosts' % subnet_id,
                                        id=mac_address,
                                        fmt=self.fmt))
        instance.delete_subnet_dhcp_host.assert_called_once_with(
            mock.ANY, mac_address, subnet_id=subnet_id)
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
        instance.update_subnet_dhcp_host.return_value = return_value

        res = self.api.put(_get_path('subnets/%s/dhcp_hosts' % subnet_id,
                                     id=mac_address,
                                     fmt=self.fmt),
                           self.serialize(update_data))

        instance.update_subnet_dhcp_host.assert_called_once_with(
            mock.ANY, mac_address, subnet_id=subnet_id, dhcp_host=update_data)
        self.assertEqual(exc.HTTPOk.code, res.status_int)


class MidonetSubnetTestPlugin(base_db.NeutronDbPluginV2):

        supported_extension_aliases = ['midonet-subnet']


class MidonetSubnetExtTestCase(test_db_plugin.NeutronDbPluginV2TestCase):

    fmt = 'json'

    def setUp(self):
        extensions_path = importutils.import_module(
            MIDOKURA_EXT_PATH).__file__
        cfg.CONF.set_override('api_extensions_path',
                              os.path.dirname(extensions_path))
        plugin_name = (__name__ + '.MidonetSubnetTestPlugin')
        super(MidonetSubnetExtTestCase, self).setUp(
            plugin=plugin_name)

    def test_dhcp_server_is_ip(self):
        """Test if new attributes for subnet are exposed.

        Best way to test this without being intrusive is to perform calls
        over the subnets resource that must to fail because new attributes'
        validators not because attribute is not exposed.
        """
        data = {'subnet': {'network_id': _uuid(),
                           'cidr': '88.123.43.0/24',
                           'ip_version': 4,
                           'midonet:dhcp_server_ip': 'foo',
                           'tenant_id': _uuid()}}
        req = self.new_create_request('subnets', data, fmt=self.fmt)
        res = req.get_response(self.api)

        self.assertEqual(exc.HTTPBadRequest.code, res.status_int)
        body = self.deserialize(self.fmt, res)
        self.assertIn('NeutronError', body)
        message = body['NeutronError']['message']
        self.assertIn("'foo' is not a valid IP address", message)

    def test_create_subnet(self):

        data = {'subnet': {'network_id': _uuid(),
                           'cidr': '88.123.43.0/24',
                           'ip_version': 4,
                           'tenant_id': self._tenant_id,
                           'midonet:interface_mtu': 1400,
                           'midonet:dhcp_server_ip': '88.123.43.44'}}

        return_value = copy.deepcopy(data['subnet'])

        plugin = manager.NeutronManager.get_plugin()
        with mock.patch.object(plugin, 'create_subnet') as po:
            po.return_value = return_value

            req = self.new_create_request('subnets', data, fmt=self.fmt)
            res = req.get_response(self.api)
            self.assertEqual(exc.HTTPCreated.code, res.status_int)
