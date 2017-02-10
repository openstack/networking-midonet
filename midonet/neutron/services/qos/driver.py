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

from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from neutron.extensions import portbindings
from neutron.services.qos.drivers import base
from neutron.services.qos.notification_drivers import qos_base
from neutron.services.qos import qos_consts

from midonet.neutron._i18n import _LW
from midonet.neutron.client import base as c_base
from midonet.neutron.common import constants as m_const


LOG = logging.getLogger(__name__)


DRIVER = None


SUPPORTED_RULES = [
    qos_consts.RULE_TYPE_BANDWIDTH_LIMIT,
    qos_consts.RULE_TYPE_DSCP_MARKING,
]


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


# NOTE(yamamoto): The following driver is just a no-op to avoid
# breaking the existing configuration.
class MidoNetQosServiceNotificationDriver(
    qos_base.QosServiceNotificationDriverBase):

    def __init__(self):
        super(MidoNetQosServiceNotificationDriver, self).__init__()
        LOG.warning(
            _LW("MidoNet QoS notification driver is no longer necessary. "
                "Please remove QoS notification_drivers configuration."))

    def get_description(self):
        return "MidoNet QoS notification driver (no-op version)"

    def create_policy(self, context, policy):
        pass

    def update_policy(self, context, policy):
        pass

    def delete_policy(self, context, policy):
        pass
