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

from neutron_lib import constants as n_const

from neutron_fwaas.tests.unit.services.firewall import test_fwaas_plugin as tfp

from midonet.neutron.tests.unit import test_midonet_plugin_ml2 as test_mn_ml2

# Overwrite the FWaaS plugin constant so that the MidoNet FWaaS plugin gets
# loaded when the tests run.
tfp.FW_PLUGIN_KLASS = "midonet_firewall"


class FirewallTestCaseMixin(object):

    def test_create_sets_status_to_active(self):
        with self.router() as router:
            router_ids = [router['router']['id']]
            with self.firewall(router_ids=router_ids) as firewall:
                # Verify that the firewall is ACTIVE
                fw_id = firewall['firewall']['id']
                req = self.new_show_request('firewalls', fw_id)
                res = self.deserialize(self.fmt,
                                       req.get_response(self.ext_api))
                status = res['firewall']['status']
                self.assertEqual(n_const.ACTIVE, status)

    def test_create_sets_status_to_inactive(self):
        with self.firewall(router_ids=[]) as firewall:
            # Verify that the firewall is INACTIVE
            fw_id = firewall['firewall']['id']
            req = self.new_show_request('firewalls', fw_id)
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            status = res['firewall']['status']
            self.assertEqual(n_const.INACTIVE, status)

    def test_create_firewall_error_deletes_firewall(self):
        self.client_mock.create_firewall.side_effect = Exception("Fake Error")
        with self.router() as router:
            router_ids = [router['router']['id']]

            self._create_firewall(self.fmt, "fw_test", "fw_desc",
                                  router_ids=router_ids,
                                  expected_res_status=500)

            # Verify that the firewall was deleted from DB
            req = self.new_list_request('firewalls')
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertFalse(res['firewalls'])

    def test_update_sets_status_to_active(self):
        with self.router() as router:
            router_ids = [router['router']['id']]
            with self.firewall(router_ids=router_ids) as firewall:

                fw_id = firewall['firewall']['id']
                data = {'firewall': {'name': 'foo'}}
                req = self.new_update_request('firewalls', data, fw_id)
                res = self.deserialize(self.fmt,
                                       req.get_response(self.ext_api))

                # Verify that the firewall is ACTIVE
                req = self.new_show_request('firewalls', fw_id)
                res = self.deserialize(self.fmt,
                                       req.get_response(self.ext_api))
                status = res['firewall']['status']
                self.assertEqual(n_const.ACTIVE, status)

    def test_update_sets_status_to_inactive(self):
        with self.router() as router:
            router_ids = [router['router']['id']]
            with self.firewall(router_ids=router_ids) as firewall:

                fw_id = firewall['firewall']['id']
                data = {'firewall': {'router_ids': []}}
                req = self.new_update_request('firewalls', data, fw_id)
                res = self.deserialize(self.fmt,
                                       req.get_response(self.ext_api))

                # Verify that the firewall is INACTIVE
                req = self.new_show_request('firewalls', fw_id)
                res = self.deserialize(self.fmt,
                                       req.get_response(self.ext_api))
                status = res['firewall']['status']
                self.assertEqual(n_const.INACTIVE, status)

    def test_update_firewall_error_sets_status_to_error(self):
        self.client_mock.update_firewall.side_effect = Exception("Fake Error")
        with self.router() as router:
            router_ids = [router['router']['id']]
            with self.firewall(router_ids=router_ids) as firewall:

                # Verify that an error while updating sets status to ERROR
                fw_id = firewall['firewall']['id']
                data = {'firewall': {'name': 'foo'}}
                req = self.new_update_request('firewalls', data, fw_id)
                res = req.get_response(self.ext_api)
                self.assertEqual(500, res.status_int)

                req = self.new_show_request('firewalls', fw_id)
                res = self.deserialize(self.fmt,
                                       req.get_response(self.ext_api))
                status = res['firewall']['status']
                self.assertEqual(n_const.ERROR, status)

    def test_delete_error_in_midonet_does_not_delete_firewall(self):
        self.client_mock.delete_firewall.side_effect = Exception("Fake Error")
        with self.router() as router:
            router_ids = [router['router']['id']]
            with self.firewall(router_ids=router_ids,
                               do_delete=False) as firewall:

                # Verify that deletion error from midonet side does not end up
                # deleting the firewall in DB
                fw_id = firewall['firewall']['id']
                req = self.new_delete_request('firewalls', fw_id)
                res = req.get_response(self.ext_api)
                self.assertEqual(500, res.status_int)

                req = self.new_show_request('firewalls', fw_id)
                res = req.get_response(self.ext_api)
                self.assertEqual(200, res.status_int)

    # The following tests do not apply to midonet since the firewall resources
    # are not in PENDING_CREATE state upon creation.

    def test_update_firewall_fails_when_firewall_pending(self):
        pass

    def test_update_firewall_policy_fails_when_firewall_pending(self):
        pass

    def test_update_firewall_rule_fails_when_firewall_pending(self):
        pass

    def test_list_firewalls_with_filtering(self):
        pass


class FirewallTestCaseML2(FirewallTestCaseMixin,
                          tfp.TestFirewallPluginBase,
                          test_mn_ml2.MidonetPluginML2TestCase):
    pass
