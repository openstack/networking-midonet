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

from neutron_lib.db import api as db_api

from midonet.neutron.client import base
from midonet.neutron.db import task_db as task


class MidonetClusterClient(base.MidonetClientBase):

    def __init__(self, conf):
        self.conf = conf

    def initialize(self):
        task.create_config_task(db_api.get_writer_session(), dict(self.conf))

    def create_network_precommit(self, context, network):
        task.create_task(context, task.CREATE, data_type=task.NETWORK,
                         resource_id=network['id'], data=network)

    def update_network_precommit(self, context, network_id, network):
        task.create_task(context, task.UPDATE, data_type=task.NETWORK,
                         resource_id=network_id, data=network)

    def delete_network_precommit(self, context, network_id):
        task.create_task(context, task.DELETE, data_type=task.NETWORK,
                         resource_id=network_id)

    def create_subnet_precommit(self, context, subnet):
        task.create_task(context, task.CREATE, data_type=task.SUBNET,
                         resource_id=subnet['id'], data=subnet)

    def update_subnet_precommit(self, context, subnet_id, subnet):
        task.create_task(context, task.UPDATE, data_type=task.SUBNET,
                         resource_id=subnet_id, data=subnet)

    def delete_subnet_precommit(self, context, subnet_id):
        task.create_task(context, task.DELETE, data_type=task.SUBNET,
                         resource_id=subnet_id)

    def create_port_precommit(self, context, port):
        task.create_task(context, task.CREATE, data_type=task.PORT,
                         resource_id=port['id'], data=port)

    def update_port_precommit(self, context, port_id, port):
        task.create_task(context, task.UPDATE, data_type=task.PORT,
                         resource_id=port_id, data=port)

    def delete_port_precommit(self, context, port_id):
        task.create_task(context, task.DELETE, data_type=task.PORT,
                         resource_id=port_id)

    def create_router_precommit(self, context, router):
        task.create_task(context, task.CREATE, data_type=task.ROUTER,
                         resource_id=router['id'], data=router)

    def update_router_precommit(self, context, router_id, router):
        task.create_task(context, task.UPDATE, data_type=task.ROUTER,
                         resource_id=router_id, data=router)

    def delete_router_precommit(self, context, router_id):
        task.create_task(context, task.DELETE, data_type=task.ROUTER,
                         resource_id=router_id)

    def create_floatingip_precommit(self, context, floatingip):
        task.create_task(context, task.CREATE, data_type=task.FLOATING_IP,
                         resource_id=floatingip['id'], data=floatingip)

    def update_floatingip_precommit(self, context, floatingip_id, floatingip):
        task.create_task(context, task.UPDATE, data_type=task.FLOATING_IP,
                         resource_id=floatingip_id, data=floatingip)

    def delete_floatingip_precommit(self, context, floatingip_id):
        task.create_task(context, task.DELETE, data_type=task.FLOATING_IP,
                         resource_id=floatingip_id)

    def create_security_group_precommit(self, context, security_group):
        task.create_task(context, task.CREATE, data_type=task.SECURITY_GROUP,
                         resource_id=security_group['id'], data=security_group)

    def delete_security_group_precommit(self, context, security_group_id):
        task.create_task(context, task.DELETE, data_type=task.SECURITY_GROUP,
                         resource_id=security_group_id)

    def create_security_group_rule_precommit(self, context,
                                             security_group_rule):
        task.create_task(context, task.CREATE,
                         data_type=task.SECURITY_GROUP_RULE,
                         resource_id=security_group_rule['id'],
                         data=security_group_rule)

    def delete_security_group_rule_precommit(self, context,
                                             security_group_rule_id):
        task.create_task(context, task.DELETE,
                         data_type=task.SECURITY_GROUP_RULE,
                         resource_id=security_group_rule_id)

    # LBaaS

    def create_vip(self, context, vip):
        task.create_task(context, task.CREATE, data_type=task.VIP,
                         resource_id=vip['id'], data=vip)

    def update_vip(self, context, vip_id, vip):
        task.create_task(context, task.UPDATE, data_type=task.VIP,
                         resource_id=vip_id, data=vip)

    def delete_vip(self, context, vip_id):
        task.create_task(context, task.DELETE, data_type=task.VIP,
                         resource_id=vip_id)

    def create_pool(self, context, pool):
        task.create_task(context, task.CREATE, data_type=task.POOL,
                         resource_id=pool['id'], data=pool)

    def update_pool(self, context, pool_id, pool):
        task.create_task(context, task.UPDATE, data_type=task.POOL,
                         resource_id=pool_id, data=pool)

    def delete_pool(self, context, pool_id):
        task.create_task(context, task.DELETE, data_type=task.POOL,
                         resource_id=pool_id)

    def create_member(self, context, member):
        task.create_task(context, task.CREATE, data_type=task.MEMBER,
                         resource_id=member['id'], data=member)

    def update_member(self, context, member_id, member):
        task.create_task(context, task.UPDATE, data_type=task.MEMBER,
                         resource_id=member_id, data=member)

    def delete_member(self, context, member_id):
        task.create_task(context, task.DELETE, data_type=task.MEMBER,
                         resource_id=member_id)

    def create_health_monitor(self, context, health_monitor):
        task.create_task(context, task.CREATE, data_type=task.HEALTH_MONITOR,
                         resource_id=health_monitor['id'], data=health_monitor)

    def update_health_monitor(self, context, health_monitor_id,
                              health_monitor):
        task.create_task(context, task.UPDATE, data_type=task.HEALTH_MONITOR,
                         resource_id=health_monitor_id, data=health_monitor)

    def delete_health_monitor(self, context, health_monitor_id):
        task.create_task(context, task.DELETE, data_type=task.HEALTH_MONITOR,
                         resource_id=health_monitor_id)

    # TODO(yamamoto): Implement the following
    # - FWaaS v1
    # - VPNaaS
    # - L2 gateway
    # - gateway device
    # - BGP
    # - logging resource / firewall log
    # - Tap as a service
    # - QoS
    # - LBaaS v2
