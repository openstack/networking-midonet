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

from midonet.neutron.client import base as c_base
from midonet.neutron.common import config  # noqa
from midonet.neutron.common import constants as const
from midonet.neutron import extensions

from neutron.api import extensions as neutron_extensions
from neutron.api.rpc.handlers import dhcp_rpc
from neutron.api.rpc.handlers import metadata_rpc
from neutron.common import rpc as n_rpc
from neutron.common import topics
from neutron.db import agents_db
from neutron.db import agentschedulers_db
from neutron.db import db_base_plugin_v2
from neutron.db import external_net_db
from neutron.db import extradhcpopt_db
from neutron.db import portbindings_db
from neutron.db import securitygroups_db
from neutron.extensions import portbindings

from oslo_config import cfg
from oslo_utils import importutils


class MidonetMixinBase(db_base_plugin_v2.NeutronDbPluginV2,
                       agentschedulers_db.DhcpAgentSchedulerDbMixin,
                       external_net_db.External_net_db_mixin,
                       extradhcpopt_db.ExtraDhcpOptMixin,
                       portbindings_db.PortBindingMixin,
                       securitygroups_db.SecurityGroupDbMixin):
    """NOTE(yamamoto): This class is shared between v1 and v2 plugins."""

    def __init__(self):
        super(MidonetMixinBase, self).__init__()

        # Instantiate MidoNet API client
        self.client = c_base.load_client(cfg.CONF.MIDONET)

        neutron_extensions.append_api_extensions_path(extensions.__path__)
        self.setup_rpc()

        self.base_binding_dict = {
            portbindings.VIF_TYPE: const.VIF_TYPE_MIDONET,
            portbindings.VNIC_TYPE: portbindings.VNIC_NORMAL,
            portbindings.VIF_DETAILS: {
                # TODO(rkukura): Replace with new VIF security details
                portbindings.CAP_PORT_FILTER:
                'security-group' in self.supported_extension_aliases}}
        self.network_scheduler = importutils.import_object(
            cfg.CONF.network_scheduler_driver
        )

    def setup_rpc(self):
        # RPC support
        self.topic = topics.PLUGIN
        self.conn = n_rpc.create_connection()
        self.endpoints = [dhcp_rpc.DhcpRpcCallback(),
                          agents_db.AgentExtRpcCallback(),
                          metadata_rpc.MetadataRpcCallback()]
        self.conn.create_consumer(self.topic, self.endpoints,
                                  fanout=False)
        # TODO(yamamoto): Remove the hasattr check after branching Liberty
        if hasattr(topics, 'REPORTS'):
            self.conn.create_consumer(topics.REPORTS,
                                      [agents_db.AgentExtRpcCallback()],
                                      fanout=False)

        # Consume from all consumers in a thread
        self.conn.consume_in_threads()
