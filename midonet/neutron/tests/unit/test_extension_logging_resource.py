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
from neutron.tests.unit.extensions import test_l3
from neutron_fwaas.tests.unit.services.firewall import test_fwaas_plugin as tfp

from midonet.neutron import extensions as midoextensions
from midonet.neutron.extensions import logging_resource as log_res_ext
from midonet.neutron.tests.unit import test_midonet_plugin_ml2 as test_mn_ml2


LOGGING_PLUGIN_KLASS = 'midonet_logging_resource'
extensions_path = ':'.join(midoextensions.__path__)

FAKE_LOG_RES_NAME = 'log_res'
NEW_LOG_RES_NAME = 'new_log_res'
FAKE_LOG_RES_DESC = 'log_res_description'
NEW_LOG_RES_DESC = 'new_log_res_description'
ENABLED_TRUE = True
ENABLED_FALSE = False
FAKE_FW_LOG_DESC = 'fw_log_description'
NEW_FW_LOG_DESC = 'new_fw_log_description'
NOT_FOUND_FW_UUID = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
NOT_FOUND_LOG_RES_UUID = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
NOT_FOUND_FW_LOG_UUID = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'


class LoggingResourceTestExtensionManager(tfp.FirewallTestExtensionManager):

    def get_resources(self):
        res = super(LoggingResourceTestExtensionManager,
                    self).get_resources()
        return res + log_res_ext.Logging_resource.get_resources()

    def get_actions(self):
        return []

    def get_request_extensions(self):
        return []


