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

from neutron.common import constants as n_const
from neutron.common import exceptions as n_exc
from neutron.db import l3_db
from neutron.db import models_v2
from neutron import i18n
from neutron import manager
from neutron.plugins.common import constants as service_constants
from sqlalchemy.orm import exc

_LE = i18n._LE


class LoadBalancerDriverDbMixin(object):

    def _check_and_get_router_id_for_pool(self, context, subnet_id):

        subnet = self.core_plugin._get_subnet(context, subnet_id)

        # Check whether the network is external
        if self._is_subnet_external(context, subnet):
            msg = (_LE("pool subnet must not be public"))
            raise n_exc.BadRequest(resource='pool', msg=msg)

        router_id = self._get_router_from_subnet(context, subnet)
        if not router_id:
            msg = (_LE("pool subnet must be associated with router"))
            raise n_exc.BadRequest(resource='pool', msg=msg)
        return router_id

    def _get_router_from_pool(self, context, pool):
        subnet = self.core_plugin._get_subnet(context, pool['subnet_id'])
        return self._get_router_from_subnet(context, subnet)

    def _get_router_from_port(self, context, port_id):
        routers = context.session.query(l3_db.Router)
        routers = routers.join(models_v2.Port,
                               l3_db.Router.id == models_v2.Port.device_id)
        routers = routers.filter(models_v2.Port.id == port_id)
        try:
            return routers.one().id
        except exc.NoResultFound:
            return None

    def _get_router_from_subnet(self, context, subnet):
        iport = self._get_router_interface_port(context, subnet)
        if iport is None:
            return None
        else:
            return self._get_router_from_port(context, iport)

    def _get_router_interface_port(self, context, subnet):
        all_ports = context.session.query(models_v2.Port).join(
            models_v2.Port.fixed_ips)
        ports = all_ports.filter(
            models_v2.Port.device_owner == n_const.DEVICE_OWNER_ROUTER_INTF)
        ports = ports.filter(models_v2.Port.network_id == subnet['network_id'])
        ports = ports.filter(
            models_v2.IPAllocation.ip_address == subnet['gateway_ip'])
        try:
            return ports.one().id
        except exc.NoResultFound:
            return None

    def _is_subnet_external(self, context, subnet):
        network = self.core_plugin._get_network(context, subnet['network_id'])
        return network.external

    def _validate_vip_subnet(self, context, vip):
        subnet = self.core_plugin._get_subnet(context, vip['subnet_id'])
        pool = self.plugin.get_pool(context, vip['pool_id'])

        # VIP and pool must not be on the same subnet if pool is associated
        # with a health monitor.  Health monitor would not work in that case.
        if pool['health_monitors'] and pool['subnet_id'] == subnet['id']:
            msg = (_LE("The VIP and pool cannot be on the same subnet if"
                       "health monitor is associated"))
            raise n_exc.BadRequest(resource='vip', msg=msg)

        if not self._is_subnet_external(context, subnet):
            return

        # ensure that if the vip subnet is public, the router has its
        # gateway set.
        router_id = self._get_router_from_pool(context, pool)

        # router_id should never be None because it was already validated
        # when we created the pool
        assert router_id is not None

        l3plugin = manager.NeutronManager.get_service_plugins().get(
            service_constants.L3_ROUTER_NAT)
        router = l3plugin._get_router(context, router_id)
        if router.get('gw_port_id') is None:
            msg = (_LE("The router must have its gateway set if the "
                       "VIP subnet is external"))
            raise n_exc.BadRequest(resource='vip', msg=msg)

    def _validate_pool_hm_assoc(self, context, pool_id, hm_id):
        pool = self.plugin.get_pool(context, pool_id)
        assoc = next((x for x in pool['health_monitors'] if x != hm_id), None)

        # There is an association with a different health monitor
        if assoc:
            msg = (_LE("The pool is already associated with a different "
                       "health monitor"))
            raise n_exc.BadRequest(resource='pool_monitor_association',
                                   msg=msg)

        # When associating health monitor, the subnet of VIP and Pool must not
        # match
        if pool['vip_id']:
            vip = self.plugin.get_vip(context, pool['vip_id'])
            if vip['subnet_id'] == pool['subnet_id']:
                msg = (_LE("The VIP and pool cannot be on the same subnet if"
                           "health monitor is associated"))
                raise n_exc.BadRequest(resource='pool_monitor_association',
                                       msg=msg)
