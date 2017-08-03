# Copyright (C) 2015 Midokura SARL.
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

import contextlib

from oslo_utils import uuidutils
import webob.exc

from neutron.tests.unit.api import test_extensions as test_ex
from neutron.tests.unit.extensions import test_l3

from midonet.neutron import extensions as midoextensions
from midonet.neutron.extensions import gateway_device
from midonet.neutron.tests.unit import test_midonet_plugin_ml2 as test_mn_ml2

FAKE_MANAGEMENT_IP = '10.0.0.3'
FAKE_MANAGEMENT_PORT = 5672
TYPE_HW_VTEP = 'hw_vtep'
TYPE_ROUTER_VTEP = 'router_vtep'
TYPE_NETWORK_VLAN = 'network_vlan'
OVSDB = 'ovsdb'
FAKE_MAC_ADDRESS = 'aa:aa:aa:aa:aa:aa'
FAKE_MAC_ADDRESS2 = 'bb:bb:bb:bb:bb:bb'
FAKE_VTEP_ADDRESS = '10.1.0.3'
FAKE_VTEP_ADDRESS2 = '10.1.0.4'
FAKE_SEG_ID = 1000
FAKE_TUNNEL_IP = '10.2.0.3'
FAKE_TUNNEL_IP2 = '10.2.0.4'
FAKE_TENANT_ID = uuidutils.generate_uuid()

DB_GATEWAY_DEVICE_PLUGIN_KLASS = 'midonet_gwdevice'
extensions_path = ':'.join(midoextensions.__path__)


class GatewayDeviceTestExtensionManager(test_l3.L3TestExtensionManager):

    def get_resources(self):
        res = super(GatewayDeviceTestExtensionManager, self).get_resources()
        return res + gateway_device.Gateway_device.get_resources()

    def get_actions(self):
        return []

    def get_request_extensions(self):
        return []


