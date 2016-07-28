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

import netaddr
from oslo_utils import excutils
from sqlalchemy import orm

from neutron.callbacks import events
from neutron.callbacks import exceptions
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.common import constants as n_const
from neutron.db import api as db_api
from neutron.db import l3_db
from neutron.db import l3_gwmode_db
from neutron.db import models_v2
from neutron.extensions import l3


class MidonetL3DBMixin(l3_gwmode_db.L3_NAT_db_mixin):
    # TODO(kengo): This is temporary workaround until upstream adds a check
    # for router deletion in l3_db

    def _check_router_not_in_use(self, context, router_id):
        try:
            kwargs = {'context': context, 'router_id': router_id}
            registry.notify(
                resources.ROUTER, events.BEFORE_DELETE, self, **kwargs)
        except exceptions.CallbackFailure as e:
            with excutils.save_and_reraise_exception():
                if len(e.errors) == 1:
                    raise e.errors[0].error
                raise l3.RouterInUse(router_id=router_id, reason=e)

    # bug 1605894
    def _validate_router_port_info(self, context, router, port_id):
        with db_api.autonested_transaction(context.session):
            return super(MidonetL3DBMixin, self)._validate_router_port_info(
                context, router, port_id)

    # REVISIT(yamamoto): This method is a copy of the base class method,
    # with 'router_id' notification argument added.
    def _confirm_router_interface_not_in_use(self, context, router_id,
                                             subnet_id):
        subnet = self._core_plugin.get_subnet(context, subnet_id)
        subnet_cidr = netaddr.IPNetwork(subnet['cidr'])
        fip_qry = context.session.query(l3_db.FloatingIP)
        try:
            kwargs = {'context': context, 'subnet_id': subnet_id,
                      'router_id': router_id}
            registry.notify(
                resources.ROUTER_INTERFACE,
                events.BEFORE_DELETE, self, **kwargs)
        except exceptions.CallbackFailure as e:
            with excutils.save_and_reraise_exception():
                # NOTE(armax): preserve old check's behavior
                if len(e.errors) == 1:
                    raise e.errors[0].error
                raise l3.RouterInUse(router_id=router_id, reason=e)
        for fip_db in fip_qry.filter_by(router_id=router_id):
            if netaddr.IPAddress(fip_db['fixed_ip_address']) in subnet_cidr:
                raise l3.RouterInterfaceInUseByFloatingIP(
                    router_id=router_id, subnet_id=subnet_id)

    def get_router_for_floatingip(self, context, internal_port,
            internal_subnet, external_network_id):
        # REVISIT(yamamoto): These direct manipulation of core-plugin db
        # resources is not ideal.
        gw_port = orm.aliased(models_v2.Port, name="gw_port")
        routerport_qry = context.session.query(
            l3_db.RouterPort.router_id,
            models_v2.IPAllocation.ip_address
        ).join(
            models_v2.Port, models_v2.IPAllocation
        ).filter(
            models_v2.Port.network_id == internal_port['network_id'],
            l3_db.RouterPort.port_type.in_(
                n_const.ROUTER_INTERFACE_OWNERS
            ),
            models_v2.IPAllocation.subnet_id == internal_subnet['id']
        ).join(
            gw_port, gw_port.device_id == l3_db.RouterPort.router_id
        ).filter(
            gw_port.network_id == external_network_id,
        ).distinct()

        first_router_id = None
        for router_id, interface_ip in routerport_qry:
            if interface_ip == internal_subnet['gateway_ip']:
                return router_id
            if not first_router_id:
                first_router_id = router_id
        if first_router_id:
            return first_router_id

        raise l3.ExternalGatewayForFloatingIPNotFound(
            subnet_id=internal_subnet['id'],
            external_network_id=external_network_id,
            port_id=internal_port['id'])

    def _subnet_has_fip(self, context, router_id, subnet_id):
        # Return True if the subnet has one of floating IPs for the router
        subnet = self._core_plugin.get_subnet(context, subnet_id)
        subnet_cidr = netaddr.IPNetwork(subnet['cidr'])
        fip_qry = context.session.query(l3_db.FloatingIP)
        fip_qry = fip_qry.filter_by(router_id=router_id)
        for fip_db in fip_qry:
            if netaddr.IPAddress(fip_db['floating_ip_address']) in subnet_cidr:
                return True
        return False

    # REVISIT(yamamoto): This method is a copy of the base class method,
    # with modified RouterExternalGatewayInUseByFloatingIp validation.
    def _delete_current_gw_port(self, context, router_id, router,
                                new_network_id):
        """Delete gw port if attached to an old network."""
        port_requires_deletion = (
            router.gw_port and router.gw_port['network_id'] != new_network_id)
        if not port_requires_deletion:
            return
        admin_ctx = context.elevated()
        old_network_id = router.gw_port['network_id']

        for ip in router.gw_port['fixed_ips']:
            if self._subnet_has_fip(admin_ctx, router_id, ip['subnet_id']):
                raise l3.RouterExternalGatewayInUseByFloatingIp(
                    router_id=router_id, net_id=router.gw_port['network_id'])
        gw_ips = [x['ip_address'] for x in router.gw_port.fixed_ips]
        with context.session.begin(subtransactions=True):
            gw_port = router.gw_port
            router.gw_port = None
            context.session.add(router)
            context.session.expire(gw_port)
            self._check_router_gw_port_in_use(context, router_id)
        self._core_plugin.delete_port(
            admin_ctx, gw_port['id'], l3_port_check=False)
        registry.notify(resources.ROUTER_GATEWAY,
                        events.AFTER_DELETE, self,
                        router_id=router_id,
                        network_id=old_network_id,
                        gateway_ips=gw_ips)
