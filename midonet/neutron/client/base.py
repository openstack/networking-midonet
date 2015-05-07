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

    # LBaaS methods - move these out when the advanced service driver-model is
    # adopted

    def create_vip_precommit(self, context, vip):
        pass

    def create_vip_postcommit(self, vip):
        pass

    def update_vip_precommit(self, context, vip_id, vip):
        pass

    def update_vip_postcommit(self, vip_id, vip):
        pass

    def delete_vip_precommit(self, context, vip_id):
        pass

    def delete_vip_postcommit(self, vip_id):
        pass

    def create_pool_precommit(self, context, pool):
        pass

    def create_pool_postcommit(self, pool):
        pass

    def update_pool_precommit(self, context, pool_id, pool):
        pass

    def update_pool_postcommit(self, pool_id, pool):
        pass

    def delete_pool_precommit(self, context, pool_id):
        pass

    def delete_pool_postcommit(self, pool_id):
        pass

    def create_member_precommit(self, context, member):
        pass

    def create_member_postcommit(self, member):
        pass

    def update_member_precommit(self, context, member_id, member):
        pass

    def update_member_postcommit(self, member_id, member):
        pass

    def delete_member_precommit(self, context, member_id):
        pass

    def delete_member_postcommit(self, member_id):
        pass

    def create_health_monitor_precommit(self, context, health_monitor):
        pass

    def create_health_monitor_postcommit(self, health_monitor):
        pass

    def update_health_monitor_precommit(self, context, health_monitor_id,
                                        health_monitor):
        pass

    def update_health_monitor_postcommit(self, health_monitor_id,
                                         health_monitor):
        pass

    def delete_health_monitor_precommit(self, context, health_monitor_id):
        pass

    def delete_health_monitor_postcommit(self, health_monitor_id):
        pass

    def create_pool_health_monitor_precommit(self, context, health_monitor,
                                             pool_id):
        pass

    def create_pool_health_monitor_postcommit(self, health_monitor, pool_id):
        pass

    def delete_pool_health_monitor_precommit(self, context, health_monitor_id,
                                             pool_id):
        pass

    def delete_pool_health_monitor_postcommit(self, health_monitor_id,
                                              pool_id):
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
