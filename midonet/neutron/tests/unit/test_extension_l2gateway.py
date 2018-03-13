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

import mock
from oslo_utils import uuidutils
import webob.exc

from networking_l2gw.extensions import l2gateway
from networking_l2gw.extensions import l2gatewayconnection
from networking_l2gw.services.l2gateway.common import constants as l2gw_consts
from neutron.db import servicetype_db as st_db
from neutron.services import provider_configuration as provconf
from neutron.tests.unit.api import test_extensions as test_ex
from neutron.tests.unit.extensions import test_l3

from midonet.neutron.common import constants as mido_const
from midonet.neutron.tests.unit import test_extension_gateway_device as test_gw
from midonet.neutron.tests.unit import test_midonet_plugin_ml2 as test_mn_ml2

L2_GW_NAME = 'l2_gw1'
L2_GW_NAME2 = 'l2_gw2'
FAKE_SEG_ID = '1000'
FAKE_SEG_ID_VXLAN = '7000'
INVALID_VLAN_ID = 4095
INVALID_VXLAN_ID = 16777216
MN_PLUGIN_KLASS = 'midonet_l2gw'
MN_DRIVER_KLASS = ('midonet.neutron.services.l2gateway.service_drivers.'
                   'l2gw_midonet.MidonetL2gwDriver')


class MidonetL2GatewayTestExtensionManager(
        test_gw.GatewayDeviceTestExtensionManager,
        test_l3.L3TestExtensionManager):

    def get_resources(self):
        res = super(MidonetL2GatewayTestExtensionManager, self).get_resources()
        return (res + l2gateway.L2gateway.get_resources() +
                l2gatewayconnection.L2gatewayconnection.get_resources())

    def get_actions(self):
        return []

    def get_request_extensions(self):
        return []


