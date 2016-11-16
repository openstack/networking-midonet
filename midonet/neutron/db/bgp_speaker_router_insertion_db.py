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

from midonet.neutron.db import bgp_speaker_router_insertion_model as model
from midonet.neutron.extensions import bgp_speaker_router_insertion as bsri

from neutron_dynamic_routing.db import bgp_db as bdb
from neutron_dynamic_routing.extensions import bgp as bgp_ext
from neutron_lib.plugins import directory

from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.extensions import l3
from oslo_db import exception as db_exc
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from sqlalchemy.orm import exc


LOG = logging.getLogger(__name__)


class BgpSpeakerRouterInsertionDbMixin(object):

    """Access methods for the bgp_speaker_router_associations table."""

    @log_helpers.log_method_call
    def set_router_for_bgp_speaker(self, context, bgp_sp_id, r_id):
        """Sets the routers associated with the bgp speaker."""
        try:
            with context.session.begin(subtransactions=True):
                bgp_router_db = model.BgpSpeakerRouterAssociation(
                        bgp_speaker_id=bgp_sp_id,
                        router_id=r_id)
                context.session.add(bgp_router_db)
        except db_exc.DBDuplicateEntry:
            raise l3.RouterInUse(
                    router_id=r_id,
                    reason='is already associated with bgp speaker')
        except db_exc.DBReferenceError:
            raise l3.RouterNotFound(router_id=r_id)

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
        self.set_router_for_bgp_speaker(
                context, bgp_sp_id, router_id)

    def _get_bgp_speakers_by_bgp_peer_binding(self, context, bgp_peer_id):
        with context.session.begin(subtransactions=True):
            query = context.session.query(bdb.BgpSpeaker)
            query = query.filter(
                bdb.BgpSpeakerPeerBinding.bgp_speaker_id == bdb.BgpSpeaker.id,
                bdb.BgpSpeakerPeerBinding.bgp_peer_id == bgp_peer_id)
            return query.all()

    def delete_bgp_speaker_router_insertion(self, context, bsp_id):
        with context.session.begin(subtransactions=True):
            query = self._model_query(
                    context, model.BgpSpeakerRouterAssociation)
            query.filter(
                model.BgpSpeakerRouterAssociation.bgp_speaker_id ==
                bsp_id).delete()


def bgp_speaker_callback(resource, event, trigger, **kwargs):
    router_id = kwargs['router_id']
    bgp_plugin = directory.get_plugin(bgp_ext.BGP_EXT_ALIAS)
    if bgp_plugin:
        context = kwargs.get('context')
        if bgp_plugin.get_bgp_speaker_associated_with_router(context,
                                                             router_id):
            raise l3.RouterInUse(router_id=router_id,
                    reason='is associated with bgp speaker')


def subscribe():
    registry.subscribe(
        bgp_speaker_callback, resources.ROUTER, events.BEFORE_DELETE)
