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

import itertools

from neutron_lib import exceptions as nexception
from neutron_lib.plugins import directory
from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_utils import excutils

from neutron.api import extensions as neutron_extensions
from neutron.db import api as db_api
from neutron_dynamic_routing import extensions as bgp_extensions
from neutron_dynamic_routing.extensions import bgp

from midonet.neutron.client import base as c_base
from midonet.neutron.common import config  # noqa
from midonet.neutron.common import constants as m_const
from midonet.neutron.db import bgp_db_midonet
from midonet.neutron.db import bgp_speaker_router_insertion_db as bsridb
from midonet.neutron import extensions
from midonet.neutron.extensions import bgp_speaker_router_insertion as bsri


LOG = logging.getLogger(__name__)


class MidonetBgpPlugin(bgp_db_midonet.MidonetBgpDbMixin,
                       bsridb.BgpSpeakerRouterInsertionDbMixin):

    """Implements MidoNet BGP dynamic routing service plugin.

    This class manages the workflow of Midonet BGP request/response.
    """

    supported_extension_aliases = [bgp.BGP_EXT_ALIAS,
                                   bsri.BGP_ROUTER_EXT_ALIAS]

    def __init__(self):
        neutron_extensions.append_api_extensions_path(extensions.__path__)
        neutron_extensions.append_api_extensions_path(bgp_extensions.__path__)

        # Instantiate MidoNet API client.
        self.client = c_base.load_client(cfg.CONF.MIDONET)

        super(MidonetBgpPlugin, self).__init__()

    @classmethod
    def get_plugin_type(cls):
        return bgp.BGP_EXT_ALIAS

    def get_plugin_description(self):
        """returns string description of the plugin."""
        return ("MidoNet BGP dynamic routing service")

    @log_helpers.log_method_call
    def create_bgp_speaker(self, context, bgp_speaker):
        with db_api.context_manager.writer.using(context):
            bgp_sp = super(MidonetBgpPlugin,
                           self).create_bgp_speaker(context, bgp_speaker)
            router_id = bgp_speaker['bgp_speaker'][m_const.LOGICAL_ROUTER]
            if router_id:
                # If the router is already associated with bgp-speaker,
                # RouterInUse will be raised.
                self.set_router_for_bgp_speaker(
                    context, bgp_sp['id'], router_id)
                bgp_sp[m_const.LOGICAL_ROUTER] = router_id

        return bgp_sp

    @log_helpers.log_method_call
    def delete_bgp_speaker(self, context, bgp_speaker_id):
        with db_api.context_manager.writer.using(context):
            bgp_sp = super(MidonetBgpPlugin, self).get_bgp_speaker(
                context, bgp_speaker_id)
            super(MidonetBgpPlugin, self).delete_bgp_speaker(
                context, bgp_speaker_id)
            # Plugin should call 'UPDATE' to clean up bgp-peers because
            # backend cannot handle excepting ID when 'DELETE' is called.
            self.client.update_bgp_speaker_precommit(
                context, bgp_speaker_id, bgp_sp)

        self.client.update_bgp_speaker_postcommit(
            bgp_speaker_id, bgp_sp)

    @log_helpers.log_method_call
    def get_bgp_speakers(self, context, filters=None, fields=None,
                         sorts=None, limit=None, marker=None,
                         page_reverse=False):
        bgp_sp_list = super(MidonetBgpPlugin, self).get_bgp_speakers(
            context, filters, fields)
        for bgp_sp in bgp_sp_list:
            rt_id = self.get_router_associated_with_bgp_speaker(
                context, bgp_sp['id'])
            bgp_sp[m_const.LOGICAL_ROUTER] = rt_id
        return bgp_sp_list

    @log_helpers.log_method_call
    def get_bgp_speaker(self, context, bgp_speaker_id, fields=None):
        bgp_sp = super(MidonetBgpPlugin, self).get_bgp_speaker(
            context, bgp_speaker_id, fields)
        rt_id = self.get_router_associated_with_bgp_speaker(
            context, bgp_speaker_id)
        bgp_sp[m_const.LOGICAL_ROUTER] = rt_id
        return bgp_sp

    @log_helpers.log_method_call
    def add_bgp_peer(self, context, bgp_speaker_id, bgp_peer_info):
        # TODO(kengo): This is temporary workaround until upstream raise
        # an error when dictionary without 'bgp_peer_id' key is specified.
        if not self._get_id_for(bgp_peer_info, 'bgp_peer_id'):
            raise nexception.BadRequest(
                resource=bgp.BGP_SPEAKER_RESOURCE_NAME,
                msg="bgp_peer_id must be specified")
        with db_api.context_manager.writer.using(context):
            # In MidoNet, bgp-peer can be related to only one bgp-speaker.
            if self._get_bgp_speakers_by_bgp_peer_binding(
                    context, bgp_peer_info['bgp_peer_id']):
                raise bsri.MidonetBgpPeerInUse(
                    id=bgp_peer_info['bgp_peer_id'])
            if not self.get_router_associated_with_bgp_speaker(
                    context, bgp_speaker_id):
                # External network must be associated with the bgp speaker.
                raise bsri.ExternalNetworkUnbound()
            info = super(MidonetBgpPlugin, self).add_bgp_peer(
                context, bgp_speaker_id, bgp_peer_info)
            # get peer info for MidoNet
            bgp_peer = super(MidonetBgpPlugin, self).get_bgp_peer(
                context, info['bgp_peer_id'])
            # merge bgp_speaker information for MidoNet
            bgp_peer['bgp_speaker'] = self.get_bgp_speaker(
                context, bgp_speaker_id)
            self.client.create_bgp_peer_precommit(context, bgp_peer)

        try:
            self.client.create_bgp_peer_postcommit(bgp_peer)
        except Exception as ex:
            LOG.error("Failed to create MidoNet resources to add bgp "
                      "peer. bgp_peer=%(bgp_peer)s, "
                      "bgp_speaker_id=%(bgp_speaker_id)s, error=%(err)r",
                      {"bgp_peer": bgp_peer, "bgp_speaker_id": bgp_speaker_id,
                       "err": ex})
            with excutils.save_and_reraise_exception():
                super(MidonetBgpPlugin, self).remove_bgp_peer(
                    context, bgp_speaker_id, bgp_peer_info)

        return info

    @log_helpers.log_method_call
    def delete_bgp_peer(self, context, bgp_peer_id):
        with db_api.context_manager.writer.using(context):
            super(MidonetBgpPlugin, self).delete_bgp_peer(
                context, bgp_peer_id)
            self.client.delete_bgp_peer_precommit(context, bgp_peer_id)

        self.client.delete_bgp_peer_postcommit(bgp_peer_id)

    @log_helpers.log_method_call
    def remove_bgp_peer(self, context, bgp_speaker_id, bgp_peer_info):
        with db_api.context_manager.writer.using(context):
            bgp_peer = super(MidonetBgpPlugin, self).remove_bgp_peer(
                context, bgp_speaker_id, bgp_peer_info)
            bgp_peer_id = bgp_peer_info['bgp_peer_id']
            self.client.delete_bgp_peer_precommit(context, bgp_peer_id)

        self.client.delete_bgp_peer_postcommit(bgp_peer_id)
        return bgp_peer

    @log_helpers.log_method_call
    def update_bgp_peer(self, context, bgp_peer_id, bgp_peer):
        with db_api.context_manager.writer.using(context):
            bgp_peer = super(MidonetBgpPlugin, self).update_bgp_peer(
                context, bgp_peer_id, bgp_peer)
            updated_bgp_peer = {'bgp_peer': bgp_peer}
            self.client.update_bgp_peer_precommit(
                context, bgp_peer_id, updated_bgp_peer)

        self.client.update_bgp_peer_postcommit(bgp_peer_id,
                                               updated_bgp_peer)
        return bgp_peer

    @log_helpers.log_method_call
    def get_advertised_routes(self, context, bgp_speaker_id):
        rt_id = self.get_router_associated_with_bgp_speaker(
            context, bgp_speaker_id)

        # figure out advertised routes from attached networks
        attached_routes = self.get_routes_from_attached_networks(
            context, bgp_speaker_id, rt_id)

        # prepare nexthops to change nexthop of extra
        # route to IP address of router port
        nexthops = list(set([route[1] for route in attached_routes]))

        # figure out advertised routes from extra routes
        extra_routes = self.get_routes_from_extra_routes(
            context, rt_id, nexthops)

        routes = attached_routes + extra_routes
        info = ({'destination': x, 'next_hop': y} for x, y in routes)
        return self._make_advertised_routes_dict(itertools.chain(info))

    @log_helpers.log_method_call
    def add_gateway_network(self, context, bgp_speaker_id, network_info):
        with db_api.context_manager.writer.using(context):
            # TODO(kengo): This validation is temporary workaround
            # until upstream adds a validation for
            # existing combination of bgp speaker and gateway network.
            if self.get_router_associated_with_bgp_speaker(
                    context, bgp_speaker_id):
                raise bsri.BgpSpeakerInUse(
                    id=bgp_speaker_id,
                    reason='is already associated with router.')
            core_plugin = directory.get_plugin()
            if not core_plugin._network_is_external(
                    context, network_info['network_id']):
                raise bsri.NetworkTypeInvalid()
            info = super(MidonetBgpPlugin, self).add_gateway_network(
                context, bgp_speaker_id, network_info)
            self.set_router_for_bgp_speaker_by_network(
                context, bgp_speaker_id, network_info['network_id'])

        return info

    @log_helpers.log_method_call
    def remove_gateway_network(self, context, bgp_speaker_id, network_info):
        with db_api.context_manager.writer.using(context):
            if self.get_bgp_peers_by_bgp_speaker(context, bgp_speaker_id):
                raise bsri.BgpSpeakerInUse(id=bgp_speaker_id)
            info = super(MidonetBgpPlugin, self).remove_gateway_network(
                context, bgp_speaker_id, network_info)
            self.delete_bgp_speaker_router_insertion(
                context, bgp_speaker_id)

        return info
