# Copyright (C) 2016 Midokura SARL
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from neutron.services.qos.notification_drivers import qos_base

from midonet.neutron.client import base as c_base


LOG = logging.getLogger(__name__)


class MidoNetQosServiceNotificationDriver(
        qos_base.QosServiceNotificationDriverBase):

    def __init__(self):
        super(MidoNetQosServiceNotificationDriver, self).__init__()
        self._client = c_base.load_client(cfg.CONF.MIDONET)

    def get_description(self):
        return "MidoNet QoS notification driver"

    @log_helpers.log_method_call
    def create_policy(self, context, policy):
        self._client.create_qos_policy(context, policy)

    @log_helpers.log_method_call
    def update_policy(self, context, policy):
        self._client.update_qos_policy(context, policy)

    @log_helpers.log_method_call
    def delete_policy(self, context, policy):
        self._client.delete_qos_policy(context, policy)
