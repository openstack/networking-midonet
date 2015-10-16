# Copyright (C) 2015 Midokura SARL.
# All rights reserved.
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

from neutron.common import constants

from midonet.neutron.client import base as c_base
from midonet.neutron.common import config  # noqa
from midonet.neutron.common import constants as const
from midonet.neutron.ml2 import sg_callback
from midonet.neutron.ml2 import util as m_util

from neutron.common import constants as n_const
from neutron.common import exceptions as n_exc
from neutron.extensions import portbindings
from neutron import i18n
from neutron.plugins.ml2 import driver_api as api
from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging

_LE = i18n._LE
LOG = logging.getLogger(__name__)


class MidonetMechanismDriver(api.MechanismDriver):

    """ML2 Mechanism Driver for Midonet."""

    def __init__(self):
        self.vif_type = const.VIF_TYPE_MIDONET
        self.supported_vnic_types = [portbindings.VNIC_NORMAL]
        self.vif_details = {portbindings.CAP_PORT_FILTER: True}

        self.client = c_base.load_client(cfg.CONF.MIDONET)
        self.client.initialize()

    def initialize(self):
        self.sec_handler = sg_callback.MidonetSecurityGroupsHandler(
            self.client)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def create_network_precommit(self, context):
        network = context.current
        self.client.create_network_precommit(context, network)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def create_network_postcommit(self, context):
        network = context.current
        self.client.create_network_postcommit(network)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def update_network_precommit(self, context):
        net = context.current
        self.client.update_network_precommit(context, net['id'], net)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def update_network_postcommit(self, context):
        net = context.current
        self.client.update_network_postcommit(net['id'], net)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def delete_network_precommit(self, context):
        network_id = context.current['id']
        self.client.delete_network_precommit(context, network_id)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def delete_network_postcommit(self, context):
        network_id = context.current['id']
        self.client.delete_network_postcommit(network_id)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def create_subnet_precommit(self, context):
        subnet = context.current
        self.client.create_subnet_precommit(context, subnet)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def create_subnet_postcommit(self, context):
        subnet = context.current
        self.client.create_subnet_postcommit(subnet)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def update_subnet_precommit(self, context):
        subnet = context.current
        self.client.update_subnet_precommit(context, subnet['id'], subnet)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def update_subnet_postcommit(self, context):
        subnet = context.current
        self.client.update_subnet_postcommit(subnet['id'], subnet)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def delete_subnet_precommit(self, context):
        subnet_id = context.current['id']
        self.client.delete_subnet_precommit(context, subnet_id)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def delete_subnet_postcommit(self, context):
        subnet_id = context.current['id']
        self.client.delete_subnet_postcommit(subnet_id)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def create_port_precommit(self, context):
        port = context.current
        self.client.create_port_precommit(context, port)

    def _validate_port_create(self, port):
        if (port.get('device_owner') == n_const.DEVICE_OWNER_ROUTER_GW
                and not port['fixed_ips']):
            msg = (_("No IPs assigned to the gateway port for"
                     " router %s") % port['device_id'])
            raise n_exc.BadRequest(resource='router', msg=msg)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def create_port_postcommit(self, context):
        port = context.current
        self._validate_port_create(port)
        self.client.create_port_postcommit(port)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def update_port_precommit(self, context):
        port = context.current
        self.client.update_port_precommit(context, port['id'], port)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def update_port_postcommit(self, context):
        port = context.current
        self.client.update_port_postcommit(port['id'], port)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def delete_port_precommit(self, context):
        port_id = context.current['id']
        self.client.delete_port_precommit(context, port_id)

    @m_util.filter_midonet_network
    @log_helpers.log_method_call
    def delete_port_postcommit(self, context):
        port_id = context.current['id']
        self.client.delete_port_postcommit(port_id)

    @log_helpers.log_method_call
    def bind_port(self, context):
        for segment in context.segments_to_bind:
            if segment['network_type'] in const.MIDONET_NET_TYPES:
                context.set_binding(segment[api.ID],
                                    self.vif_type,
                                    self.vif_details,
                                    constants.PORT_STATUS_ACTIVE)
                break
            else:
                LOG.debug(('midonet mechanism driver did NOT bind '
                           'port for segment %r'), segment)
