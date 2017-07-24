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

from neutron_lib.plugins import constants
from neutron_lib.plugins import directory
from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from neutron.ipam import utils as ipam_utils
from neutron_dynamic_routing.db import bgp_db

LOG = logging.getLogger(__name__)


class MidonetBgpDbMixin(bgp_db.BgpDbMixin):

    """Access methods to figure out advertised route by bgp speaker."""

    @log_helpers.log_method_call
    def get_routes_from_attached_networks(self, context,
                                          bgp_speaker_id, rt_id):
        """This method gets routes for networks attached to this router.

        * 'nexthop' is the IP address of the ports on this router
          that are on the same subnet as the peer IP addresses of
          the provided bgp speaker.
        * 'dest_networks' are all the networks attached to the router
          excluding gateway and uplink networks.
        """
        nexthops, dest_networks, route_info = [], [], []
        peers = self.get_bgp_peers_by_bgp_speaker(context, bgp_speaker_id)
        peer_ips = [peer['peer_ip'] for peer in peers]
        LOG.debug("peer_ips %s associated with bgp_speaker %s",
                  peer_ips, bgp_speaker_id)
        core_plugin = directory.get_plugin()
        ports = core_plugin.get_ports(context, filters={'device_id': [rt_id]})
        for port in ports:
            subnet_id = port['fixed_ips'][0]['subnet_id']
            cidr = core_plugin.get_subnet(
                context, subnet_id, fields=['cidr'])
            if self._extract_valid_peer_ips(cidr['cidr'], peer_ips):
                nexthops.append(port['fixed_ips'][0]['ip_address'])
            dest_networks.append(cidr['cidr'])
        for nexthop in nexthops:
            route_info += self._make_route_info(nexthop, dest_networks)
        LOG.debug("advertised routes from attached networks: %s", route_info)
        return route_info

    @log_helpers.log_method_call
    def get_routes_from_extra_routes(self, context, rt_id, nexthops):
        """This method gets routes for extra routes defined on this router.

        * 'nexthop' is the IP address of the ports on this router
          that are on the same subnet as the peer IP addresses of
          the provided bgp speaker.
        * 'dests' are all the networks defined as extra routes
          on the router.
        """
        changed_extra = []
        l3plugin = directory.get_plugin(constants.L3)
        extra = l3plugin.get_router(context, rt_id,
                                    fields=['routes'])['routes']
        dest_networks = [extra_route['destination'] for extra_route in extra]
        for nexthop in nexthops:
            changed_extra += self._change_nexthop_to_router_ip(nexthop,
                                                               dest_networks)
        LOG.debug("advertised routes from extra routes: %s", changed_extra)
        return changed_extra

    def _change_nexthop_to_router_ip(self, nexthop, dests):
        return [(dest, nexthop) for dest in dests]

    def _make_route_info(self, nexthop, dest_networks):
        return [(network, nexthop) for network in dest_networks
                if not ipam_utils.check_subnet_ip(network, nexthop)]

    def _extract_valid_peer_ips(self, cidr, peer_ips):
        return [(peer_ip) for peer_ip in peer_ips
                if ipam_utils.check_subnet_ip(cidr, peer_ip)]