class LoggingResourceTestCaseMixin(test_l3.L3NatTestCaseMixin):

    def setUp(self, plugin=None, service_plugins=None, ext_mgr=None):

        service_plugins = {
            'logging_resource_plugin_name': LOGGING_PLUGIN_KLASS,
            'fwaas_plugin_name': 'midonet_firewall'}

        log_res_mgr = LoggingResourceTestExtensionManager()
        super(LoggingResourceTestCaseMixin, self).setUp(
            service_plugins=service_plugins, ext_mgr=log_res_mgr)
        self.ext_api = test_ex.setup_extensions_middleware(log_res_mgr)

        router1 = self._make_router(self.fmt, uuidutils.generate_uuid(),
                                    'router1', True)
        self._router_id1 = router1['router']['id']
        router2 = self._make_router(self.fmt, uuidutils.generate_uuid(),
                                    'router2', True)
        self._router_id2 = router2['router']['id']
        self._tenant_id1 = uuidutils.generate_uuid()
        self._tenant_id2 = uuidutils.generate_uuid()
        fw1 = self._create_firewall(self._tenant_id1)
        self._fw_id1 = fw1['firewall']['id']
        fw2 = self._create_firewall(self._tenant_id1)
        self._fw_id2 = fw2['firewall']['id']

    @contextlib.contextmanager
    def firewall(self, tenant_id):
        firewall = self._create_firewall(tenant_id)
        yield firewall

    def _create_firewall(self, tenant_id):
        fw_policy_data = {'firewall_policy': {'tenant_id': tenant_id,
                                              'name': 'fw_policy'}}
        req = self.new_create_request('fw/firewall_policies', fw_policy_data,
                                      'json')
        res = self.deserialize(self.fmt, req.get_response(self.ext_api))
        firewall_data = {'firewall': {
            'name': 'fw',
            'firewall_policy_id': res['firewall_policy']['id'],
            'tenant_id': tenant_id,
            'shared': False}}
        req = self.new_create_request('fw/firewalls', firewall_data, 'json')
        return self.deserialize(self.fmt, req.get_response(self.ext_api))

    @contextlib.contextmanager
    def logging_resource(self, name=FAKE_LOG_RES_NAME, tenant_id=None,
                         desc=FAKE_LOG_RES_DESC, enabled=ENABLED_FALSE):
        logging_resource = self._make_logging_resource(name, tenant_id,
                                                       desc, enabled)
        yield logging_resource

    def _make_logging_resource(self, name, tenant_id, desc, enabled):
        res = self._create_logging_resource(name, tenant_id, desc, enabled)
        if res.status_int >= webob.exc.HTTPBadRequest.code:
            raise webob.exc.HTTPClientError(code=res.status_int)
        return self.deserialize(self.fmt, res)

    def _create_logging_resource(self, name=FAKE_LOG_RES_NAME, tenant_id=None,
                                 desc=FAKE_LOG_RES_DESC,
                                 enabled=ENABLED_FALSE):
        data = {'logging_resource': {'tenant_id': tenant_id or self._tenant_id,
                                     'name': name,
                                     'description': desc,
                                     'enabled': enabled}}
        log_res_req = self.new_create_request('logging/logging_resources',
                                              data, self.fmt)
        return log_res_req.get_response(self.ext_api)

    @contextlib.contextmanager
    def firewall_log(self, log_res_id, firewall_id=None,
                     desc=FAKE_FW_LOG_DESC, tenant_id=None,
                     fw_event=log_res_ext.FW_EVENT_ALL):
        firewall_log = self._make_firewall_log(log_res_id, firewall_id,
                                               desc, tenant_id, fw_event)
        yield firewall_log

    def _make_firewall_log(self, log_res_id, firewall_id, desc,
                           tenant_id, fw_event):
        res = self._create_firewall_log(log_res_id, firewall_id,
                                        desc, tenant_id, fw_event)
        if res.status_int >= webob.exc.HTTPBadRequest.code:
            raise webob.exc.HTTPClientError(code=res.status_int)
        return self.deserialize(self.fmt, res)

    def _create_firewall_log(self, log_res_id, firewall_id=None,
                             desc=FAKE_FW_LOG_DESC, tenant_id=None,
                             fw_event=log_res_ext.FW_EVENT_ALL):
        data = {'firewall_log': {'tenant_id': tenant_id or self._tenant_id,
                                 'description': desc,
                                 'fw_event': fw_event}}
        if firewall_id:
            data['firewall_log']['firewall_id'] = firewall_id
        f_log_req = self.new_create_request('logging/logging_resources/'
                                            + log_res_id + '/firewall_logs',
                                            data, self.fmt)
        return f_log_req.get_response(self.ext_api)

    def test_create_logging_resource(self):
        expected = {'name': FAKE_LOG_RES_NAME,
                    'description': FAKE_LOG_RES_DESC,
                    'enabled': ENABLED_FALSE,
                    'firewall_logs': []}
        with self.logging_resource() as log_res:
            self.assertDictSupersetOf(expected, log_res['logging_resource'])

    def test_show_logging_resource(self):
        expected = {'name': FAKE_LOG_RES_NAME,
                    'description': FAKE_LOG_RES_DESC,
                    'enabled': ENABLED_FALSE,
                    'firewall_logs': []}
        with self.logging_resource() as log_res:
            req = self.new_show_request('logging/logging_resources',
                                        log_res['logging_resource']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertDictSupersetOf(expected, res['logging_resource'])

    def test_show_logging_resource_not_found(self):
        req = self.new_show_request('logging/logging_resources',
                                    NOT_FOUND_LOG_RES_UUID)
        res = req.get_response(self.ext_api)
        self.assertEqual(webob.exc.HTTPNotFound.code, res.status_int)

    def test_list_logging_resource(self):
        with self.logging_resource(), self.logging_resource():
            req = self.new_list_request('logging/logging_resources')
            res = self.deserialize(
                self.fmt, req.get_response(self.ext_api))
            self.assertEqual(2, len(res['logging_resources']))

    def test_update_logging_resource_without_firewall_log(self):
        expected = {'name': NEW_LOG_RES_NAME,
                    'description': NEW_LOG_RES_DESC,
                    'enabled': ENABLED_TRUE}
        with self.logging_resource() as log_res:
            data = {'logging_resource': {'name': NEW_LOG_RES_NAME,
                                         'description': NEW_LOG_RES_DESC,
                                         'enabled': ENABLED_TRUE}}
            req = self.new_update_request('logging/logging_resources',
                                          data,
                                          log_res['logging_resource']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertDictSupersetOf(expected, res['logging_resource'])
            self.client_mock.update_logging_resource_postcommit. \
                assert_not_called()

    def test_update_logging_resource_with_firewall_log(self):
        expected = {'name': NEW_LOG_RES_NAME,
                    'description': NEW_LOG_RES_DESC,
                    'enabled': ENABLED_TRUE}
        with self.logging_resource() as log_res, \
                self.firewall_log(log_res['logging_resource']['id'],
                                  firewall_id=self._fw_id1):
            data = {'logging_resource': {'name': NEW_LOG_RES_NAME,
                                         'description': NEW_LOG_RES_DESC,
                                         'enabled': ENABLED_TRUE}}
            req = self.new_update_request('logging/logging_resources',
                                          data,
                                          log_res['logging_resource']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertDictSupersetOf(expected, res['logging_resource'])
            self.client_mock.update_logging_resource_postcommit.assert_called()

    def test_update_logging_resource_error_rollback_neutron_resource(self):
        self.client_mock.update_logging_resource_postcommit.side_effect = (
            Exception("Fake Error"))
        with self.logging_resource() as log_res, \
                self.firewall_log(log_res['logging_resource']['id'],
                                  firewall_id=self._fw_id1):
            data = {'logging_resource': {'enabled': ENABLED_TRUE}}
            req = self.new_update_request('logging/logging_resources',
                                          data,
                                          log_res['logging_resource']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPInternalServerError.code,
                             res.status_int)
            # ensure enabled are not changed.
            expected = {'enabled': ENABLED_FALSE}
            req = self.new_show_request('logging/logging_resources',
                                        log_res['logging_resource']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertDictSupersetOf(expected, res['logging_resource'])

    def test_delete_logging_resource(self):
        with self.logging_resource() as log_res:
            req = self.new_delete_request('logging/logging_resources',
                                          log_res['logging_resource']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPNoContent.code, res.status_int)

    def test_delete_logging_resource_with_firewall_logs(self):
        with self.logging_resource() as log_res, \
                self.firewall_log(log_res['logging_resource']['id'],
                                  firewall_id=self._fw_id1), \
                self.firewall_log(log_res['logging_resource']['id'],
                                  firewall_id=self._fw_id2):
            req = self.new_delete_request('logging/logging_resources',
                                          log_res['logging_resource']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPNoContent.code, res.status_int)

    def test_delete_logging_resource_error_delete_neutron_resource(self):
        self.client_mock.delete_logging_resource_postcommit.side_effect = (
            Exception("Fake Error"))
        with self.logging_resource() as log_res:
            req = self.new_delete_request('logging/logging_resources',
                                          log_res['logging_resource']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPInternalServerError.code,
                             res.status_int)
            # check the resource deleted in Neutron DB
            req = self.new_list_request('logging/logging_resources')
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertFalse(res['logging_resources'])

    def test_create_firewall_log(self):
        expected = {'description': FAKE_FW_LOG_DESC,
                    'fw_event': log_res_ext.FW_EVENT_ALL,
                    'firewall_id': self._fw_id1}
        with self.logging_resource() as log_res, \
                self.firewall_log(log_res['logging_resource']['id'],
                                  firewall_id=self._fw_id1) as f_log:
            self.assertDictSupersetOf(expected, f_log['firewall_log'])

    def test_create_firewall_log_diff_log_res_diff_tenant_same_firewall(self):
        with self.logging_resource() as log_res, \
                self.logging_resource(
                    tenant_id=self._tenant_id2) as log_res2, \
                self.firewall_log(log_res['logging_resource']['id'],
                                  firewall_id=self._fw_id1):
            res = self._create_firewall_log(
                log_res2['logging_resource']['id'],
                firewall_id=self._fw_id1,
                tenant_id=self._tenant_id2)
            self.assertEqual(webob.exc.HTTPCreated.code, res.status_int)

    def test_create_firewall_log_with_not_found_firewall(self):
        with self.logging_resource() as log_res:
            res = self._create_firewall_log(
                log_res['logging_resource']['id'],
                firewall_id=NOT_FOUND_FW_UUID)
            self.assertEqual(webob.exc.HTTPNotFound.code, res.status_int)

    def test_create_firewall_log_in_same_log_res_with_same_firewall(self):
        with self.logging_resource() as log_res, \
                self.firewall_log(log_res['logging_resource']['id'],
                                  firewall_id=self._fw_id1):
            res = self._create_firewall_log(
                log_res['logging_resource']['id'],
                firewall_id=self._fw_id1)
            self.assertEqual(webob.exc.HTTPCreated.code, res.status_int)

    def test_create_firewall_log_in_diff_log_res_with_same_firewall(self):
        with self.logging_resource() as log_res, \
                self.logging_resource() as log_res2, \
                self.firewall_log(log_res['logging_resource']['id'],
                                  firewall_id=self._fw_id1):
            res = self._create_firewall_log(
                log_res2['logging_resource']['id'],
                firewall_id=self._fw_id1)
            self.assertEqual(webob.exc.HTTPCreated.code, res.status_int)

    def test_create_firewall_log_error_delete_neutron_resource(self):
        self.client_mock.create_firewall_log_postcommit.side_effect = (
            Exception("Fake Error"))
        with self.logging_resource() as log_res:
            try:
                with self.firewall_log(log_res['logging_resource']['id']):
                    self.assertTrue(False)
            except webob.exc.HTTPClientError:
                pass
            req = self.new_list_request('logging/logging_resources/'
                                        + log_res['logging_resource']['id']
                                        + '/firewall_logs')
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertFalse(res['firewall_logs'])

    def test_update_firewall_log(self):
        expected = {'description': NEW_FW_LOG_DESC,
                    'fw_event': log_res_ext.FW_EVENT_DROP}
        with self.logging_resource() as log_res, \
                self.firewall_log(log_res['logging_resource']['id'],
                                  firewall_id=self._fw_id1) as f_log:
            data = {'firewall_log': {'description': NEW_FW_LOG_DESC,
                                     'fw_event': log_res_ext.FW_EVENT_DROP}}
            req = self.new_update_request('logging/logging_resources/'
                                          + log_res['logging_resource']['id']
                                          + '/firewall_logs',
                                          data,
                                          f_log['firewall_log']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertDictSupersetOf(expected, res['firewall_log'])

    def test_update_firewall_log_error_rollback_neutron_resource(self):
        self.client_mock.update_firewall_log_postcommit.side_effect = (
            Exception("Fake Error"))
        with self.logging_resource() as log_res, \
                self.firewall_log(log_res['logging_resource']['id'],
                                  firewall_id=self._fw_id1) as f_log:
            data = {'firewall_log': {'fw_event': log_res_ext.FW_EVENT_DROP}}
            req = self.new_update_request('logging/logging_resources/'
                                          + log_res['logging_resource']['id']
                                          + '/firewall_logs',
                                          data,
                                          f_log['firewall_log']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPInternalServerError.code,
                             res.status_int)
            # ensure fw_event is not changed.
            expected = {'fw_event': log_res_ext.FW_EVENT_ALL}
            req = self.new_show_request('logging/logging_resources/'
                                        + log_res['logging_resource']['id']
                                        + '/firewall_logs',
                                        f_log['firewall_log']['id'])
            res = self.deserialize(self.fmt, req.get_response(self.ext_api))
            self.assertDictSupersetOf(expected, res['firewall_log'])

    def test_show_firewall_log(self):
        expected = {'description': FAKE_FW_LOG_DESC,
                    'fw_event': log_res_ext.FW_EVENT_ALL,
                    'firewall_id': self._fw_id1}
        with self.logging_resource() as log_res, \
                self.firewall_log(log_res['logging_resource']['id'],
                                  firewall_id=self._fw_id1) as f_log:
            req = self.new_show_request('logging/logging_resources/'
                                        + log_res['logging_resource']['id']
                                        + '/firewall_logs',
                                        f_log['firewall_log']['id'])
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertDictSupersetOf(expected, res['firewall_log'])

    def test_show_firewall_log_not_found(self):
        with self.logging_resource() as log_res:
            req = self.new_show_request('logging/logging_resources/'
                                        + log_res['logging_resource']['id']
                                        + '/firewall_logs',
                                        NOT_FOUND_FW_LOG_UUID)
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPNotFound.code, res.status_int)

    def test_list_firewall_log(self):
        with self.logging_resource() as log_res, \
                self.firewall_log(log_res['logging_resource']['id'],
                                  firewall_id=self._fw_id1), \
                self.firewall_log(log_res['logging_resource']['id'],
                                  firewall_id=self._fw_id2):
            req = self.new_list_request('logging/logging_resources/'
                                        + log_res['logging_resource']['id']
                                        + '/firewall_logs')
            res = self.deserialize(
                self.fmt, req.get_response(self.ext_api))
            self.assertEqual(2, len(res['firewall_logs']))

    def test_delete_firewall_log(self):
        with self.logging_resource() as log_res, \
                self.firewall_log(log_res['logging_resource']['id'],
                                  firewall_id=self._fw_id1) as f_log:
            req = self.new_delete_request('logging/logging_resources/'
                                          + log_res['logging_resource']['id']
                                          + '/firewall_logs',
                                          f_log['firewall_log']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPNoContent.code, res.status_int)

    def test_delete_firewall_log_error_delete_neutron_resource(self):
        self.client_mock.delete_firewall_log_postcommit.side_effect = (
            Exception("Fake Error"))
        with self.logging_resource() as log_res, \
                self.firewall_log(log_res['logging_resource']['id'],
                                  firewall_id=self._fw_id1) as f_log:
            req = self.new_delete_request('logging/logging_resources/'
                                          + log_res['logging_resource']['id']
                                          + '/firewall_logs',
                                          f_log['firewall_log']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPInternalServerError.code,
                             res.status_int)
            # check the resource deleted in Neutron DB
            req = self.new_list_request('logging/logging_resources')
            res = self.deserialize(self.fmt,
                                   req.get_response(self.ext_api))
            self.assertEqual(
                [],
                res['logging_resources'][0]['firewall_logs'])

    def test_delete_firewall_with_firewall_log(self):
        with self.logging_resource() as log_res, \
                self.firewall(self._tenant_id) as fw, \
                self.firewall_log(log_res['logging_resource']['id'],
                                  firewall_id=fw['firewall']['id']) as f_log:
            req = self.new_delete_request('fw/firewalls',
                                          fw['firewall']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPNoContent.code, res.status_int)
            req = self.new_show_request('logging/logging_resources/'
                                        + log_res['logging_resource']['id']
                                        + '/firewall_logs',
                                        f_log['firewall_log']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPNotFound.code, res.status_int)

    def test_delete_firewall_with_multiple_firewall_logs(self):
        with self.logging_resource() as log_res1, \
                self.logging_resource(
                    tenant_id=self._tenant_id2) as log_res2, \
                self.firewall(self._tenant_id) as fw, \
                self.firewall_log(
                    log_res1['logging_resource']['id'],
                    firewall_id=fw['firewall']['id']) as f_log1, \
                self.firewall_log(log_res2['logging_resource']['id'],
                                  firewall_id=fw['firewall']['id'],
                                  tenant_id=self._tenant_id2) as f_log2:
            req = self.new_delete_request('fw/firewalls',
                                          fw['firewall']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPNoContent.code, res.status_int)
            req = self.new_show_request('logging/logging_resources/'
                                        + log_res1['logging_resource']['id']
                                        + '/firewall_logs',
                                        f_log1['firewall_log']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPNotFound.code, res.status_int)
            req = self.new_show_request('logging/logging_resources/'
                                        + log_res2['logging_resource']['id']
                                        + '/firewall_logs',
                                        f_log2['firewall_log']['id'])
            res = req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPNotFound.code, res.status_int)


class LoggingResourceTestCaseML2(LoggingResourceTestCaseMixin,
                                 test_mn_ml2.MidonetPluginML2TestCase):
    pass