class MidonetL2GatewayTestCaseMixin(test_gw.GatewayDeviceTestCaseMixin,
                                    test_l3.L3NatTestCaseMixin):

    def setUp(self, plugin=None, ext_mgr=None):

        service_plugins = {'l2gw_plugin_name': MN_PLUGIN_KLASS,
                           'gateway_device_plugin_name':
                               test_gw.DB_GATEWAY_DEVICE_PLUGIN_KLASS}
        l2gw_provider = (l2gw_consts.L2GW + ':' +
                         mido_const.MIDONET_L2GW_PROVIDER +
                         ':' + MN_DRIVER_KLASS + ':default')
        mock.patch.object(provconf.NeutronModule, 'service_providers',
                          return_value=[l2gw_provider]).start()
        manager = st_db.ServiceTypeManager.get_instance()
        manager.add_provider_configuration(
            l2gw_consts.L2GW, provconf.ProviderConfiguration())
        l2_gw_mgr = MidonetL2GatewayTestExtensionManager()

        super(MidonetL2GatewayTestCaseMixin, self).setUp(
            service_plugins=service_plugins, ext_mgr=l2_gw_mgr)
        self.ext_api = test_ex.setup_extensions_middleware(l2_gw_mgr)

        network = self._make_network(self.fmt, 'net1', True)
        self._network_id = network['network']['id']
        self._subnet = self._make_subnet(self.fmt, network, "10.0.0.1",
                                         '10.0.0.0/24')
        self._subnet_id = self._subnet['subnet']['id']
        network2 = self._make_network(self.fmt, 'net2', True)
        self._network_id2 = network2['network']['id']
        self._subnet2 = self._make_subnet(self.fmt, network2, "20.0.0.1",
                                          '20.0.0.0/24')
        self._subnet_id2 = self._subnet2['subnet']['id']
        router1 = self._make_router('json', uuidutils.generate_uuid(),
                                    'router1', True)
        self._router_id = router1['router']['id']
        router2 = self._make_router('json', uuidutils.generate_uuid(),
                                    'router2', True)
        self._router_id2 = router2['router']['id']

        # for network_vlan gateway device setting
        res = self._create_network(self.fmt, 'gateway_network_vlan', True)
        self._vlan_network_id = self.deserialize(
            self.fmt, res)['network']['id']

    def _create_l2_gateway(self, name=L2_GW_NAME, device_id="", device_id2="",
                           seg_id=None):
        data = {'l2_gateway': {'devices': [{'device_id': device_id}],
                               'tenant_id': uuidutils.generate_uuid(),
                               'name': name}}
        if device_id2:
            data['l2_gateway']['devices'].append({'device_id': device_id2})
        if seg_id:
            data['l2_gateway']['devices'][0]['segmentation_id'] = seg_id
        l2_gw_req = self.new_create_request('l2-gateways',
                                            data, self.fmt)
        return l2_gw_req.get_response(self.ext_api)

    def _create_l2_gateway_connection(self, l2_gateway_id="", network_id="",
                                      segmentation_id=FAKE_SEG_ID):
        data = {
            'l2_gateway_connection': {'l2_gateway_id': l2_gateway_id,
                                      'network_id': network_id,
                                      'tenant_id': uuidutils.generate_uuid(),
                                      'segmentation_id': segmentation_id}}
        l2_gw_conn_req = self.new_create_request('l2-gateway-connections',
                                                 data, self.fmt)
        return l2_gw_conn_req.get_response(self.ext_api)

    @contextlib.contextmanager
    def l2_gateway(self, name=L2_GW_NAME, device_id="", segmentation_id=''):
        l2_gw = self._make_l2_gateway(name, device_id, segmentation_id)
        yield l2_gw

    @contextlib.contextmanager
    def l2_gateway_connection(self, l2_gateway_id="", network_id="",
                              segmentation_id=FAKE_SEG_ID):
        l2_gw_con = self._make_l2_gateway_connection(l2_gateway_id,
                                                     network_id,
                                                     segmentation_id)
        yield l2_gw_con

    def _make_l2_gateway(self, name, device_id, segmentation_id):
        res = self._create_l2_gateway(name, device_id, seg_id=segmentation_id)
        if res.status_int >= webob.exc.HTTPBadRequest.code:
            raise webob.exc.HTTPClientError(code=res.status_int)
        return self.deserialize(self.fmt, res)

    def _make_l2_gateway_connection(self, l2_gateway_id, network_id,
                                    segmentation_id):
        res = self._create_l2_gateway_connection(l2_gateway_id, network_id,
                                                 segmentation_id)
        if res.status_int >= webob.exc.HTTPBadRequest.code:
            raise webob.exc.HTTPClientError(code=res.status_int)
        return self.deserialize(self.fmt, res)

    def test_create_midonet_l2gateway(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            name = L2_GW_NAME
            device_id = gw_dev['gateway_device']['id']
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']) as l2_gw:
                self.assertEqual(name, l2_gw['l2_gateway']['name'])
                self.assertEqual(
                    device_id,
                    l2_gw['l2_gateway']['devices'][0]['device_id'])

    def test_create_midonet_l2gateway_vlan(self):
        with self.gateway_device_type_network_vlan(
                resource_id=self._vlan_network_id) as gw_dev:
            name = L2_GW_NAME
            device_id = gw_dev['gateway_device']['id']
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']) as l2_gw:
                self.assertEqual(name, l2_gw['l2_gateway']['name'])
                self.assertEqual(
                    device_id,
                    l2_gw['l2_gateway']['devices'][0]['device_id'])

    def test_create_midonet_l2gateway_with_invalid_seg_id(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            res = self._create_l2_gateway(
                device_id=gw_dev['gateway_device']['id'],
                seg_id=INVALID_VXLAN_ID)
            self.deserialize(self.fmt, res)
            self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_create_midonet_l2gateway_vlan_with_invalid_seg_id(self):
        with self.gateway_device_type_network_vlan(
                resource_id=self._vlan_network_id) as gw_dev:
            res = self._create_l2_gateway(
                device_id=gw_dev['gateway_device']['id'],
                seg_id=INVALID_VLAN_ID)
            self.deserialize(self.fmt, res)
            self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_create_midonet_l2gateway_with_gateway_device_not_found(self):
        res = self._create_l2_gateway(device_id='a')
        self.deserialize(self.fmt, res)
        self.assertEqual(webob.exc.HTTPNotFound.code, res.status_int)

    def test_create_midonet_l2gateway_with_multiple_gateway_devices(self):
        res = self._create_l2_gateway(device_id='a', device_id2='b')
        self.deserialize(self.fmt, res)
        self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_create_midonet_l2gateway_with_segmentation_id(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            name = L2_GW_NAME
            device_id = gw_dev['gateway_device']['id']
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id'],
                    segmentation_id=FAKE_SEG_ID_VXLAN) as l2_gw:
                self.assertEqual(name, l2_gw['l2_gateway']['name'])
                self.assertEqual(
                    device_id,
                    l2_gw['l2_gateway']['devices'][0]['device_id'])
                self.assertEqual(
                    FAKE_SEG_ID_VXLAN,
                    l2_gw['l2_gateway']['devices'][0]['segmentation_id'])

    def test_create_midonet_l2gateway_vlan_with_segmentation_id(self):
        with self.gateway_device_type_network_vlan(
                resource_id=self._vlan_network_id) as gw_dev:
            name = L2_GW_NAME
            device_id = gw_dev['gateway_device']['id']
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id'],
                    segmentation_id=FAKE_SEG_ID) as l2_gw:
                self.assertEqual(name, l2_gw['l2_gateway']['name'])
                self.assertEqual(
                    device_id,
                    l2_gw['l2_gateway']['devices'][0]['device_id'])
                self.assertEqual(
                    FAKE_SEG_ID,
                    l2_gw['l2_gateway']['devices'][0]['segmentation_id'])

    def test_delete_midonet_l2gateway(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']) as l2_gw:
                req = self.new_delete_request('l2-gateways',
                                              l2_gw['l2_gateway']['id'])
                res = req.get_response(self.ext_api)
                self.assertEqual(webob.exc.HTTPNoContent.code, res.status_int)

    def test_delete_midonet_l2gateway_vlan(self):
        with self.gateway_device_type_network_vlan(
                resource_id=self._vlan_network_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']) as l2_gw:
                req = self.new_delete_request('l2-gateways',
                                              l2_gw['l2_gateway']['id'])
                res = req.get_response(self.ext_api)
                self.assertEqual(webob.exc.HTTPNoContent.code, res.status_int)

    def test_delete_midonet_l2gateway_with_seg_id(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id'],
                    segmentation_id=FAKE_SEG_ID) as l2_gw:
                req = self.new_delete_request('l2-gateways',
                                              l2_gw['l2_gateway']['id'])
                res = req.get_response(self.ext_api)
                self.assertEqual(webob.exc.HTTPNoContent.code, res.status_int)

    def test_list_l2gateways(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev1:
            with self.l2_gateway(name=L2_GW_NAME,
                                 device_id=gw_dev1['gateway_device']['id']):
                with self.gateway_device_type_router_vtep(
                        resource_id=self._router_id2,
                        tunnel_ips=[test_gw.FAKE_TUNNEL_IP2]) as gw_dev2:
                    with self.l2_gateway(
                            name=L2_GW_NAME,
                            device_id=gw_dev2['gateway_device']['id']):
                        req = self.new_list_request('l2-gateways')
                        res = self.deserialize(
                            self.fmt, req.get_response(self.ext_api))
                        self.assertEqual(2, len(res['l2_gateways']))

    def test_create_midonet_l2gateway_connection(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']) as l2_gw:
                with self.l2_gateway_connection(
                        l2_gateway_id=l2_gw['l2_gateway']['id'],
                        network_id=self._network_id,
                        segmentation_id=str(FAKE_SEG_ID_VXLAN)) as l2_gw_con:
                    self.assertEqual(
                        self._network_id,
                        l2_gw_con['l2_gateway_connection']['network_id'])
                    self.assertEqual(
                        l2_gw['l2_gateway']['id'],
                        l2_gw_con['l2_gateway_connection']['l2_gateway_id'])
                    self.assertEqual(
                        FAKE_SEG_ID_VXLAN,
                        l2_gw_con['l2_gateway_connection']['segmentation_id'])

    def test_create_midonet_l2gateway_vlan_connection(self):
        with self.gateway_device_type_network_vlan(
                resource_id=self._vlan_network_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']) as l2_gw:
                with self.l2_gateway_connection(
                        l2_gateway_id=l2_gw['l2_gateway']['id'],
                        network_id=self._network_id) as l2_gw_con:
                    self.assertEqual(
                        self._network_id,
                        l2_gw_con['l2_gateway_connection']['network_id'])
                    self.assertEqual(
                        l2_gw['l2_gateway']['id'],
                        l2_gw_con['l2_gateway_connection']['l2_gateway_id'])
                    self.assertEqual(
                        FAKE_SEG_ID,
                        l2_gw_con['l2_gateway_connection']['segmentation_id'])

    def test_create_midonet_l2gateway_and_l2gateway_con_without_seg_id(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']) as l2_gw:
                res = self._create_l2_gateway_connection(
                    l2_gateway_id=l2_gw['l2_gateway']['id'],
                    network_id=self._network_id,
                    segmentation_id='')
                self.deserialize(self.fmt, res)
                self.assertEqual(webob.exc.HTTPBadRequest.code,
                                 res.status_int)

    def test_create_midonet_l2gateway_connection_with_not_found_network(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']) as l2_gw:
                res = self._create_l2_gateway_connection(
                    l2_gateway_id=l2_gw['l2_gateway']['id'],
                    network_id='a')
                self.deserialize(self.fmt, res)
                self.assertEqual(webob.exc.HTTPNotFound.code, res.status_int)

    def test_create_midonet_l2gateway_connection_with_invalid_seg_id(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']) as l2_gw:
                res = self._create_l2_gateway_connection(
                    l2_gateway_id=l2_gw['l2_gateway']['id'],
                    network_id=self._network_id,
                    segmentation_id=str(INVALID_VXLAN_ID))
                self.deserialize(self.fmt, res)
                self.assertEqual(webob.exc.HTTPBadRequest.code,
                                 res.status_int)

    def test_create_midonet_l2gateway_vlan_conn_with_invalid_seg_id(self):
        with self.gateway_device_type_network_vlan(
                resource_id=self._vlan_network_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']) as l2_gw:
                res = self._create_l2_gateway_connection(
                    l2_gateway_id=l2_gw['l2_gateway']['id'],
                    network_id=self._network_id,
                    segmentation_id=str(INVALID_VLAN_ID))
                self.deserialize(self.fmt, res)
                self.assertEqual(webob.exc.HTTPBadRequest.code,
                                 res.status_int)

    def test_create_midonet_l2gateway_connection_with_invalid_l2_gateway(self):
        res = self._create_l2_gateway_connection(l2_gateway_id='a',
                                                 network_id=self._network_id,
                                                 segmentation_id=FAKE_SEG_ID)
        self.deserialize(self.fmt, res)
        self.assertEqual(webob.exc.HTTPNotFound.code, res.status_int)

    def test_create_midonet_l2gateway_con_seg_id_with_l2gw_seg_id(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id'],
                    segmentation_id=FAKE_SEG_ID) as l2_gw:
                res = self._create_l2_gateway_connection(
                    l2_gateway_id=l2_gw['l2_gateway']['id'],
                    network_id=self._network_id,
                    segmentation_id=str(FAKE_SEG_ID))
                self.deserialize(self.fmt, res)
                self.assertEqual(webob.exc.HTTPBadRequest.code,
                                 res.status_int)

    def test_create_midonet_l2gateway_connection_with_l2gw_seg_id(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id'],
                    segmentation_id=FAKE_SEG_ID_VXLAN) as l2_gw:
                with self.l2_gateway_connection(
                        l2_gateway_id=l2_gw['l2_gateway']['id'],
                        network_id=self._network_id,
                        segmentation_id='') as l2_gw_con:
                    self.assertEqual(
                        self._network_id,
                        l2_gw_con['l2_gateway_connection']['network_id'])
                    self.assertEqual(
                        l2_gw['l2_gateway']['id'],
                        l2_gw_con['l2_gateway_connection']['l2_gateway_id'])
                    self.assertEqual(
                        '',
                        l2_gw_con['l2_gateway_connection']['segmentation_id'])

    def test_create_midonet_l2gateway_vlan_connection_with_l2gw_seg_id(self):
        with self.gateway_device_type_network_vlan(
                resource_id=self._vlan_network_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id'],
                    segmentation_id=FAKE_SEG_ID) as l2_gw:
                with self.l2_gateway_connection(
                        l2_gateway_id=l2_gw['l2_gateway']['id'],
                        network_id=self._network_id,
                        segmentation_id='') as l2_gw_con:
                    self.assertEqual(
                        self._network_id,
                        l2_gw_con['l2_gateway_connection']['network_id'])
                    self.assertEqual(
                        l2_gw['l2_gateway']['id'],
                        l2_gw_con['l2_gateway_connection']['l2_gateway_id'])
                    self.assertEqual(
                        '',
                        l2_gw_con['l2_gateway_connection']['segmentation_id'])

    def test_create_midonet_l2gateway_conn_error_delete_neutron_resource(self):
        self.client_mock.create_l2_gateway_connection.side_effect = Exception(
            "Fake Error")
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']) as l2_gw:
                try:
                    with self.l2_gateway_connection(
                            l2_gateway_id=l2_gw['l2_gateway']['id'],
                            network_id=self._network_id,
                            segmentation_id=FAKE_SEG_ID):
                        self.assertTrue(False)
                except webob.exc.HTTPClientError:
                    pass
                req = self.new_list_request('l2-gateway-connections')
                res = self.deserialize(self.fmt,
                                       req.get_response(self.ext_api))
                self.assertFalse(res['l2_gateway_connections'])

    def test_create_multiple_midonet_l2gateway_con_with_same_l2gateway(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']) as l2_gw:
                with self.l2_gateway_connection(
                        l2_gateway_id=l2_gw['l2_gateway']['id'],
                        network_id=self._network_id):
                    res = self._create_l2_gateway_connection(
                        l2_gateway_id=l2_gw['l2_gateway']['id'],
                        network_id=self._network_id2,
                        segmentation_id=FAKE_SEG_ID)
                    self.deserialize(self.fmt, res)
                    self.assertEqual(webob.exc.HTTPConflict.code,
                                     res.status_int)

    def test_delete_midonet_l2gateway_connection(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']) as l2_gw:
                with self.l2_gateway_connection(
                        l2_gateway_id=l2_gw['l2_gateway']['id'],
                        network_id=self._network_id) as l2_gw_con:
                    req = self.new_delete_request(
                        'l2-gateway-connections',
                        l2_gw_con['l2_gateway_connection']['id'])
                    res = req.get_response(self.ext_api)
                    self.assertEqual(webob.exc.HTTPNoContent.code,
                                     res.status_int)

    def test_delete_midonet_l2gateway_vlan_connection(self):
        with self.gateway_device_type_network_vlan(
                resource_id=self._vlan_network_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']) as l2_gw:
                with self.l2_gateway_connection(
                        l2_gateway_id=l2_gw['l2_gateway']['id'],
                        network_id=self._network_id) as l2_gw_con:
                    req = self.new_delete_request(
                        'l2-gateway-connections',
                        l2_gw_con['l2_gateway_connection']['id'])
                    res = req.get_response(self.ext_api)
                    self.assertEqual(webob.exc.HTTPNoContent.code,
                                     res.status_int)

    def test_delete_midonet_l2gateway_connection_without_seg_id(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id'],
                    segmentation_id=FAKE_SEG_ID) as l2_gw:
                with self.l2_gateway_connection(
                        l2_gateway_id=l2_gw['l2_gateway']['id'],
                        network_id=self._network_id,
                        segmentation_id='') as l2_gw_con:
                    req = self.new_delete_request(
                        'l2-gateway-connections',
                        l2_gw_con['l2_gateway_connection']['id'])
                    res = req.get_response(self.ext_api)
                    self.assertEqual(webob.exc.HTTPNoContent.code,
                                     res.status_int)

    def test_delete_midonet_l2gateway_with_connection(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']) as l2_gw:
                with self.l2_gateway_connection(
                        l2_gateway_id=l2_gw['l2_gateway']['id'],
                        network_id=self._network_id):
                    req = self.new_delete_request('l2-gateways',
                                                  l2_gw['l2_gateway']['id'])
                    res = req.get_response(self.ext_api)
                    self.assertEqual(webob.exc.HTTPConflict.code,
                                     res.status_int)

    def test_list_gateway_connections(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']) as l2_gw:
                with self.l2_gateway_connection(
                        l2_gateway_id=l2_gw['l2_gateway']['id'],
                        network_id=self._network_id):
                    req = self.new_list_request('l2-gateway-connections')
                    res = self.deserialize(
                        self.fmt, req.get_response(self.ext_api))
                    self.assertEqual(1, len(res['l2_gateway_connections']))

    def test_delete_gateway_device_in_use_by_l2gateway(self):
        with self.gateway_device_type_router_vtep(
                resource_id=self._router_id) as gw_dev:
            with self.l2_gateway(
                    name=L2_GW_NAME,
                    device_id=gw_dev['gateway_device']['id']):
                req = self.new_delete_request('gw/gateway_devices',
                                              gw_dev['gateway_device']['id'])
                res = req.get_response(self.ext_api)
                self.assertEqual(webob.exc.HTTPConflict.code,
                                 res.status_int)


class MidonetL2GatewayTestCaseML2(MidonetL2GatewayTestCaseMixin,
                                  test_mn_ml2.MidonetPluginML2TestCase):
    pass
