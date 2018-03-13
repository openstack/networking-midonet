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

import mock
from neutron_lib import constants
from neutron_lib.plugins import constants as plugin_const
import webob.exc

from neutron.db import servicetype_db as sdb
from neutron import extensions as nextensions
from neutron.services import provider_configuration as provconf
from neutron.tests.unit.extensions import test_l3 as test_l3_plugin
from neutron_vpnaas import extensions
from neutron_vpnaas.tests.unit.db.vpn import test_vpn_db

from midonet.neutron.tests.unit import test_midonet_plugin_ml2 as test_mn_ml2


MN_DRIVER_KLASS = ('midonet.neutron.services.vpn.service_drivers.'
                   'midonet_ipsec.MidonetIPsecVPNDriver')

extensions_path = ':'.join(extensions.__path__ + nextensions.__path__)
DB_VPN_PLUGIN_KLASS = "neutron_vpnaas.services.vpn.plugin.VPNDriverPlugin"
FLAVOR_PLUGIN_KLASS = "neutron.services.flavors.flavors_plugin.FlavorsPlugin"


class VPNTestExtensionManager(test_l3_plugin.L3TestExtensionManager):

    def get_resources(self):
        res = super(VPNTestExtensionManager, self).get_resources()
        return res + extensions.vpnaas.Vpnaas.get_resources()

    def get_actions(self):
        return []

    def get_request_extensions(self):
        return []


