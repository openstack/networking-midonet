# Copyright (C) 2016,2017 Midokura SARL
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

from neutron_lib.api.definitions import portbindings
from neutron_lib import constants
from neutron_lib.db import constants as db_consts
from neutron_lib.services.qos import base
from neutron_lib.services.qos import constants as qos_consts
from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from midonet.neutron.client import base as c_base
from midonet.neutron.common import config  # noqa
from midonet.neutron.common import constants as m_const


LOG = logging.getLogger(__name__)


DRIVER = None


SUPPORTED_RULES = {
    qos_consts.RULE_TYPE_BANDWIDTH_LIMIT: {
        qos_consts.MAX_KBPS: {
            'type:range': [0, db_consts.DB_INTEGER_MAX_VALUE]},
        qos_consts.MAX_BURST: {
            'type:range': [0, db_consts.DB_INTEGER_MAX_VALUE]},
        qos_consts.DIRECTION: {
            'type:values': [constants.EGRESS_DIRECTION]}
    },
    qos_consts.RULE_TYPE_DSCP_MARKING: {
        qos_consts.DSCP_MARK: {'type:values': constants.VALID_DSCP_MARKS}
    }
}


# TODO(yamamoto): Override precommit methods for task-based api
class MidoNetQosDriver(base.DriverBase):

    def __init__(self, *args, **kwargs):
        super(MidoNetQosDriver, self).__init__(*args, **kwargs)
        self._client = c_base.load_client(cfg.CONF.MIDONET)

    @staticmethod
    @log_helpers.log_method_call
    def create():
        return MidoNetQosDriver(
            name='midonet',
            vif_types=[
                m_const.VIF_TYPE_MIDONET,
            ],
            vnic_types=[
                portbindings.VNIC_NORMAL,
            ],
            supported_rules=SUPPORTED_RULES,
            requires_rpc_notifications=False)

    @log_helpers.log_method_call
    def create_policy(self, context, policy):
        self._client.create_qos_policy(context, policy)

    @log_helpers.log_method_call
    def update_policy(self, context, policy):
        self._client.update_qos_policy(context, policy)

    @log_helpers.log_method_call
    def delete_policy(self, context, policy):
        self._client.delete_qos_policy(context, policy)


def register():
    global DRIVER
    if not DRIVER:
        DRIVER = MidoNetQosDriver.create()
    LOG.debug('MidoNet QoS driver registered')
