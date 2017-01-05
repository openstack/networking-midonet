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

import abc
import six

from midonet.neutron._i18n import _LE

from oslo_log import log as logging
from oslo_utils import excutils
from oslo_utils import importutils

LOG = logging.getLogger(__name__)


def load_client(conf):
    try:
        client = importutils.import_object(conf.client, conf)
        LOG.debug("Loaded midonet client '%(client)s'", {'client': client})
        return client
    except ImportError:
        with excutils.save_and_reraise_exception():
            LOG.exception(_LE("Error loading midonet client '%(client)s'"),
                          {'client': conf.client})


@six.add_metaclass(abc.ABCMeta)
class MidonetClientBase(object):
    """Neutron MidoNet client base class.

    This class abstracts the communication between Neutron and MidoNet as there
    may be multiple ways to do so.  All MidoNet clients intended to be used
    from the Neutron plugin should extend this class.
    """

    def initialize(self):
        pass

    def create_network_precommit(self, context, network):
        pass

    def create_network_postcommit(self, network):
        pass

    def update_network_precommit(self, context, network_id, network):
        pass

    def update_network_postcommit(self, network_id, network):
        pass

    def delete_network_precommit(self, context, network_id):
        pass

    def delete_network_postcommit(self, network_id):
        pass

    def create_subnet_precommit(self, context, subnet):
        pass

    def create_subnet_postcommit(self, subnet):
        pass

    def update_subnet_precommit(self, context, subnet_id, subnet):
        pass

    def update_subnet_postcommit(self, subnet_id, subnet):
        pass

    def delete_subnet_precommit(self, context, subnet_id):
        pass

    def delete_subnet_postcommit(self, subnet_id):
        pass

    def create_port_precommit(self, context, port):
        pass

    def create_port_postcommit(self, port):
        pass

    def update_port_precommit(self, context, port_id, port):
        pass

    def update_port_postcommit(self, port_id, port):
        pass

    def delete_port_precommit(self, context, port_id):
        pass

    def delete_port_postcommit(self, port_id):
        pass

    def create_router_precommit(self, context, router):
        pass

    def create_router_postcommit(self, router):
        pass

    def update_router_precommit(self, context, router_id, router):
        pass

    def update_router_postcommit(self, router_id, router):
        pass

    def delete_router_precommit(self, context, router_id):
        pass

    def delete_router_postcommit(self, router_id):
        pass

    def add_router_interface_precommit(self, context, router_id,
                                       interface_info):
        pass

    def add_router_interface_postcommit(self, router_id, interface_info):
        pass

    def remove_router_interface_precommit(self, context, router_id,
                                          interface_info):
        pass

    def remove_router_interface_postcommit(self, router_id, interface_info):
        pass

    def create_floatingip_precommit(self, context, floatingip):
        pass

    def create_floatingip_postcommit(self, floatingip):
        pass

    def update_floatingip_precommit(self, context, floatingip_id, floatingip):
        pass

    def update_floatingip_postcommit(self, floatingip_id, floatingip):
        pass

    def delete_floatingip_precommit(self, context, floatingip_id):
        pass

    def delete_floatingip_postcommit(self, floatingip_id):
        pass

    def create_security_group_precommit(self, context, security_group):
        pass

    def create_security_group_postcommit(self, security_group):
        pass

    def update_security_group_precommit(self, context, security_group_id,
                                        security_group):
        pass

    def update_security_group_postcommit(self, security_group_id,
                                         security_group):
        pass

    def delete_security_group_precommit(self, context, security_group_id):
        pass

    def delete_security_group_postcommit(self, security_group_id):
        pass

    def create_security_group_rule_precommit(self, context,
                                             security_group_rule):
        pass

    def create_security_group_rule_postcommit(self, security_group_rule):
        pass

    def create_security_group_rule_bulk_precommit(self, context,
                                                  security_group_rules):
        pass

    def create_security_group_rule_bulk_postcommit(self, security_group_rules):
        pass

    def delete_security_group_rule_precommit(self, context,
                                             security_group_rule_id):
        pass

    def delete_security_group_rule_postcommit(self, security_group_rule_id):
        pass

    # Agent membership extension

    def create_agent_membership_precommit(self, context, agent_membership):
        pass

    def create_agent_membership_postcommit(self, agent_membership):
        pass

    def delete_agent_membership_precommit(self, context, agent_membership_id):
        pass

    def delete_agent_membership_postcommit(self, agent_membership_id):
        pass

    # Agent extension

    def get_agent(self, agent_id):
        return None

    def get_agents(self):
        return []

    # LBaaS methods - these are not inside a DB transaction.  DB updates as
    # well as blocking API calls are allowed.

    def create_vip(self, context, vip):
        pass

    def update_vip(self, context, vip_id, new_vip):
        pass

    def delete_vip(self, context, vip_id):
        pass

    def create_pool(self, context, pool):
        pass

    def update_pool(self, context, pool_id, pool):
        pass

    def delete_pool(self, context, pool_id):
        pass

    def create_member(self, context, member):
        pass

    def update_member(self, context, member_id, member):
        pass

    def delete_member(self, context, member_id):
        pass

    def create_health_monitor(self, context, health_monitor):
        pass

    def update_health_monitor(self, context, health_monitor_id,
                              health_monitor):
        pass

    def delete_health_monitor(self, context, health_monitor_id):
        pass

    # FWaaS methods - these are not called inside DB transaction.

    def create_firewall(self, context, firewall):
        pass

    def delete_firewall(self, context, firewall):
        pass

    def update_firewall(self, context, firewall):
        pass

    # VPNaaS methods

    def create_vpn_service(self, context, vpn_service):
        pass

    def update_vpn_service(self, context, vpn_service_id, vpn_service):
        pass

    def delete_vpn_service(self, context, vpn_service_id):
        pass

    def create_ipsec_site_conn(self, context, ipsec_site_conn):
        pass

    def update_ipsec_site_conn(self, context, ipsec_site_conn_id,
            ipsec_site_conn):
        pass

    def delete_ipsec_site_conn(self, context, ipsec_site_conn_id):
        pass

    # Gateway Device extensions

    def create_gateway_device_precommit(self, context, gw_dev):
        pass

    def create_gateway_device_postcommit(self, gw_dev):
        pass

    def update_gateway_device_precommit(self, context, gw_dev_id, gw_dev):
        pass

    def update_gateway_device_postcommit(self, gw_dev_id, gw_dev):
        pass

    def delete_gateway_device_precommit(self, context, gw_dev_id):
        pass

    def delete_gateway_device_postcommit(self, gw_dev_id):
        pass

    def create_gateway_device_remote_mac_entry_precommit(self, context,
                                                         mac_entry):
        pass

    def create_gateway_device_remote_mac_entry_postcommit(self, mac_entry):
        pass

    def delete_gateway_device_remote_mac_entry_precommit(self, context,
                                                         mac_entry_id):
        pass

    def delete_gateway_device_remote_mac_entry_postcommit(self, mac_entry_id):
        pass

    # L2 Gateway extensions

    def create_l2_gateway_connection(self, context, l2_gw_conn):
        pass

    def delete_l2_gateway_connection(self, context, l2_gw_conn_id):
        pass

    # BGP extensions

    def update_bgp_speaker_precommit(self, context,
                                     bgp_speaker_id, bgp_speaker):
        pass

    def update_bgp_speaker_postcommit(self, bgp_speaker_id, bgp_speaker):
        pass

    def create_bgp_peer_precommit(self, context, bgp_peer):
        pass

    def create_bgp_peer_postcommit(self, bgp_peer):
        pass

    def update_bgp_peer_precommit(self, context, bgp_peer_id, bgp_peer):
        pass

    def update_bgp_peer_postcommit(self, bgp_peer_id, bgp_peer):
        pass

    def delete_bgp_peer_precommit(self, context, bgp_peer_id):
        pass

    def delete_bgp_peer_postcommit(self, bgp_peer_id):
        pass

    # Logging Resource extensions

    def update_logging_resource_precommit(
            self, context, logging_resource_id, logging_resource):
        pass

    def update_logging_resource_postcommit(self, logging_resource_id,
                                           logging_resource):
        pass

    def delete_logging_resource_precommit(self, context, logging_resource_id):
        pass

    def delete_logging_resource_postcommit(self, logging_resource_id):
        pass

    def create_firewall_log_precommit(self, context, firewall_log):
        pass

    def create_firewall_log_postcommit(self, firewall_log):
        pass

    def update_firewall_log_precommit(self, context,
                                      firewall_log_id, firewall_log):
        pass

    def update_firewall_log_postcommit(self, firewall_log_id, firewall_log):
        pass

    def delete_firewall_log_precommit(self, context, firewall_log_id):
        pass

    def delete_firewall_log_postcommit(self, firewall_log_id):
        pass

    # Tap as a service

    def create_tap_flow(self, context, tap_flow):
        pass

    def delete_tap_flow(self, context, tap_flow_id):
        pass

    def create_tap_service(self, context, tap_service):
        pass

    def delete_tap_service(self, context, tap_service_id):
        pass

    # QoS
    def create_qos_policy(self, context, policy):
        pass

    def update_qos_policy(self, context, policy):
        pass

    def delete_qos_policy(self, context, policy):
        pass

    # MidoNet Pool Member
    def get_pool_member(self, context, member_id):
        pass

    # REVISIT(yamamoto): LBaaS v2