class VPNTestCaseMixin(test_vpn_db.VPNTestMixin,
                       test_l3_plugin.L3NatTestCaseMixin):
    def setUp(self):
        service_plugins = {
            'vpn_plugin_name': DB_VPN_PLUGIN_KLASS,
            'flavors_plugin': FLAVOR_PLUGIN_KLASS}
        vpnaas_provider = (plugin_const.VPN + ':vpnaas:' + MN_DRIVER_KLASS
                           + ':default')
        mock.patch.object(provconf.NeutronModule, 'service_providers',
                          return_value=[vpnaas_provider]).start()
        manager = sdb.ServiceTypeManager.get_instance()
        manager.add_provider_configuration(
            plugin_const.VPN, provconf.ProviderConfiguration())

        super(VPNTestCaseMixin, self).setUp(service_plugins=service_plugins,
                                            ext_mgr=VPNTestExtensionManager())

    def test_create_vpn_service(self):
        with self.vpnservice() as vpnservice:
            req = self.new_show_request(
                'vpnservices', vpnservice['vpnservice']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertEqual(constants.ACTIVE, res['vpnservice']['status'])

    def test_create_vpn_service_error_delete_neutron_resource(self):
        self.client_mock.create_vpn_service.side_effect = Exception(
            "Fake Error")
        with self.subnet(cidr='10.2.0.0/24') as subnet, \
                self.router() as router:
            try:
                with self.vpnservice(subnet=subnet, router=router,
                                     do_delete=False):
                    # Shouldn't be reached
                    self.assertTrue(False)
            except webob.exc.HTTPClientError:
                pass
            req = self.new_list_request('vpnservices')
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertFalse(res['vpnservices'])

    def test_update_vpn_service(self):
        with self.vpnservice() as vpnservice:
            data = {'vpnservice': {'name': 'vpnservice2'}}
            vpnservice_id = vpnservice['vpnservice']['id']
            req = self.new_update_request('vpnservices', data, vpnservice_id)
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertEqual('vpnservice2', res['vpnservice']['name'])
            self.assertEqual(
                'vpnservice2',
                self.client_mock.update_vpn_service.call_args[0][2]['name'])

    def test_update_vpn_service_error_change_neutron_resource_status(self):
        self.client_mock.update_vpn_service.side_effect = Exception(
            "Fake Error")
        with self.vpnservice() as vpnservice:
            data = {'vpnservice': {'name': 'vpnservice2'}}
            vpnservice_id = vpnservice['vpnservice']['id']
            req = self.new_update_request('vpnservices', data, vpnservice_id)
            res = req.get_response(self.ext_api)
            self.assertEqual(500, res.status_int)

            req = self.new_show_request('vpnservices', vpnservice_id)
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertEqual(constants.ERROR, res['vpnservice']['status'])

    def test_delete_vpnservice(self):
        """Test case to delete a vpnservice."""
        with self.vpnservice(name='vpnserver',
                             do_delete=False) as vpnservice:
            req = self.new_delete_request('vpnservices',
                                          vpnservice['vpnservice']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(204, res.status_int)

    def test_delete_vpn_service_error_delete_neutron_resource(self):
        self.client_mock.delete_vpn_service_side_effect = Exception(
            "Fake Error")
        self.test_delete_vpnservice()
        # check the resource deleted in Neutron DB
        req = self.new_list_request('vpnservices')
        res = self.deserialize(self.fmt, req.get_response(self.ext_api))
        self.assertFalse(res['vpnservices'])

    def test_create_ipsec_site_connection(self):
        with self.ipsec_site_connection() as ipsec_site_connection:
            req = self.new_show_request(
                'ipsec-site-connections',
                ipsec_site_connection['ipsec_site_connection']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertEqual(
                constants.ACTIVE,
                res['ipsec_site_connection']['status'])

    def test_create_two_ipsec_site_connections_one_vpnservice(self):
        with self.vpnservice() as vpnservice, \
                self.ipsec_site_connection(vpnservice=vpnservice), \
                self.ipsec_site_connection(vpnservice=vpnservice,
                                           peer_address='192.168.1.11',
                                           peer_id='192.168.1.11',
                                           peer_cidrs=['10.0.11.0/24']):
            # Check there are two ipsec site connections
            req = self.new_list_request('ipsec-site-connections')
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertTrue(len(res['ipsec_site_connections']) == 2)
            self.assertNotEqual(res['ipsec_site_connections'][0]['id'],
                                res['ipsec_site_connections'][1]['id'])

            for ipsec_site_connection in res['ipsec_site_connections']:
                # Check that the associated vpnservice is the correct one
                req = self.new_show_request(
                    'vpnservices', ipsec_site_connection['vpnservice_id'])
                res = self.deserialize(self.fmt,
                                       req.get_response(self.ext_api))
                self.assertEqual(vpnservice['vpnservice']['id'],
                                 res['vpnservice']['id'])

                self.assertEqual(constants.ACTIVE,
                                 ipsec_site_connection['status'])

    def test_create_ipsec_site_connection_error_delete_neutron_resource(self):
        self.client_mock.create_ipsec_site_conn.side_effect = Exception(
            "Fake Error")
        with self.vpnservice() as vpnservice, \
                self.ikepolicy() as ikepolicy, \
                self.ipsecpolicy() as ipsecpolicy:
            self._create_ipsec_site_connection(
                self.fmt, 'site_conn2',
                peer_cidrs='192.168.101.0/24',
                vpnservice_id=vpnservice['vpnservice']['id'],
                ikepolicy_id=ikepolicy['ikepolicy']['id'],
                ipsecpolicy_id=ipsecpolicy['ipsecpolicy']['id'],
                expected_res_status=500)
            req = self.new_list_request('ipsec-site-connections')
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertFalse(res['ipsec_site_connections'])

    def test_update_ipsec_site_connection(self):
        with self.ipsec_site_connection() as ipsec_site_connection:
            data = {'ipsec_site_connection': {'mtu': '1300'}}
            ipsec_site_conn_id = (
                ipsec_site_connection['ipsec_site_connection']['id'])
            req = self.new_update_request(
                'ipsec-site-connections', data, ipsec_site_conn_id)
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertEqual(1300, res['ipsec_site_connection']['mtu'])
            self.assertEqual(
                1300,
                self.client_mock.update_ipsec_site_conn.call_args[0][2]['mtu'])

    def test_update_ipsec_site_connection_error(self):
        self.client_mock.update_ipsec_site_conn.side_effect = Exception(
            "Fake Error")
        with self.ipsec_site_connection() as ipsec_site_connection:
            data = {'ipsec_site_connection': {'mtu': '1300'}}
            ipsec_site_conn_id = (
                ipsec_site_connection['ipsec_site_connection']['id'])
            req = self.new_update_request('ipsec-site-connections', data,
                                          ipsec_site_conn_id)
            res = req.get_response(self.ext_api)
            self.assertEqual(500, res.status_int)

            req = self.new_show_request(
                'ipsec-site-connections',
                ipsec_site_conn_id)
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertEqual(
                constants.ERROR,
                res['ipsec_site_connection']['status'])

    def test_delete_ipsec_site_connection(self):
        with self.ipsec_site_connection(
                name="site_conn2", do_delete=False) as ipsec_site_connection:
            ipsec_site_conn_id = \
                ipsec_site_connection['ipsec_site_connection']['id']
            req = self.new_delete_request(
                'ipsec-site-connections', ipsec_site_conn_id)
            res = req.get_response(self.ext_api)
            self.assertEqual(204, res.status_int)

    def test_delete_ipsec_site_connection_error(self):
        self.client_mock.delete_ipsec_site_conn.side_effect = Exception(
            "Fake Error")
        self.test_delete_ipsec_site_connection()
        req = self.new_list_request('ipsec-site-connections')
        res = self.deserialize(self.fmt, req.get_response(self.ext_api))
        self.assertFalse(res['ipsec_site_connections'])


class VPNTestCaseML2(VPNTestCaseMixin,
                     test_mn_ml2.MidonetPluginML2TestCase):
    pass
