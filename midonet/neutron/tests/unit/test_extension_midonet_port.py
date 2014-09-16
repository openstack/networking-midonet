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

from midonet.neutron.extensions import midonet_port

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path

class PortExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    fmt = "json"

    def setUp(self):
        super(PortExtensionTestCase, self).setUp()
        plural_mappings = {'midonet_port': 'midonet_ports'}
        self._setUpExtension(
            'midonet.neutron.extensions.midonet_port.PortPluginBase',
            midonet_port.PORT, midonet_port.RESOURCE_ATTRIBUTE_MAP,
            midonet_port.Midonet_port, '', plural_mappings=plural_mappings)

    def test_port_list(self):
        return_value = [{'device_id': _uuid(),
                         'host_id': _uuid(),
                         'id': _uuid(),
                         'inbound_filter_id': _uuid(),
                         'outbound_filter_id': _uuid(),
                         'interface_name': 'random_name',
                         'port_address': "10.0.0.10",
                         'network_cidr': "10.0.0.0/24"}]

        instance = self.plugin.return_value
        instance.get_midonet_ports.return_value = return_value

        res = self.api.get(_get_path('midonet_ports', fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_midonet_ports.assert_called_once_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('midonet_ports', res)
        self.assertEqual(1, len(res['midonet_ports']))

    def test_port_show(self):
        port_id = _uuid()
        return_value = {'device_id': _uuid(),
                        'host_id': _uuid(),
                        'id': port_id,
                        'inbound_filter_id': _uuid(),
                        'outbound_filter_id': _uuid(),
                        'interface_name': 'random_name',
                        'port_address': "10.0.0.10",
                        'network_cidr': "10.0.0.0/24"}

        instance = self.plugin.return_value
        instance.get_midonet_port.return_value = return_value

        res = self.api.get(_get_path('midonet_ports/%s' % port_id, fmt=self.fmt))
        self.assertEqual(exc.HTTPOk.code, res.status_int)

        instance.get_midonet_port.assert_called_once_with(
            mock.ANY, unicode(port_id), fields=mock.ANY)

        res = self.deserialize(res)
        self.assertIn('midonet_port', res)

    def test_port_update(self):
        port_id = _uuid()
        return_value = {'device_id': _uuid(),
                        'host_id': _uuid(),
                        'id': port_id,
                        'inbound_filter_id': _uuid(),
                        'outbound_filter_id': _uuid(),
                        'interface_name': 'random_name',
                        'port_address': "10.0.0.10",
                        'network_cidr': "10.0.0.0/24"}

        update_data = {'midonet_port': {'inbound_filter_id': _uuid()}}

        instance = self.plugin.return_value
        instance.update_midonet_port.return_value = return_value

        res = self.api.put(_get_path('midonet_ports', id=port_id, fmt=self.fmt),
                           self.serialize(update_data))

        instance.update_midonet_port.assert_called_once_with(
            mock.ANY, port_id, midonet_port=update_data)
        self.assertEqual(exc.HTTPOk.code, res.status_int)

    def test_port_delete(self):
        port_id = _uuid()

        instance = self.plugin.return_value

        res = self.api.delete(_get_path('midonet_ports', id=port_id))

        instance.delete_midonet_port.assert_called_once_with(mock.ANY, port_id)
        self.assertEqual(exc.HTTPNoContent.code, res.status_int)


class PortExtensionTestCaseXml(PortExtensionTestCase):

    fmt = "xml"