class GatewayDeviceTestCaseMixin(object):

    @contextlib.contextmanager
    def gateway_device_type_hw_vtep(self, name=TYPE_HW_VTEP,
                                    type=TYPE_HW_VTEP,
                                    management_ip=FAKE_MANAGEMENT_IP,
                                    management_port=FAKE_MANAGEMENT_PORT,
                                    management_protocol=OVSDB,
                                    tunnel_ips=None):
        if tunnel_ips is None:
            tunnel_ips = [FAKE_TUNNEL_IP]
        gw_dev = self._make_gateway_device_hw_vtep(name, type, management_ip,
                                                   management_port,
                                                   management_protocol,
                                                   tunnel_ips)
        yield gw_dev

    @contextlib.contextmanager
    def gateway_device_type_router_vtep(self, name=TYPE_ROUTER_VTEP,
                                        type=TYPE_ROUTER_VTEP,
                                        resource_id="", tunnel_ips=None):
        if tunnel_ips is None:
            tunnel_ips = [FAKE_TUNNEL_IP]
        gw_dev = self._make_gateway_device_router_vtep(name, type,
                                                       resource_id,
                                                       tunnel_ips)
        yield gw_dev

    @contextlib.contextmanager
    def gateway_device_type_network_vlan(self, name=TYPE_NETWORK_VLAN,
                                         type=TYPE_NETWORK_VLAN,
                                         resource_id=""):
        gw_dev = self._make_gateway_device_network_vlan(name, type,
                                                        resource_id)
        yield gw_dev

    def _make_gateway_device_hw_vtep(self, name, type, management_ip,
                                     management_port,
                                     management_protocol, tunnel_ips):
        res = self._create_gateway_device_hw_vtep(name, type, management_ip,
                                                  management_port,
                                                  management_protocol,
                                                  tunnel_ips)
        if res.status_int >= webob.exc.HTTPBadRequest.code:
            raise webob.exc.HTTPClientError(code=res.status_int)
        return self.deserialize(self.fmt, res)

    def _make_gateway_device_router_vtep(self, name, type,
                                         resource_id, tunnel_ips):
        res = self._create_gateway_device_router_vtep(name, type,
                                                      resource_id,
                                                      tunnel_ips)
        if res.status_int >= webob.exc.HTTPBadRequest.code:
            raise webob.exc.HTTPClientError(code=res.status_int)
        return self.deserialize(self.fmt, res)

    def _make_gateway_device_network_vlan(self, name, type,
                                          resource_id):
        res = self._create_gateway_device_network_vlan(name, type,
                                                       resource_id)
        if res.status_int >= webob.exc.HTTPBadRequest.code:
            raise webob.exc.HTTPClientError(code=res.status_int)
        return self.deserialize(self.fmt, res)

    def _create_gateway_device_router_vtep(self, name=TYPE_ROUTER_VTEP,
                                           type=TYPE_ROUTER_VTEP,
                                           resource_id="",
                                           tunnel_ips=None):
        data = {'gateway_device': {'name': name,
                                   'tenant_id': FAKE_TENANT_ID,
                                   'type': type,
                                   'resource_id': resource_id,
                                   'tunnel_ips': tunnel_ips or None}}
        gw_dev_req = self.new_create_request('gw/gateway_devices',
                                             data, self.fmt)
        return gw_dev_req.get_response(self.ext_api)

    def _create_gateway_device_hw_vtep(self, name=TYPE_HW_VTEP,
                                       type=TYPE_HW_VTEP,
                                       management_ip=None,
                                       management_port=None,
                                       management_protocol=None,
                                       tunnel_ips=None):
        data = {'gateway_device': {'name': name,
                                   'tenant_id': FAKE_TENANT_ID,
                                   'type': type,
                                   'management_ip': management_ip,
                                   'management_port': management_port,
                                   'management_protocol': management_protocol,
                                   'tunnel_ips': tunnel_ips or []}}
        gw_dev_req = self.new_create_request('gw/gateway_devices',
                                             data, self.fmt)
        return gw_dev_req.get_response(self.ext_api)

    def _create_gateway_device_network_vlan(self, name=TYPE_NETWORK_VLAN,
                                            type=TYPE_NETWORK_VLAN,
                                            resource_id=""):
        data = {'gateway_device': {'name': name,
                                   'tenant_id': FAKE_TENANT_ID,
                                   'type': type,
                                   'resource_id': resource_id}}
        gw_dev_req = self.new_create_request('gw/gateway_devices',
                                             data, self.fmt)
        return gw_dev_req.get_response(self.ext_api)


