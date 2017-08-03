# Copyright (C) 2016 Midokura SARL.
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
from neutron.tests.unit.extensions import test_extraroute
from neutron.tests.unit.extensions import test_l3
from neutron_dynamic_routing.extensions import bgp

from midonet.neutron.common import constants as m_const
from midonet.neutron import extensions as midoextensions
from midonet.neutron.extensions import bgp_speaker_router_insertion as bsri
from midonet.neutron.services.bgp import plugin as bgp_plugin
from midonet.neutron.tests.unit import test_midonet_plugin_ml2 as test_mn_ml2

FAKE_SPEAKER_NAME = "bgp_spaeker_1"
FAKE_LOCAL_AS = 65000
FAKE_REMOTE_AS = 65001
NOT_FOUND_ROUTER_UUID = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
FAKE_PEER_IP = "192.168.0.254"
FAKE_PEER_IP2 = "192.168.1.254"
FAKE_PEER_NAME = "bgp_peer_1"
FAKE_PEER_NAME2 = "bgp_peer_2"
AUTH_TYPE_MD5 = "md5"
AUTH_TYPE_NONE = "none"
FAKE_AUTH_PASSWORD = "testtest"
ADD_BGP_PEER_ACTION = "add_bgp_peer"
REMOVE_BGP_PEER_ACTION = "remove_bgp_peer"
ADD_NETWORK_ACTION = "add_gateway_network"
REMOVE_NETWORK_ACTION = "remove_gateway_network"
ADD_INTERFACE_ACTION = "add_router_interface"
REMOVE_INTERFACE_ACTION = "remove_router_interface"

BGP_PLUGIN_KLASS = 'midonet_bgp'
extensions_path = ':'.join(midoextensions.__path__)


class BgpTestExtensionManager(
        test_extraroute.ExtraRouteTestExtensionManager):

    def get_resources(self):
        res = super(BgpTestExtensionManager, self).get_resources()
        bgp.RESOURCE_ATTRIBUTE_MAP['bgp-speakers'].update(
            bsri.EXTENDED_ATTRIBUTES_2_0['bgp-speakers'])
        return res + bgp.Bgp.get_resources()

    def get_actions(self):
        return []

    def get_request_extensions(self):
        return []


