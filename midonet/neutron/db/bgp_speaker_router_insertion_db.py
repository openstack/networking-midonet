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

from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib.callbacks import resources
from neutron_lib.exceptions import l3 as l3_exc
from neutron_lib.plugins import directory
from oslo_db import exception as db_exc
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from sqlalchemy.orm import exc

from neutron.db import api as db_api
from neutron_dynamic_routing.db import bgp_db as bdb

from midonet.neutron.db import bgp_speaker_router_insertion_model as model
from midonet.neutron.extensions import bgp_speaker_router_insertion as bsri


LOG = logging.getLogger(__name__)


@registry.has_registry_receivers
class BgpSpeakerRouterInsertionDbMixin(object):

    """Access methods for the bgp_speaker_router_associations table."""

    @log_helpers.log_method_call
    def set_router_for_bgp_speaker(self, context, bgp_sp_id, r_id):
        """Sets the routers associated with the bgp speaker."""
        try:
            with db_api.context_manager.writer.using(context):
                bgp_router_db = model.BgpSpeakerRouterAssociation(
                    bgp_speaker_id=bgp_sp_id,
                    router_id=r_id)
                context.session.add(bgp_router_db)
        except db_exc.DBDuplicateEntry:
            raise l3_exc.RouterInUse(
                router_id=r_id,
                reason='is already associated with bgp speaker')
        except db_exc.DBReferenceError:
            raise l3_exc.RouterNotFound(router_id=r_id)

    @log_helpers.log_method_call
    def get_router_associated_with_bgp_speaker(self, context, bgp_sp_id):
        """Gets router associated with a bgp speaker."""
        r_id = None
        try:
            query = self._model_query(context,
                                      model.BgpSpeakerRouterAssociation)
            bsra = query.filter(
                model.BgpSpeakerRouterAssociation.bgp_speaker_id ==
                bgp_sp_id).one()
            r_id = bsra['router_id']

        except exc.NoResultFound:
            LOG.debug("the bgp speaker %s is not attached to any router",
                      bgp_sp_id)
        return r_id

    @log_helpers.log_method_call
    def get_bgp_speaker_associated_with_router(self, context, router_id):
        """Gets router associated with a bgp speaker."""
        bgp_sp_id = None
        try:
            query = self._model_query(context,
                                      model.BgpSpeakerRouterAssociation)
            bsra = query.filter(
                model.BgpSpeakerRouterAssociation.router_id == router_id).one()
            bgp_sp_id = bsra['bgp_speaker_id']

        except exc.NoResultFound:
            LOG.debug("the router %s is not attached to any bgp speaker",
                      bgp_sp_id)
        return bgp_sp_id

    @log_helpers.log_method_call
    def set_router_for_bgp_speaker_by_network(self, context,
                                              bgp_sp_id, net_id):
        """This method selects one router to be a bgp speaker.

        To pare down routers, only first subnet in specified external
        network is used for selection.
        REVISIT(Kengo): There may be a case where there are two subnets
        and a router is associated with the second subnet. The case is
        a restriction for user and should be improved later.
        """
        core_plugin = directory.get_plugin()
        subnets = core_plugin.get_subnets_by_network(context, net_id)
        if not subnets:
            raise bsri.NoSubnetInNetwork(network_id=net_id)
        if not subnets[0]['gateway_ip']:
            raise bsri.NoGatewayIpOnSubnet(subnet_id=subnets[0]['id'])
        filters = {'fixed_ips': {'ip_address': [subnets[0]['gateway_ip']],
                                 'subnet_id': [subnets[0]['id']]}}
        ports = core_plugin.get_ports(context, filters=filters)
        if not ports:
            raise bsri.NoGatewayIpPortOnSubnet(subnet_id=subnets[0]['id'])
        router_id = ports[0]['device_id']
        # If the router is already associated with bgp-speaker,
        # RouterInUse will be raised.
        self.set_router_for_bgp_speaker(context, bgp_sp_id, router_id)

    def _get_bgp_speakers_by_bgp_peer_binding(self, context, bgp_peer_id):
        with db_api.context_manager.reader.using(context):
            query = context.session.query(bdb.BgpSpeaker)
            query = query.filter(
                bdb.BgpSpeakerPeerBinding.bgp_speaker_id == bdb.BgpSpeaker.id,
                bdb.BgpSpeakerPeerBinding.bgp_peer_id == bgp_peer_id)
            return query.all()

    def delete_bgp_speaker_router_insertion(self, context, bsp_id):
        with db_api.context_manager.writer.using(context):
            query = self._model_query(
                context, model.BgpSpeakerRouterAssociation)
            query.filter(
                model.BgpSpeakerRouterAssociation.bgp_speaker_id ==
                bsp_id).delete()

    @registry.receives(resources.ROUTER, [events.BEFORE_DELETE])
    def bgp_speaker_callback(self, resource, event, trigger, payload=None):
        router_id = payload.resource_id
        context = payload.context
        if self.get_bgp_speaker_associated_with_router(context, router_id):
            raise l3_exc.RouterInUse(
                router_id=router_id, reason='is associated with bgp speaker')
