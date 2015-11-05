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
import uuid
import webob.exc

from midonet.neutron.extensions import agent_membership as ext_am
from midonet.neutron.tests.unit import test_midonet_plugin_v2 as test_mn

from neutron.tests.unit.api import test_extensions as test_ex
from oslo_utils import uuidutils

FAKE_AGENT_ID = uuidutils.generate_uuid()
FAKE_IP = '10.0.0.3'


class AgentMembershipExtensionManager(object):

    def get_resources(self):
        return ext_am.Agent_membership.get_resources()

    def get_actions(self):
        return []

    def get_request_extensions(self):
        return []


class AgentMembershipTestCase(test_mn.MidonetPluginV2TestCase):

    def setUp(self, plugin=None, ext_mgr=None):
        ext_mgr = AgentMembershipExtensionManager()
        super(AgentMembershipTestCase, self).setUp()
        self.ext_api = test_ex.setup_extensions_middleware(ext_mgr)

    def _create_agent_membership(self, agent_id, ip_address):
        data = {'agent_membership': {'id': agent_id,
                                     'tenant_id': str(uuid.uuid4()),
                                     'ip_address': ip_address}}
        am_req = self.new_create_request('agent_memberships', data, self.fmt)
        return am_req.get_response(self.ext_api)

    def _make_agent_membership(self, agent_id, ip_address):
        res = self._create_agent_membership(agent_id, ip_address)
        if res.status_int >= webob.exc.HTTPBadRequest.code:
            raise webob.exc.HTTPClientError(code=res.status_int)
        return self.deserialize(self.fmt, res)

    @contextlib.contextmanager
    def agent_membership(self, agent_id=FAKE_AGENT_ID, ip_address=FAKE_IP):
        am = self._make_agent_membership(agent_id, ip_address)
        yield am

    def test_create_agent_membership(self):
        expected = {'id': FAKE_AGENT_ID, 'ip_address': FAKE_IP}
        with self.agent_membership() as am:
            for k, v in expected.items():
                self.assertEqual(v, am['agent_membership'][k])

    def test_delete_agent_membership(self):
        with self.agent_membership() as am:
            req = self.new_delete_request('agent_memberships',
                                          am['agent_membership']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPNoContent.code, res.status_int)

    def test_show_agent_membership(self):
        expected = {'id': FAKE_AGENT_ID, 'ip_address': FAKE_IP}
        with self.agent_membership() as am:
            req = self.new_show_request('agent_memberships',
                                        am['agent_membership']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            for k, v in expected.items():
                self.assertEqual(v, res['agent_membership'][k])

    def test_list_agent_memberships(self):
        with self.agent_membership():
            with self.agent_membership(uuidutils.generate_uuid(), '10.0.0.4'):
                req = self.new_list_request('agent_memberships')
                res = self.deserialize(
                    self.fmt, req.get_response(self.ext_api))
                self.assertEqual(2, len(res['agent_memberships']))