class GatewayDeviceTestCase(test_l3.L3NatTestCaseMixin,
                            GatewayDeviceTestCaseMixin):

    def setUp(self, plugin=None, service_plugins=None, ext_mgr=None):

        service_plugins = {
            'gateway_device_plugin_name': DB_GATEWAY_DEVICE_PLUGIN_KLASS}

        gw_dev_mgr = GatewayDeviceTestExtensionManager()
        super(GatewayDeviceTestCase, self).setUp(
            service_plugins=service_plugins, ext_mgr=gw_dev_mgr)
        self.ext_api = test_ex.setup_extensions_middleware(gw_dev_mgr)

        network = self._make_network(self.fmt, 'net1', True)
        self._subnet = self._make_subnet(self.fmt, network, "10.0.0.1",
                                         '10.0.0.0/24')
        self._subnet_id = self._subnet['subnet']['id']
        router1 = self._make_router(self.fmt, uuidutils.generate_uuid(),
                                    'router1', True)
        self._router_id = router1['router']['id']

        router2 = self._make_router(self.fmt, uuidutils.generate_uuid(),
                                    'router2', True)
        self._router_id_in_use = router2['router']['id']
        self._router_interface_action('add', self._router_id_in_use,
                                      self._subnet_id, None)

        # for network_vlan gateway device setting
        res = self._create_network(self.fmt, 'gateway_network_vlan',
                                   True)
        self._network_id = self.deserialize(self.fmt, res)['network']['id']

    def _create_remote_mac_entry(self, gw_dev_id,
                                 mac_address=FAKE_MAC_ADDRESS,
                                 vtep_address=FAKE_VTEP_ADDRESS,
                                 segmentation_id=FAKE_SEG_ID):
        data = {'remote_mac_entry': {'mac_address': mac_address,
                                     'vtep_address': vtep_address,
                                     'segmentation_id': segmentation_id,
                                     'tenant_id': FAKE_TENANT_ID}}
        gw_dev_mac_req = self.new_create_request('gw/gateway_devices/'
                                                 + gw_dev_id
                                                 + '/remote_mac_entries',
                                                 data,
                                                 self.fmt)

        return gw_dev_mac_req.get_response(self.ext_api)

    def test_create_remote_mac(self):
        expected = {'mac_address': FAKE_MAC_ADDRESS,
                    'vtep_address': FAKE_VTEP_ADDRESS,
                    'segmentation_id': FAKE_SEG_ID}
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.remote_mac_entry(gw_dev['gateway_device']['id']) as rme:
                self.assertDictSupersetOf(expected, rme['remote_mac_entry'])

    def test_create_remote_mac_on_network_vlan(self):
        with self.gateway_device_type_network_vlan(
                resource_id=self._network_id) as gw_dev:
            res = self._create_remote_mac_entry(gw_dev['gateway_device']['id'])
            self.deserialize(self.fmt, res)
            self.assertEqual(webob.exc.HTTPConflict.code, res.status_int)

    def test_create_remote_mac_with_same_vtep_address(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.remote_mac_entry(gw_dev['gateway_device']['id']):
                with self.remote_mac_entry(gw_dev['gateway_device']['id'],
                                           mac_address=FAKE_MAC_ADDRESS2):
                    req = self.new_list_request(
                        'gw/gateway_devices/'
                        + gw_dev['gateway_device']['id']
                        + '/remote_mac_entries')
                    res = self.deserialize(
                        self.fmt, req.get_response(self.ext_api))
                    self.assertEqual(len(res['remote_mac_entries']), 2)

    def test_create_remote_mac_with_duplicate_mac_address(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.remote_mac_entry(gw_dev['gateway_device']['id']):
                res = self._create_remote_mac_entry(
                    gw_dev['gateway_device']['id'],
                    vtep_address=FAKE_VTEP_ADDRESS2)
                self.deserialize(self.fmt, res)
                self.assertEqual(webob.exc.HTTPConflict.code, res.status_int)

    def test_show_remote_mac(self):
        expected = {'mac_address': FAKE_MAC_ADDRESS,
                    'vtep_address': FAKE_VTEP_ADDRESS,
                    'segmentation_id': FAKE_SEG_ID}
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.remote_mac_entry(gw_dev['gateway_device']['id']) as rme:
                req = self.new_show_request('gw/gateway_devices/'
                                            + gw_dev['gateway_device']['id']
                                            + '/remote_mac_entries',
                                            rme['remote_mac_entry']['id'])
                res = self.deserialize(self.fmt,
                                       req.get_response(self.ext_api))
                self.assertDictSupersetOf(expected, res['remote_mac_entry'])

    def test_list_remote_mac(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.remote_mac_entry(gw_dev['gateway_device']['id']):
                req = self.new_list_request('gw/gateway_devices/'
                                            + gw_dev['gateway_device']['id']
                                            + '/remote_mac_entries')
                res = self.deserialize(
                    self.fmt, req.get_response(self.ext_api))
                self.assertEqual(1, len(res['remote_mac_entries']))

    def test_list_remote_mac_with_two_gateways(self):
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id) as gw_dev, \
                self.gateway_device_type_router_vtep(
                    resource_id=self._router_id_in_use,
                    tunnel_ips=[FAKE_TUNNEL_IP2]) as gw_dev2:
            with self.remote_mac_entry(gw_dev['gateway_device']['id']) as rme:
                req = self.new_list_request('gw/gateway_devices/'
                                            + gw_dev['gateway_device']['id']
                                            + '/remote_mac_entries')
                res = self.deserialize(
                    self.fmt, req.get_response(self.ext_api))
                self.assertEqual(1, len(res['remote_mac_entries']))
                self.assertEqual(rme['remote_mac_entry']['id'],
                                 res['remote_mac_entries'][0]['id'])
                req = self.new_list_request('gw/gateway_devices/'
                                            + gw_dev2['gateway_device']['id']
                                            + '/remote_mac_entries')
                res = self.deserialize(
                    self.fmt, req.get_response(self.ext_api))
                self.assertEqual([], res['remote_mac_entries'])

    def test_delete_remote_mac(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.remote_mac_entry(gw_dev['gateway_device']['id']) as rme:
                req = self.new_delete_request('gw/gateway_devices/'
                                              + gw_dev['gateway_device']['id']
                                              + '/remote_mac_entries',
                                              rme['remote_mac_entry']['id'])
                res = req.get_response(self.ext_api)
                self.assertEqual(webob.exc.HTTPNoContent.code, res.status_int)

    def test_delete_remote_mac_with_wrong_gateway(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev, \
                self.gateway_device_type_router_vtep(
                    resource_id=self._router_id_in_use,
                    tunnel_ips=[FAKE_TUNNEL_IP2]) as gw_dev2:
            with self.remote_mac_entry(gw_dev['gateway_device']['id']) as rme:
                req = self.new_delete_request('gw/gateway_devices/'
                                              + gw_dev2['gateway_device']['id']
                                              + '/remote_mac_entries',
                                              rme['remote_mac_entry']['id'])
                res = req.get_response(self.ext_api)
                self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_delete_gateway_device_with_remote_mac(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.remote_mac_entry(gw_dev['gateway_device']['id']):
                req = self.new_delete_request('gw/gateway_devices',
                                              gw_dev['gateway_device']['id'])
                res = req.get_response(self.ext_api)
                self.assertEqual(webob.exc.HTTPNoContent.code, res.status_int)

    def test_create_gateway_device_with_tunnel_ips(self):
        expected = {'name': TYPE_ROUTER_VTEP,
                    'type': TYPE_ROUTER_VTEP,
                    'resource_id': self._router_id,
                    'tunnel_ips': [FAKE_TUNNEL_IP],
                    'tenant_id': FAKE_TENANT_ID}
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id,
                tunnel_ips=[FAKE_TUNNEL_IP]) as gw_dev:
            self.assertDictSupersetOf(expected, gw_dev['gateway_device'])

    def test_create_gateway_device_error_delete_neutron_resource(self):
        self.client_mock.create_gateway_device_postcommit.side_effect = (
            Exception("Fake Error"))
        self._create_gateway_device_router_vtep()
        req = self.new_list_request('gw/gateway_devices')
        res = self.deserialize(self.fmt, req.get_response(self.ext_api))
        self.assertFalse(res['gateway_devices'])

    def test_create_gateway_device_error_delete_neutron_network(self):
        self.client_mock.create_gateway_device_postcommit.side_effect = (
            Exception("Fake Error"))
        self._create_gateway_device_network_vlan()
        req = self.new_list_request('gw/gateway_devices')
        res = self.deserialize(self.fmt, req.get_response(self.ext_api))
        self.assertFalse(res['gateway_devices'])

    def test_update_gateway_device_error_rollback_neutron_resource(self):
        self.client_mock.update_gateway_device_postcommit.side_effect = (
            Exception("Fake Error"))
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id,
                tunnel_ips=[FAKE_TUNNEL_IP]) as gw_dev:
            data = {'gateway_device': {'tunnel_ips': [FAKE_TUNNEL_IP2]}}
            req = self.new_update_request('gw/gateway_devices',
                                          data,
                                          gw_dev['gateway_device']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPInternalServerError.code,
                             res.status_int)
            # ensure TunnelIPs are not changed.
            expected = {'tunnel_ips': [FAKE_TUNNEL_IP]}
            req = self.new_show_request('gw/gateway_devices',
                                        gw_dev['gateway_device']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertDictSupersetOf(expected, res['gateway_device'])

    def test_create_remote_mac_entry_error_delete_neutron_resource(self):
        (self.client_mock.create_gateway_device_remote_mac_entry_postcommit.
         side_effect) = Exception("Fake Error")
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            try:
                with self.remote_mac_entry(gw_dev['gateway_device']['id']):
                    self.assertTrue(False)
            except webob.exc.HTTPClientError:
                pass
            req = self.new_list_request('gw/gateway_devices/'
                                        + gw_dev['gateway_device']['id']
                                        + '/remote_mac_entries')
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertFalse(res['remote_mac_entries'])

    def test_delete_gateway_device_error_delete_neutron_resource(self):
        self.client_mock.delete_gateway_device_postcommit.side_effect = (
            Exception("Fake Error"))
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            req = self.new_delete_request('gw/gateway_devices',
                                          gw_dev['gateway_device']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPInternalServerError.code,
                             res.status_int)
            # check the resource deleted in Neutron DB
            req = self.new_list_request('gw/gateway_devices')
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertFalse(res['gateway_devices'])

    def test_delete_remote_mac_entry_error_delete_neutron_resource(self):
        (self.client_mock.delete_gateway_device_remote_mac_entry_postcommit.
         side_effect) = Exception("Fake Error")
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.remote_mac_entry(gw_dev['gateway_device']['id']) as rme:
                req = self.new_delete_request('gw/gateway_devices/'
                                              + gw_dev['gateway_device']['id']
                                              + '/remote_mac_entries',
                                              rme['remote_mac_entry']['id'])
                res = req.get_response(self.ext_api)
                self.assertEqual(webob.exc.HTTPInternalServerError.code,
                                 res.status_int)
                # check the resource deleted in Neutron DB
                req = self.new_list_request('gw/gateway_devices')
                res = self.deserialize(self.fmt,
                                       req.get_response(self.ext_api))
                self.assertEqual(
                    [],
                    res['gateway_devices'][0]['remote_mac_entries'])

    def _make_remote_mac_entry(self, gw_dev_id, mac_address=FAKE_MAC_ADDRESS,
                               vtep_address=FAKE_VTEP_ADDRESS,
                               segmentation_id=FAKE_SEG_ID):
        res = self._create_remote_mac_entry(gw_dev_id, mac_address,
                                            vtep_address,
                                            segmentation_id)
        if res.status_int >= webob.exc.HTTPBadRequest.code:
            raise webob.exc.HTTPClientError(code=res.status_int)
        return self.deserialize(self.fmt, res)

    @contextlib.contextmanager
    def remote_mac_entry(self, gw_dev_id, mac_address=FAKE_MAC_ADDRESS,
                         vtep_address=FAKE_VTEP_ADDRESS,
                         segmentation_id=FAKE_SEG_ID):
        rme = self._make_remote_mac_entry(gw_dev_id, mac_address, vtep_address,
                                          segmentation_id)
        yield rme

    def test_create_gateway_device_hw_vtep(self):
        expected = {'name': TYPE_HW_VTEP,
                    'type': TYPE_HW_VTEP,
                    'management_ip': FAKE_MANAGEMENT_IP,
                    'management_port': FAKE_MANAGEMENT_PORT,
                    'management_protocol': OVSDB,
                    'tenant_id': FAKE_TENANT_ID}
        with self.gateway_device_type_hw_vtep() as gw_dev:
            self.assertDictSupersetOf(expected, gw_dev['gateway_device'])

    def test_create_gateway_device_router_vtep(self):
        expected = {'name': TYPE_ROUTER_VTEP,
                    'type': TYPE_ROUTER_VTEP,
                    'resource_id': self._router_id,
                    'tenant_id': FAKE_TENANT_ID}
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            self.assertDictSupersetOf(expected, gw_dev['gateway_device'])

    def test_create_gateway_device_network_vlan(self):
        expected = {'name': TYPE_NETWORK_VLAN,
                    'type': TYPE_NETWORK_VLAN,
                    'resource_id': self._network_id,
                    'tenant_id': FAKE_TENANT_ID}
        with self.gateway_device_type_network_vlan(
                resource_id=self._network_id) as gw_dev:
            self.assertDictSupersetOf(expected, gw_dev['gateway_device'])

    def test_create_gateway_device_router_vtep_not_found(self):
        res = self._create_gateway_device_router_vtep(resource_id='a')
        self.deserialize(self.fmt, res)
        self.assertEqual(webob.exc.HTTPNotFound.code, res.status_int)

    def test_create_gateway_device_network_vlan_not_found(self):
        res = self._create_gateway_device_network_vlan(resource_id='a')
        self.deserialize(self.fmt, res)
        self.assertEqual(webob.exc.HTTPNotFound.code, res.status_int)

    def test_create_gateway_device_with_multiple_tunnel_ips(self):
        res = self._create_gateway_device_router_vtep(
            resource_id=self._router_id,
            tunnel_ips=[FAKE_TUNNEL_IP, FAKE_TUNNEL_IP2])
        self.deserialize(self.fmt, res)
        self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_create_gateway_device_without_tunnel_ips(self):
        res = self._create_gateway_device_router_vtep(
            resource_id=self._router_id,
            tunnel_ips=[])
        self.deserialize(self.fmt, res)
        self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_update_gateway_device_with_multiple_tunnel_ips(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            data = {
                'gateway_device': {
                    'tunnel_ips': [
                        FAKE_TUNNEL_IP,
                        FAKE_TUNNEL_IP2
                    ]
                }
            }
            gw_dev_req = self.new_update_request(
                'gw/gateway_devices',
                data,
                gw_dev['gateway_device']['id'])
            res = gw_dev_req.get_response(self.ext_api)
            self.deserialize(self.fmt, res)
            self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_update_gateway_device_without_tunnel_ips(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            data = {'gateway_device': {'tunnel_ips': []}}
            gw_dev_req = self.new_update_request(
                'gw/gateway_devices',
                data,
                gw_dev['gateway_device']['id'])
            res = gw_dev_req.get_response(self.ext_api)
            self.deserialize(self.fmt, res)
            self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_create_gateway_device_router_with_duplicate_router(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            res = self._create_gateway_device_router_vtep(
                resource_id=gw_dev['gateway_device']['resource_id'])
            self.deserialize(self.fmt, res)
            self.assertEqual(webob.exc.HTTPConflict.code, res.status_int)

    def test_create_gateway_device_network_with_duplicate_network(self):
        with self.gateway_device_type_network_vlan(
                resource_id=self._network_id) as gw_dev:
            res = self._create_gateway_device_network_vlan(
                resource_id=gw_dev['gateway_device']['resource_id'])
            self.deserialize(self.fmt, res)
            self.assertEqual(webob.exc.HTTPConflict.code, res.status_int)

    def test_create_gateway_device_hw_vtep_without_management_ip(self):
        res = self._create_gateway_device_hw_vtep(
            management_port=FAKE_MANAGEMENT_PORT,
            management_protocol=OVSDB,
            tunnel_ips=[FAKE_TUNNEL_IP])
        self.deserialize(self.fmt, res)
        self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_create_gateway_device_hw_vtep_without_management_port(self):
        res = self._create_gateway_device_hw_vtep(
            management_ip=FAKE_MANAGEMENT_IP,
            management_protocol=OVSDB,
            tunnel_ips=[FAKE_TUNNEL_IP])
        self.deserialize(self.fmt, res)
        self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_create_gateway_device_hw_vtep_without_management_protocol(self):
        res = self._create_gateway_device_hw_vtep(
            management_ip=FAKE_MANAGEMENT_IP,
            management_port=FAKE_MANAGEMENT_PORT,
            tunnel_ips=[FAKE_TUNNEL_IP])
        self.deserialize(self.fmt, res)
        self.assertEqual(webob.exc.HTTPCreated.code, res.status_int)

    def test_create_gateway_device_hw_vtep_without_tunnel_ips(self):
        res = self._create_gateway_device_hw_vtep(
            management_ip=FAKE_MANAGEMENT_IP,
            management_port=FAKE_MANAGEMENT_PORT,
            management_protocol=OVSDB)
        self.deserialize(self.fmt, res)
        self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_create_gateway_device_hw_vtep_with_string_management_port(self):
        res = self._create_gateway_device_hw_vtep(
            management_ip=FAKE_MANAGEMENT_IP,
            management_port=str(FAKE_MANAGEMENT_PORT),
            management_protocol=OVSDB,
            tunnel_ips=[FAKE_TUNNEL_IP])
        self.deserialize(self.fmt, res)
        self.assertEqual(webob.exc.HTTPCreated.code, res.status_int)

    def test_create_gateway_device_router_vtep_without_resource_id(self):
        res = self._create_gateway_device_router_vtep()
        self.deserialize(self.fmt, res)
        self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_create_gateway_device_vlan_network_without_resource_id(self):
        res = self._create_gateway_device_network_vlan()
        self.deserialize(self.fmt, res)
        self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_delete_gateway_device(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            req = self.new_delete_request('gw/gateway_devices',
                                          gw_dev['gateway_device']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPNoContent.code, res.status_int)

    def test_delete_router_in_use(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id):
            req = self.new_delete_request('routers',
                                          self._router_id)
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPConflict.code, res.status_int)

    def test_delete_network_in_use(self):
        with self.gateway_device_type_network_vlan(
                resource_id=self._network_id):
            req = self.new_delete_request('networks',
                                          self._network_id)
            res = req.get_response(self.api)
            self.assertEqual(webob.exc.HTTPConflict.code, res.status_int)
            req = self.new_show_request('networks', self._network_id)
            res = req.get_response(self.api)
            self.assertEqual(webob.exc.HTTPOk.code, res.status_int)

    def test_update_gateway_device(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            data = {'gateway_device': {'name': 'new_name'}}
            req = self.new_update_request('gw/gateway_devices',
                                          data,
                                          gw_dev['gateway_device']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertEqual(data['gateway_device']['name'],
                             res['gateway_device']['name'])

    def test_update_gateway_device_tunnel_ips(self):
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id,
                tunnel_ips=[FAKE_TUNNEL_IP]) as gw_dev:
            data = {'gateway_device': {'tunnel_ips': [FAKE_TUNNEL_IP2]}}
            req = self.new_update_request('gw/gateway_devices',
                                          data,
                                          gw_dev['gateway_device']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertEqual(data['gateway_device']['tunnel_ips'],
                             res['gateway_device']['tunnel_ips'])

    def test_show_gateway_device_hw_vtep(self):
        expected = {'name': TYPE_HW_VTEP,
                    'type': TYPE_HW_VTEP,
                    'management_ip': FAKE_MANAGEMENT_IP,
                    'management_port': FAKE_MANAGEMENT_PORT,
                    'management_protocol': OVSDB,
                    'tenant_id': FAKE_TENANT_ID}
        with self.gateway_device_type_hw_vtep() as gw_dev:
            req = self.new_show_request('gw/gateway_devices',
                                        gw_dev['gateway_device']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertDictSupersetOf(expected, res['gateway_device'])

    def test_show_gateway_device_router_vtep(self):
        expected = {'name': TYPE_ROUTER_VTEP,
                    'type': TYPE_ROUTER_VTEP,
                    'resource_id': self._router_id,
                    'tenant_id': FAKE_TENANT_ID}
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            req = self.new_show_request('gw/gateway_devices',
                                        gw_dev['gateway_device']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertDictSupersetOf(expected, res['gateway_device'])

    def test_show_gateway_device_network_vlan(self):
        expected = {'name': TYPE_NETWORK_VLAN,
                    'type': TYPE_NETWORK_VLAN,
                    'resource_id': self._network_id,
                    'tenant_id': FAKE_TENANT_ID}
        with self.gateway_device_type_network_vlan(
                resource_id=self._network_id) as gw_dev:
            req = self.new_show_request('gw/gateway_devices',
                                        gw_dev['gateway_device']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertDictSupersetOf(expected, res['gateway_device'])

    def test_list_gateway_devices(self):
        with self.gateway_device_type_router_vtep(resource_id=self._router_id):
            with self.gateway_device_type_hw_vtep(
                    tunnel_ips=[FAKE_TUNNEL_IP2]):
                req = self.new_list_request('gw/gateway_devices')
                res = self.deserialize(
                    self.fmt, req.get_response(self.ext_api))
                self.assertEqual(2, len(res['gateway_devices']))


class GatewayDeviceTestCaseWithML2(GatewayDeviceTestCase,
                                   test_mn_ml2.MidonetPluginML2TestCase):
    pass
