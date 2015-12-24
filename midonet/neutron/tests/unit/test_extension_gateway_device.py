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

from midonet.neutron import extensions as midoextensions
from midonet.neutron.extensions import gateway_device
from midonet.neutron.tests.unit import test_midonet_plugin_v2 as test_mn
from neutron.tests.unit.api import test_extensions as test_ex
from neutron.tests.unit.extensions import test_l3
import uuid
import webob.exc

FAKE_MANAGEMENT_IP = '10.0.0.3'
FAKE_MANAGEMENT_PORT = 5672
TYPE_HW_VTEP = 'hw_vtep'
TYPE_ROUTER_VTEP = 'router_vtep'
OVSDB = 'ovsdb'
FAKE_MAC_ADDRESS = 'aa:aa:aa:aa:aa:aa'
FAKE_MAC_ADDRESS2 = 'bb:bb:bb:bb:bb:bb'
FAKE_VTEP_ADDRESS = '10.1.0.3'
FAKE_VTEP_ADDRESS2 = '10.1.0.4'
FAKE_SEG_ID = 1000
FAKE_TUNNEL_IP = '10.2.0.3'
FAKE_TUNNEL_IP2 = '10.2.0.4'
FAKE_TENANT_ID = str(uuid.uuid4())

DB_GATEWAY_DEVICE_PLUGIN_KLASS =\
    'midonet.neutron.services.gw_device.plugin.MidonetGwDeviceServicePlugin'
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
        gw_dev = self._make_gateway_device_hw_vtep(name, type, management_ip,
                                                   management_port,
                                                   management_protocol,
                                                   tunnel_ips or [])
        yield gw_dev

    @contextlib.contextmanager
    def gateway_device_type_router_vtep(self, name=TYPE_ROUTER_VTEP,
                                        type=TYPE_ROUTER_VTEP,
                                        resource_id="", tunnel_ips=None):
        gw_dev = self._make_gateway_device_router_vtep(name, type,
                                                       resource_id,
                                                       tunnel_ips or [])
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


