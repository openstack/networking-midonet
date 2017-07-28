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

import mock

from neutron.tests import base

from midonet.neutron.services.qos import driver as qos_driver


class QoSDriverTestCase(base.BaseTestCase):
    def setUp(self):
        super(QoSDriverTestCase, self).setUp()
        self._mock_client = mock.Mock()
        with mock.patch("midonet.neutron.client.base.load_client",
                        return_value=self._mock_client), \
            mock.patch(
                "neutron_lib.services.qos.base.DriverBase.__init__"):
            self._driver = qos_driver.MidoNetQosDriver()

    def test_qos_policy_create(self):
        mock_context = mock.Mock()
        mock_policy_obj = mock.Mock()
        self._driver.create_policy(mock_context, mock_policy_obj)
        self.assertEqual([
            mock.call.create_qos_policy(mock_context, mock_policy_obj),
        ], self._mock_client.mock_calls)

    def test_qos_policy_update(self):
        mock_context = mock.Mock()
        mock_policy_obj = mock.Mock()
        self._driver.update_policy(mock_context, mock_policy_obj)
        self.assertEqual([
            mock.call.update_qos_policy(mock_context, mock_policy_obj),
        ], self._mock_client.mock_calls)

    def test_qos_policy_delete(self):
        mock_context = mock.Mock()
        mock_policy_obj = mock.Mock()
        self._driver.delete_policy(mock_context, mock_policy_obj)
        self.assertEqual([
            mock.call.delete_qos_policy(mock_context, mock_policy_obj),
        ], self._mock_client.mock_calls)