class BgpTestCaseMixin(test_l3.L3NatTestCaseMixin):

    def setUp(self, plugin=None, service_plugins=None, ext_mgr=None):

        service_plugins = {'bgp_plugin_name': BGP_PLUGIN_KLASS}
        bgp_mgr = BgpTestExtensionManager()
        super(BgpTestCaseMixin, self).setUp(
            service_plugins=service_plugins, ext_mgr=bgp_mgr)
        self.ext_api = test_ex.setup_extensions_middleware(bgp_mgr)
        self.bgp_plugin = bgp_plugin.MidonetBgpPlugin()

        network = self._make_network(self.fmt, 'net1', True)
        self._subnet = self._make_subnet(self.fmt, network, "192.168.0.1",
                                         '192.168.0.0/24')
        self._subnet_id = self._subnet['subnet']['id']
        network = self._make_network(self.fmt, 'net2', True)
        self._subnet = self._make_subnet(self.fmt, network, "192.168.1.1",
                                         '192.168.1.0/24')
        self._subnet_id2 = self._subnet['subnet']['id']
        network = self._make_network(self.fmt, 'net3', True)
        self._subnet = self._make_subnet(self.fmt, network, "192.168.2.1",
                                         '192.168.2.0/24')
        self._subnet_id3 = self._subnet['subnet']['id']
        port = self._make_port(self.fmt, network['network']['id'])
        self._port_id = port['port']['id']
        self._port_fixed_ip = port['port']['fixed_ips'][0]['ip_address']
        router1 = self._make_router(self.fmt, uuidutils.generate_uuid(),
                                    'router1', True)
        self._router_id = router1['router']['id']
        router2 = self._make_router(self.fmt, uuidutils.generate_uuid(),
                                    'router2', True)
        self._router_id2 = router2['router']['id']
        self._router_interface_action('add', self._router_id, self._subnet_id,
                                      None)
        self._router_interface_action('add', self._router_id, self._subnet_id2,
                                      None)
        self._router_interface_action('add', self._router_id, self._subnet_id3,
                                      None)
        self._router_interface_action('add', self._router_id2, None,
                                      self._port_id)

        # for non-router use case
        ext_net = self._make_network(self.fmt, 'ext_net2', True)
        self._set_net_external(ext_net['network']['id'])
        self._ext_net_id = ext_net['network']['id']
        self._ext_subnet = self._make_subnet(self.fmt, ext_net, "100.65.0.1",
                                             '100.65.0.0/24')
        self._ext_subnet_id = self._ext_subnet['subnet']['id']
        edge_router = self._make_router(self.fmt, uuidutils.generate_uuid(),
                                        'edge_router', True)
        self._edge_router_id = edge_router['router']['id']
        self._router_interface_action('add', self._edge_router_id,
                                      self._ext_subnet_id, None)

    @contextlib.contextmanager
    def bgp_speaker(self, name=FAKE_SPEAKER_NAME,
                    local_as=FAKE_LOCAL_AS, router_id=None):
        bgp_speaker = self._make_bgp_speaker(name, local_as, router_id)
        yield bgp_speaker

    @contextlib.contextmanager
    def bgp_peer(self, name=FAKE_PEER_NAME, peer_ip=FAKE_PEER_IP,
                 remote_as=FAKE_REMOTE_AS, auth_type=AUTH_TYPE_MD5):
        bgp_peer = self._make_bgp_peer(name, peer_ip,
                                       remote_as, auth_type)
        yield bgp_peer

    def _make_bgp_speaker(self, name, local_as, router_id):
        res = self._create_bgp_speaker(name, local_as, router_id)
        if res.status_int >= webob.exc.HTTPBadRequest.code:
            raise webob.exc.HTTPClientError(code=res.status_int)
        return self.deserialize(self.fmt, res)

    def _make_bgp_peer(self, name, peer_ip, remote_as, auth_type):
        res = self._create_bgp_peer(name, peer_ip, remote_as, auth_type)
        if res.status_int >= webob.exc.HTTPBadRequest.code:
            raise webob.exc.HTTPClientError(code=res.status_int)
        return self.deserialize(self.fmt, res)

    def _create_bgp_speaker(self, name=FAKE_SPEAKER_NAME,
                            local_as=FAKE_LOCAL_AS, router_id=None):
        data = {'bgp_speaker': {'tenant_id': uuidutils.generate_uuid(),
                                'name': name,
                                'local_as': local_as,
                                'ip_version': 4}}
        if router_id:
            data['bgp_speaker'][m_const.LOGICAL_ROUTER] = router_id
        bgp_sp_req = self.new_create_request('bgp-speakers',
                                             data, self.fmt)
        return bgp_sp_req.get_response(self.ext_api)

    def _create_bgp_peer(self, name=FAKE_PEER_NAME, peer_ip=FAKE_PEER_IP,
                         remote_as=FAKE_REMOTE_AS,
                         auth_type=AUTH_TYPE_MD5):
        data = {'bgp_peer': {'tenant_id': uuidutils.generate_uuid(),
                             'name': name,
                             'peer_ip': peer_ip,
                             'remote_as': remote_as,
                             'auth_type': auth_type}}
        if auth_type == AUTH_TYPE_MD5:
            data['bgp_peer']['password'] = FAKE_AUTH_PASSWORD
        bgp_peer_req = self.new_create_request('bgp-peers',
                                               data, self.fmt)
        return bgp_peer_req.get_response(self.ext_api)

    def test_create_bgp_speaker_with_router(self):
        expected = {'name': FAKE_SPEAKER_NAME,
                    'local_as': FAKE_LOCAL_AS,
                    'ip_version': 4,
                    m_const.LOGICAL_ROUTER: self._router_id}
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker:
            self.assertDictSupersetOf(expected, bgp_speaker['bgp_speaker'])

    def test_update_bgp_speaker_with_router(self):
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker:
            data = {'bgp_speaker': {'name': 'new_name'}}
            req = self.new_update_request('bgp-speakers',
                                          data,
                                          bgp_speaker['bgp_speaker']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertEqual(data['bgp_speaker']['name'],
                             res['bgp_speaker']['name'])

    def test_show_bgp_speaker_with_router(self):
        expected = {'name': FAKE_SPEAKER_NAME,
                    'local_as': FAKE_LOCAL_AS,
                    'ip_version': 4,
                    m_const.LOGICAL_ROUTER: self._router_id}
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker:
            req = self.new_show_request('bgp-speakers',
                                        bgp_speaker['bgp_speaker']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertDictSupersetOf(expected, res['bgp_speaker'])

    def test_list_bgp_speaker_with_router(self):
        with self.bgp_speaker(router_id=self._router_id), \
                self.bgp_speaker(router_id=self._router_id2):
            req = self.new_list_request('bgp-speakers')
            res = self.deserialize(
                self.fmt, req.get_response(self.ext_api))
            self.assertEqual(2, len(res['bgp_speakers']))

    def test_delete_bgp_speaker(self):
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker:
            req = self.new_delete_request('bgp-speakers',
                                          bgp_speaker['bgp_speaker']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPNoContent.code, res.status_int)

    def test_delete_bgp_speaker_with_peer(self):
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker, \
                self.bgp_peer() as bgp_peer:
            data = {"bgp_peer_id": bgp_peer['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            peers = [bgp_peer['bgp_peer']['id']]
            req = self.new_show_request('bgp-speakers',
                                        bgp_speaker['bgp_speaker']['id'])
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertEqual(peers, res['bgp_speaker']['peers'])
            req = self.new_delete_request('bgp-speakers',
                                          bgp_speaker['bgp_speaker']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPNoContent.code, res.status_int)

    def test_create_bgp_speaker_with_same_router(self):
        with self.bgp_speaker(router_id=self._router_id):
            res = self._create_bgp_speaker(router_id=self._router_id)
            self.deserialize(self.fmt, res)
            self.assertEqual(webob.exc.HTTPConflict.code, res.status_int)

    def test_create_bgp_speaker_with_not_found_router(self):
        res = self._create_bgp_speaker(router_id=NOT_FOUND_ROUTER_UUID)
        self.deserialize(self.fmt, res)
        self.assertEqual(webob.exc.HTTPNotFound.code, res.status_int)

    def test_create_bgp_speaker_without_router(self):
        expected = {'name': FAKE_SPEAKER_NAME,
                    'local_as': FAKE_LOCAL_AS,
                    'ip_version': 4}
        with self.bgp_speaker() as bgp_speaker:
            self.assertDictSupersetOf(expected, bgp_speaker['bgp_speaker'])

    def test_delete_bgp_speaker_error_delete_neutron_resource(self):
        self.client_mock.update_bgp_speaker_postcommit.side_effect = (
            Exception("Fake Error"))
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker, \
                self.bgp_peer() as bgp_peer:
            data = {"bgp_peer_id": bgp_peer['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            req = self.new_delete_request('bgp-speakers',
                                          bgp_speaker['bgp_speaker']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPInternalServerError.code,
                             res.status_int)
            # check the resource deleted in Neutron DB
            req = self.new_list_request('bgp-speakers')
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertFalse(res['bgp_speakers'])

    def test_delete_router_in_use_by_bgp_speaker(self):
        with self.bgp_speaker(router_id=self._router_id):
            req = self.new_delete_request('routers',
                                          self._router_id)
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPConflict.code, res.status_int)

    def test_create_bgp_peer(self):
        expected = {'name': FAKE_PEER_NAME,
                    'peer_ip': FAKE_PEER_IP,
                    'remote_as': FAKE_REMOTE_AS,
                    'auth_type': AUTH_TYPE_MD5}
        with self.bgp_peer() as bgp_peer:
            self.assertDictSupersetOf(expected, bgp_peer['bgp_peer'])

    def test_create_bgp_peer_with_auth_type_none(self):
        expected = {'name': FAKE_PEER_NAME,
                    'peer_ip': FAKE_PEER_IP,
                    'remote_as': FAKE_REMOTE_AS,
                    'auth_type': AUTH_TYPE_NONE}
        with self.bgp_peer(auth_type=AUTH_TYPE_NONE) as bgp_peer:
            self.assertDictSupersetOf(expected, bgp_peer['bgp_peer'])

    def test_update_bgp_peer(self):
        with self.bgp_peer() as bgp_peer:
            data = {'bgp_peer': {'password': 'new_password'}}
            req = self.new_update_request('bgp-peers',
                                          data,
                                          bgp_peer['bgp_peer']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPOk.code, res.status_int)

    def test_show_bgp_peer(self):
        expected = {'name': FAKE_PEER_NAME,
                    'remote_as': FAKE_REMOTE_AS,
                    'peer_ip': FAKE_PEER_IP,
                    'auth_type': AUTH_TYPE_MD5}
        with self.bgp_peer() as bgp_peer:
            req = self.new_show_request('bgp-peers',
                                        bgp_peer['bgp_peer']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertDictSupersetOf(expected, res['bgp_peer'])

    def test_list_bgp_peer(self):
        with self.bgp_peer(), self.bgp_peer():
            req = self.new_list_request('bgp-peers')
            res = self.deserialize(
                self.fmt, req.get_response(self.ext_api))
            self.assertEqual(2, len(res['bgp_peers']))

    def test_delete_bgp_peer(self):
        with self.bgp_peer() as bgp_peer:
            req = self.new_delete_request('bgp-peers',
                                          bgp_peer['bgp_peer']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPNoContent.code, res.status_int)

    def test_delete_bgp_peer_related_to_bgp_speaker(self):
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker, \
                self.bgp_peer() as bgp_peer:
            data = {"bgp_peer_id": bgp_peer['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            peers = [bgp_peer['bgp_peer']['id']]
            req = self.new_show_request('bgp-speakers',
                                        bgp_speaker['bgp_speaker']['id'])
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertEqual(peers, res['bgp_speaker']['peers'])
            req = self.new_delete_request('bgp-peers',
                                          bgp_peer['bgp_peer']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPNoContent.code, res.status_int)
            req = self.new_show_request('bgp-speakers',
                                        bgp_speaker['bgp_speaker']['id'])
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertEqual([], res['bgp_speaker']['peers'])

    def test_add_bgp_peer_error_neutron_resource_rollback(self):
        self.client_mock.create_bgp_peer_postcommit.side_effect = (
            Exception("Fake Error"))
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker, \
                self.bgp_peer() as bgp_peer:
            data = {"bgp_peer_id": bgp_peer['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPInternalServerError.code,
                             res.status_int)
            req = self.new_show_request('bgp-speakers',
                                        bgp_speaker['bgp_speaker']['id'])
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertEqual([], res['bgp_speaker']['peers'])

    def test_add_bgp_peer_with_associated_bgp_speaker(self):
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker, \
                self.bgp_peer() as bgp_peer, self.bgp_peer() as bgp_peer2:
            data = {"bgp_peer_id": bgp_peer['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            data = {"bgp_peer_id": bgp_peer2['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPConflict.code, res.status_int)

    def test_add_bgp_peer_to_bgp_speaker_without_router(self):
        with self.bgp_speaker() as bgp_speaker, self.bgp_peer() as bgp_peer:
            data = {"bgp_peer_id": bgp_peer['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_add_bgp_peer_without_bgp_peer_id_parameter(self):
        with self.bgp_speaker() as bgp_speaker, self.bgp_peer():
            req = self.new_action_request('bgp-speakers', {},
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_remove_bgp_peer_from_speaker_with_router(self):
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker, \
                self.bgp_peer() as bgp_peer:
            data = {"bgp_peer_id": bgp_peer['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            peers = [bgp_peer['bgp_peer']['id']]
            req = self.new_show_request('bgp-speakers',
                                        bgp_speaker['bgp_speaker']['id'])
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertEqual(peers, res['bgp_speaker']['peers'])
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          REMOVE_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            req = self.new_show_request('bgp-speakers',
                                        bgp_speaker['bgp_speaker']['id'])
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertEqual([], res['bgp_speaker']['peers'])

    def test_delete_bgp_peer_error_delete_neutron_resource(self):
        self.client_mock.delete_bgp_peer_postcommit.side_effect = (
            Exception("Fake Error"))
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker, \
                self.bgp_peer() as bgp_peer:
            data = {"bgp_peer_id": bgp_peer['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            peers = [bgp_peer['bgp_peer']['id']]
            req = self.new_show_request('bgp-speakers',
                                        bgp_speaker['bgp_speaker']['id'])
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertEqual(peers, res['bgp_speaker']['peers'])
            req = self.new_delete_request('bgp-peers',
                                          bgp_peer['bgp_peer']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPInternalServerError.code,
                             res.status_int)
            # check the resource deleted in Neutron DB
            req = self.new_list_request('bgp-peers')
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertFalse(res['bgp_peers'])

    def test_remove_bgp_peer_error_delete_neutron_resource(self):
        self.client_mock.delete_bgp_peer_postcommit.side_effect = (
            Exception("Fake Error"))
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker, \
                self.bgp_peer() as bgp_peer:
            data = {"bgp_peer_id": bgp_peer['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          REMOVE_BGP_PEER_ACTION)
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPInternalServerError.code,
                             res.status_int)
            req = self.new_show_request('bgp-speakers',
                                        bgp_speaker['bgp_speaker']['id'])
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertEqual([], res['bgp_speaker']['peers'])

    def test_mutiple_bgp_peers_per_bgp_speaker(self):
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker, \
                self.bgp_peer() as bgp_peer1, \
                self.bgp_peer(name=FAKE_PEER_NAME2,
                              peer_ip=FAKE_PEER_IP2) as bgp_peer2:
            data = {"bgp_peer_id": bgp_peer1['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            data = {"bgp_peer_id": bgp_peer2['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            req = self.new_show_request('bgp-speakers',
                                        bgp_speaker['bgp_speaker']['id'])
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertEqual(2, len(res['bgp_speaker']['peers']))

    def test_add_gateway_network_to_bgp_speaker_without_router(self):
        with self.bgp_speaker() as bgp_speaker:
            data = {'network_id': self._ext_net_id}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_NETWORK_ACTION)
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPOk.code, res.status_int)
            req = self.new_show_request('bgp-speakers',
                                        bgp_speaker['bgp_speaker']['id'])
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertEqual(self._edge_router_id,
                             res['bgp_speaker']['logical_router'])
            self.assertEqual(1, len(res['bgp_speaker']['networks']))

    def test_add_gateway_network_to_bgp_speaker_with_router(self):
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker:
            data = {'network_id': self._ext_net_id}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_NETWORK_ACTION)
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPConflict.code, res.status_int)

    def test_add_private_network_to_bgp_speaker_without_router(self):
        with self.bgp_speaker() as bgp_speaker, self.network() as net:
            data = {'network_id': net['network']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_NETWORK_ACTION)
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_add_gateway_network_without_subnets(self):
        with self.bgp_speaker() as bgp_speaker, self.network() as ext_net:
            self._set_net_external(ext_net['network']['id'])
            data = {'network_id': ext_net['network']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_NETWORK_ACTION)
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_add_gateway_network_with_no_gateway_ip_subnet(self):
        with self.bgp_speaker() as bgp_speaker, self.network() as ext_net:
            self._set_net_external(ext_net['network']['id'])
            self._make_subnet(self.fmt, ext_net, None, '100.64.0.0/24')
            data = {'network_id': ext_net['network']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_NETWORK_ACTION)
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_add_gateway_network_with_no_gateway_ip_port(self):
        with self.bgp_speaker() as bgp_speaker, self.network() as ext_net:
            self._set_net_external(ext_net['network']['id'])
            self._make_subnet(self.fmt, ext_net, '100.64.0.1', '100.64.0.0/24')
            data = {'network_id': ext_net['network']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_NETWORK_ACTION)
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPBadRequest.code, res.status_int)

    def test_remove_gateway_network_from_bgp_speaker_with_peers(self):
        with self.bgp_speaker() as bgp_speaker, self.bgp_peer() as bgp_peer:
            data = {'network_id': self._ext_net_id}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_NETWORK_ACTION)
            req.get_response(self.ext_api)
            data = {"bgp_peer_id": bgp_peer['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            data = {'network_id': self._ext_net_id}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          REMOVE_NETWORK_ACTION)
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPConflict.code, res.status_int)

    def test_remove_gateway_network_from_bgp_speaker(self):
        with self.bgp_speaker() as bgp_speaker, self.bgp_peer():
            data = {'network_id': self._ext_net_id}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_NETWORK_ACTION)
            req.get_response(self.ext_api)
            data = {'network_id': self._ext_net_id}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          REMOVE_NETWORK_ACTION)
            req.get_response(self.ext_api)
            req = self.new_show_request('bgp-speakers',
                                        bgp_speaker['bgp_speaker']['id'])
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertFalse(res['bgp_speaker']['logical_router'])
            self.assertFalse(res['bgp_speaker']['networks'])

    def test_get_advertised_routes_with_single_peer(self):
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker, \
                self.bgp_peer() as bgp_peer:
            data = {"bgp_peer_id": bgp_peer['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            req = self._adver_route_list('bgp-speakers', None,
                                         bgp_speaker['bgp_speaker']['id'],
                                         'get_advertised_routes')
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertEqual(2, len(res['advertised_routes']))

    def test_get_advertised_routes_with_single_peer_and_extra_routes(self):
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker, \
                self.bgp_peer() as bgp_peer:
            data = {"router": {"routes": [{"nexthop": self._port_fixed_ip,
                                           "destination": "20.0.0.0/8"}]}}
            req = self.new_update_request('routers',
                                          data,
                                          self._router_id)
            req.get_response(self.ext_api)
            data = {"bgp_peer_id": bgp_peer['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            req = self._adver_route_list('bgp-speakers', None,
                                         bgp_speaker['bgp_speaker']['id'],
                                         'get_advertised_routes')
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertEqual(3, len(res['advertised_routes']))

    def test_get_advertised_routes_with_mutiple_peers(self):
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker, \
                self.bgp_peer() as bgp_peer, \
                self.bgp_peer(peer_ip=FAKE_PEER_IP2) as bgp_peer2:
            data = {"bgp_peer_id": bgp_peer['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            data = {"bgp_peer_id": bgp_peer2['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            req = self._adver_route_list('bgp-speakers', None,
                                         bgp_speaker['bgp_speaker']['id'],
                                         'get_advertised_routes')
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertEqual(4, len(res['advertised_routes']))

    def test_get_advertised_routes_with_mutiple_peers_and_extra_routes(self):
        with self.bgp_speaker(router_id=self._router_id) as bgp_speaker, \
                self.bgp_peer() as bgp_peer, \
                self.bgp_peer(peer_ip=FAKE_PEER_IP2) as bgp_peer2:
            data = {"router": {"routes": [{"nexthop": self._port_fixed_ip,
                                           "destination": "20.0.0.0/8"}]}}
            req = self.new_update_request('routers',
                                          data,
                                          self._router_id)
            res = req.get_response(self.ext_api)
            data = {"bgp_peer_id": bgp_peer['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            data = {"bgp_peer_id": bgp_peer2['bgp_peer']['id']}
            req = self.new_action_request('bgp-speakers', data,
                                          bgp_speaker['bgp_speaker']['id'],
                                          ADD_BGP_PEER_ACTION)
            req.get_response(self.ext_api)
            req = self._adver_route_list('bgp-speakers', None,
                                         bgp_speaker['bgp_speaker']['id'],
                                         'get_advertised_routes')
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertEqual(6, len(res['advertised_routes']))

    def _adver_route_list(self, resource, data, id, action, fmt=None,
                          subresource=None):
        return self._req(
            'GET',
            resource,
            None,
            fmt,
            id=id,
            action=action,
            subresource=subresource
        )


class BgpTestCaseML2(BgpTestCaseMixin, test_mn_ml2.MidonetPluginML2TestCase):
    pass