class GatewayDeviceTestCase(test_l3.L3NatTestCaseMixin,
                            GatewayDeviceTestCaseMixin,
                            test_mn.MidonetPluginV2TestCase):

    def setUp(self, plugin=None, service_plugins=None, ext_mgr=None):

        service_plugins = {
            'gateway_device_plugin_name': DB_GATEWAY_DEVICE_PLUGIN_KLASS}

        gw_dev_mgr = GatewayDeviceTestExtensionManager()
        super(GatewayDeviceTestCase,
            self).setUp(service_plugins=service_plugins,
                        ext_mgr=gw_dev_mgr)
        self.ext_api = test_ex.setup_extensions_middleware(gw_dev_mgr)

        network = self._make_network(self.fmt, 'net1', True)
        self._subnet = self._make_subnet(self.fmt, network, "10.0.0.1",
                                   '10.0.0.0/24')
        self._subnet_id = self._subnet['subnet']['id']
        router1 = self._make_router(self.fmt, str(uuid.uuid4()),
                                    'router1', True)
        self._router_id = router1['router']['id']

        router2 = self._make_router(self.fmt, str(uuid.uuid4()),
                                    'router2', True)
        self._router_id_in_use = router2['router']['id']
        self._router_interface_action('add', self._router_id_in_use,
                                      self._subnet_id, None)

    def _create_remote_mac_entry(self, mac_address=FAKE_MAC_ADDRESS,
                                 vtep_address=FAKE_VTEP_ADDRESS,
                                 segmentation_id=FAKE_SEG_ID, gw_dev_id=""):
        data = {'remote_mac_entry': {'mac_address': FAKE_MAC_ADDRESS,
                                     'vtep_address': FAKE_VTEP_ADDRESS,
                                     'segmentation_id': FAKE_SEG_ID,
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
            with self.remote_mac_entry(FAKE_MAC_ADDRESS, FAKE_VTEP_ADDRESS,
                                       FAKE_SEG_ID,
                                       gw_dev['gateway_device']['id']) as rme:
                for k, v in expected.items():
                    self.assertEqual(rme['remote_mac_entry'][k], v)

    def test_create_remote_mac_with_duplicate_mac_address(self):
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id) as gw_dev:
            with self.remote_mac_entry(FAKE_MAC_ADDRESS, FAKE_VTEP_ADDRESS,
                                       FAKE_SEG_ID,
                                       gw_dev['gateway_device']['id']):
                res = self._create_remote_mac_entry(
                    FAKE_MAC_ADDRESS,
                    FAKE_VTEP_ADDRESS2,
                    FAKE_SEG_ID,
                    gw_dev['gateway_device']['id'])
                self.deserialize(self.fmt, res)
                self.assertEqual(res.status_int, webob.exc.HTTPConflict.code)

    def test_create_remote_mac_with_duplicate_vtep_address(self):
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id) as gw_dev:
            with self.remote_mac_entry(FAKE_MAC_ADDRESS, FAKE_VTEP_ADDRESS,
                                       FAKE_SEG_ID,
                                       gw_dev['gateway_device']['id']):
                res = self._create_remote_mac_entry(
                    FAKE_MAC_ADDRESS2,
                    FAKE_VTEP_ADDRESS,
                    FAKE_SEG_ID,
                    gw_dev['gateway_device']['id'])
                self.deserialize(self.fmt, res)
                self.assertEqual(res.status_int, webob.exc.HTTPConflict.code)

    def test_show_remote_mac(self):
        expected = {'mac_address': FAKE_MAC_ADDRESS,
                    'vtep_address': FAKE_VTEP_ADDRESS,
                    'segmentation_id': FAKE_SEG_ID}
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id) as gw_dev:
            with self.remote_mac_entry(FAKE_MAC_ADDRESS, FAKE_VTEP_ADDRESS,
                                       FAKE_SEG_ID,
                                       gw_dev['gateway_device']['id']) as rme:
                req = self.new_show_request('gw/gateway_devices/'
                                            + gw_dev['gateway_device']['id']
                                            + '/remote_mac_entries',
                                            rme['remote_mac_entry']['id'])
                res = self.deserialize(self.fmt,
                                       req.get_response(self.ext_api))
                for k, v in expected.items():
                    self.assertEqual(res['remote_mac_entry'][k], v)

    def test_list_remote_mac(self):
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id) as gw_dev:
            with self.remote_mac_entry(FAKE_MAC_ADDRESS, FAKE_VTEP_ADDRESS,
                                       FAKE_SEG_ID,
                                       gw_dev['gateway_device']['id']):
                req = self.new_list_request('gw/gateway_devices/'
                                            + gw_dev['gateway_device']['id']
                                            + '/remote_mac_entries')
                res = self.deserialize(
                    self.fmt, req.get_response(self.ext_api))
                self.assertEqual(len(res['remote_mac_entries']), 1)

    def test_delete_remote_mac(self):
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id) as gw_dev:
            with self.remote_mac_entry(FAKE_MAC_ADDRESS, FAKE_VTEP_ADDRESS,
                                       FAKE_SEG_ID,
                                       gw_dev['gateway_device']['id']) as rme:
                req = self.new_delete_request('gw/gateway_devices/'
                                              + gw_dev['gateway_device']['id']
                                              + '/remote_mac_entries',
                                              rme['remote_mac_entry']['id'])
                res = req.get_response(self.ext_api)
                self.assertEqual(res.status_int, webob.exc.HTTPNoContent.code)

    def test_delete_gateway_device_with_remote_mac(self):
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id) as gw_dev:
            with self.remote_mac_entry(FAKE_MAC_ADDRESS, FAKE_VTEP_ADDRESS,
                                       FAKE_SEG_ID,
                                       gw_dev['gateway_device']['id']):
                req = self.new_delete_request('gw/gateway_devices',
                                              gw_dev['gateway_device']['id'])
                res = req.get_response(self.ext_api)
                self.assertEqual(res.status_int, webob.exc.HTTPNoContent.code)

    def test_create_gateway_device_with_tunnel_ips(self):
        expected = {'name': TYPE_ROUTER_VTEP,
                    'type': TYPE_ROUTER_VTEP,
                    'resource_id': self._router_id,
                    'tunnel_ips': [FAKE_TUNNEL_IP],
                    'tenant_id': FAKE_TENANT_ID}
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id,
            tunnel_ips=[FAKE_TUNNEL_IP]) as gw_dev:
            for k, v in expected.items():
                self.assertEqual(gw_dev['gateway_device'][k], v)

    def test_create_gateway_device_error_delete_neutron_resouce(self):
        self.client_mock.create_gateway_device_postcommit.side_effect = \
            Exception("Fake Error")
        self._create_gateway_device_router_vtep()
        req = self.new_list_request('gw/gateway_devices')
        res = self.deserialize(self.fmt, req.get_response(self.ext_api))
        self.assertFalse(res['gateway_devices'])

    def test_update_gateway_device_error_rollback_neutron_resouce(self):
        self.client_mock.update_gateway_device_postcommit.side_effect = \
            Exception("Fake Error")
        self.test_update_gateway_device_tunnel_ips()
        req = self.new_list_request('gw/gateway_devices')
        res = self.deserialize(self.fmt, req.get_response(self.ext_api))
        self.assertEqual(res['gateway_devices'][0]['tunnel_ips'],
                         [FAKE_TUNNEL_IP])

    def test_create_remote_mac_entry_error_delete_neutron_resouce(self):
        self.client_mock.update_gateway_device_postcommit.\
            side_effect = Exception("Fake Error")
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id) as gw_dev:
            try:
                with self.remote_mac_entry(FAKE_MAC_ADDRESS, FAKE_VTEP_ADDRESS,
                                           FAKE_SEG_ID,
                                           gw_dev['gateway_device']['id']):
                    self.assertTrue(False)
            except webob.exc.HTTPClientError:
                pass
            req = self.new_list_request('gw/gateway_devices/'
                                        + gw_dev['gateway_device']['id']
                                        + '/remote_mac_entries')
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertFalse(res['remote_mac_entries'])

    def test_delete_gateway_device_error_delete_neutron_resouce(self):
        self.client_mock.delete_gateway_device_postcommit.side_effect = \
            Exception("Fake Error")
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id) as gw_dev:
            req = self.new_delete_request('gw/gateway_devices',
                                          gw_dev['gateway_device']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(res.status_int,
                             webob.exc.HTTPInternalServerError.code)
            # check the resouce deleted in Neutron DB
            req = self.new_list_request('gw/gateway_devices')
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertFalse(res['gateway_devices'])

    def test_delete_remote_mac_entry_error_delete_neutron_resouce(self):
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id) as gw_dev:
            with self.remote_mac_entry(FAKE_MAC_ADDRESS, FAKE_VTEP_ADDRESS,
                                       FAKE_SEG_ID,
                                       gw_dev['gateway_device']['id']) as rme:
                self.client_mock.update_gateway_device_postcommit.\
                    side_effect = Exception("Fake Error")
                req = self.new_delete_request('gw/gateway_devices/'
                                              + gw_dev['gateway_device']['id']
                                              + '/remote_mac_entries',
                                              rme['remote_mac_entry']['id'])
                res = req.get_response(self.ext_api)
                self.assertEqual(res.status_int,
                                 webob.exc.HTTPInternalServerError.code)
                # check the resouce deleted in Neutron DB
                req = self.new_list_request('gw/gateway_devices')
                res = self.deserialize(self.fmt,
                                       req.get_response(self.ext_api))
                self.assertEqual(
                    res['gateway_devices'][0]['remote_mac_entries'], [])

    def _make_remote_mac_entry(self, mac_address=FAKE_MAC_ADDRESS,
                               vtep_address=FAKE_VTEP_ADDRESS,
                               segmentation_id=FAKE_SEG_ID, gw_dev_id=""):
        res = self._create_remote_mac_entry(mac_address,
                                            vtep_address,
                                            segmentation_id, gw_dev_id)
        if res.status_int >= webob.exc.HTTPBadRequest.code:
            raise webob.exc.HTTPClientError(code=res.status_int)
        return self.deserialize(self.fmt, res)

    @contextlib.contextmanager
    def remote_mac_entry(self, mac_address=FAKE_MAC_ADDRESS,
                         vtep_address=FAKE_VTEP_ADDRESS,
                         segmentation_id=FAKE_SEG_ID, gw_dev_id=""):
        rme = self._make_remote_mac_entry(mac_address, vtep_address,
                                          segmentation_id, gw_dev_id)
        yield rme

    def test_create_gateway_device_hw_vtep(self):
        expected = {'name': TYPE_HW_VTEP,
                    'type': TYPE_HW_VTEP,
                    'management_ip': FAKE_MANAGEMENT_IP,
                    'management_port': FAKE_MANAGEMENT_PORT,
                    'management_protocol': OVSDB}
        with self.gateway_device_type_hw_vtep() as gw_dev:
            for k, v in expected.items():
                self.assertEqual(gw_dev['gateway_device'][k], v)

    def test_create_gateway_device_router_vtep(self):
        expected = {'name': TYPE_ROUTER_VTEP,
                    'type': TYPE_ROUTER_VTEP,
                    'resource_id': self._router_id}
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id) as gw_dev:
            for k, v in expected.items():
                self.assertEqual(gw_dev['gateway_device'][k], v)

    def test_create_gateway_device_router_vtep_not_found(self):
        res = self._create_gateway_device_router_vtep(resource_id='a')
        self.deserialize(self.fmt, res)
        self.assertEqual(res.status_int, webob.exc.HTTPNotFound.code)

    def test_create_gateway_device_with_multiple_tunnel_ips(self):
        res = self._create_gateway_device_router_vtep(
            resource_id=self._router_id,
            tunnel_ips=[FAKE_TUNNEL_IP, FAKE_TUNNEL_IP2])
        self.deserialize(self.fmt, res)
        self.assertEqual(res.status_int, webob.exc.HTTPBadRequest.code)

    def test_update_gateway_device_with_multiple_tunnel_ips(self):
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id) as gw_dev:
            data = {'gateway_device':
                {'tunnel_ips': [FAKE_TUNNEL_IP, FAKE_TUNNEL_IP2]}}
            gw_dev_req = self.new_update_request(
                'gw/gateway_devices',
                data,
                gw_dev['gateway_device']['id'])
            res = gw_dev_req.get_response(self.ext_api)
            self.deserialize(self.fmt, res)
            self.assertEqual(res.status_int, webob.exc.HTTPBadRequest.code)

    def test_create_gateway_device_router_with_duplicate_router(self):
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id) as gw_dev:
            res = self._create_gateway_device_router_vtep(
                resource_id=gw_dev['gateway_device']['resource_id'])
            self.deserialize(self.fmt, res)
            self.assertEqual(res.status_int, webob.exc.HTTPConflict.code)

    def test_create_gateway_device_hw_vtep_without_management_ip(self):
        res = self._create_gateway_device_hw_vtep(
            management_port=FAKE_MANAGEMENT_PORT)
        self.deserialize(self.fmt, res)
        self.assertEqual(res.status_int, webob.exc.HTTPBadRequest.code)

    def test_create_gateway_device_hw_vtep_without_management_port(self):
        res = self._create_gateway_device_hw_vtep(
            management_ip=FAKE_MANAGEMENT_IP)
        self.deserialize(self.fmt, res)
        self.assertEqual(res.status_int, webob.exc.HTTPBadRequest.code)

    def test_create_gateway_device_router_vtep_without_resource_id(self):
        res = self._create_gateway_device_router_vtep()
        self.deserialize(self.fmt, res)
        self.assertEqual(res.status_int, webob.exc.HTTPBadRequest.code)

    def test_delete_gateway_device(self):
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id) as gw_dev:
            req = self.new_delete_request('gw/gateway_devices',
                                          gw_dev['gateway_device']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPNoContent.code)

    def test_delete_gateway_device_in_use(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id_in_use) as gw_dev:
            req = self.new_delete_request('gw/gateway_devices',
                                          gw_dev['gateway_device']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPConflict.code)

    def test_delete_router_in_use(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id):
            req = self.new_delete_request('routers',
                                          self._router_id)
            res = req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPConflict.code)

    def test_update_gateway_device(self):
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id) as gw_dev:
            data = {'gateway_device': {'name': 'new_name'}}
            req = self.new_update_request('gw/gateway_devices',
                                          data,
                                          gw_dev['gateway_device']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertEqual(res['gateway_device']['name'],
                             data['gateway_device']['name'])

    def test_update_gateway_device_tunnel_ips(self):
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id,
            tunnel_ips=[FAKE_TUNNEL_IP]) as gw_dev:
            data = {'gateway_device': {'tunnel_ips': [FAKE_TUNNEL_IP2]}}
            req = self.new_update_request('gw/gateway_devices',
                                          data,
                                          gw_dev['gateway_device']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertEqual(res['gateway_device']['tunnel_ips'],
                             data['gateway_device']['tunnel_ips'])

    def test_show_gateway_device_hw_vtep(self):
        expected = {'name': TYPE_HW_VTEP,
                    'type': TYPE_HW_VTEP,
                    'management_ip': FAKE_MANAGEMENT_IP,
                    'management_port': FAKE_MANAGEMENT_PORT,
                    'management_protocol': OVSDB}
        with self.gateway_device_type_hw_vtep() as gw_dev:
            req = self.new_show_request('gw/gateway_devices',
                                        gw_dev['gateway_device']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            for k, v in expected.items():
                self.assertEqual(res['gateway_device'][k], v)

    def test_show_gateway_device_router_vtep(self):
        expected = {'name': TYPE_ROUTER_VTEP,
                    'type': TYPE_ROUTER_VTEP,
                    'resource_id': self._router_id}
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id) as gw_dev:
            req = self.new_show_request('gw/gateway_devices',
                                        gw_dev['gateway_device']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            for k, v in expected.items():
                self.assertEqual(res['gateway_device'][k], v)

    def test_list_gateway_devices(self):
        with self.gateway_device_type_router_vtep(
            resource_id=self._router_id):
            with self.gateway_device_type_hw_vtep():
                req = self.new_list_request('gw/gateway_devices')
                res = self.deserialize(
                    self.fmt, req.get_response(self.ext_api))
                self.assertEqual(len(res['gateway_devices']), 2)
