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
from oslo_utils import uuidutils
from sqlalchemy import orm

from neutron_lib import constants as n_const
from neutron_lib import exceptions as n_exc

from neutron.callbacks import events
from neutron.callbacks import exceptions
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.db import l3_gwmode_db
from neutron.db.models import l3 as l3_models
from neutron.db import models_v2
from neutron.extensions import l3
from neutron.plugins.common import utils as p_utils

from midonet.neutron._i18n import _

DEVICE_OWNER_FLOATINGIP = n_const.DEVICE_OWNER_FLOATINGIP


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

    def get_router_for_floatingip(self, context, internal_port,
            internal_subnet, external_network_id):
        # REVISIT(yamamoto): These direct manipulation of core-plugin db
        # resources is not ideal.
        gw_port = orm.aliased(models_v2.Port, name="gw_port")
        routerport_qry = context.session.query(
            l3_models.RouterPort.router_id,
            models_v2.IPAllocation.ip_address
        ).join(
            models_v2.Port, models_v2.IPAllocation
        ).filter(
            models_v2.Port.network_id == internal_port['network_id'],
            l3_models.RouterPort.port_type.in_(
                n_const.ROUTER_INTERFACE_OWNERS
            ),
            models_v2.IPAllocation.subnet_id == internal_subnet['id']
        ).join(
            gw_port, gw_port.device_id == l3_models.RouterPort.router_id
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
        fip_qry = context.session.query(l3_models.FloatingIP)
        fip_qry = fip_qry.filter_by(router_id=router_id)
        for fip_db in fip_qry:
            if netaddr.IPAddress(fip_db['floating_ip_address']) in subnet_cidr:
                return True
        return False

    def router_gw_port_has_floating_ips(self, context, router_id):
        router = self._get_router(context, router_id)
        return any([self._subnet_has_fip(context, router_id, ip['subnet_id'])
            for ip in router.gw_port['fixed_ips']])

    def find_next_hop_for_fip(self, context, floatingip_db):
        # Find a next-hop address for a route from the floating_network_id
        # network to the floating-ip.
        # NOTE(tidwellr) use admin context here
        # tenant may not own the router and that's OK on a FIP association
        router_id = floatingip_db.router_id
        router = self._get_router(context.elevated(), router_id)
        gw_port = None
        for rp in router.attached_ports:
            if rp.port.network_id == floatingip_db.floating_network_id:
                gw_port = rp.port
                break
        if not gw_port:
            return None
        fip_addr = netaddr.IPAddress(floatingip_db.floating_ip_address)
        for fixed_ip in gw_port.fixed_ips:
            addr = netaddr.IPAddress(fixed_ip.ip_address)
            if addr.version == fip_addr.version:
                return fixed_ip.ip_address

    def _port_fixed_ips_for_floatingip(self, port):
        # Returns the fixed IP addresses on the given port preferring IPv4
        # over IPv6 ones
        port_ips = self._port_ipv4_fixed_ips(port)
        if not port_ips:
            port_ips = self._port_ipv6_fixed_ips(port)
        return port_ips

    def _port_ipv6_fixed_ips(self, port):
        return [ip for ip in port['fixed_ips']
                if netaddr.IPAddress(ip['ip_address']).version == 6]

    def _validate_network_for_floatingip(self, context, net_id):
        if not any(self._core_plugin._get_network(context, net_id).subnets):
            msg = _("Network %s does not contain any subnet") % net_id
            raise n_exc.BadRequest(resource='floatingip', msg=msg)

    # REVISIT(bikfalvi): This method is a copy of the base class method,
    # modified to use the _port_fixed_ips hook and replace the network
    # validation from IPv4 to any IP.
    def _create_floatingip(self, context, floatingip,
                           initial_status=n_const.FLOATINGIP_STATUS_ACTIVE):
        fip = floatingip['floatingip']
        fip_id = uuidutils.generate_uuid()

        f_net_id = fip['floating_network_id']
        if not self._core_plugin._network_is_external(context, f_net_id):
            msg = _("Network %s is not a valid external network") % f_net_id
            raise n_exc.BadRequest(resource='floatingip', msg=msg)

        self._validate_network_for_floatingip(context, f_net_id)

        # This external port is never exposed to the tenant.
        # it is used purely for internal system and admin use when
        # managing floating IPs.

        port = {'tenant_id': '',  # tenant intentionally not set
                'network_id': f_net_id,
                'admin_state_up': True,
                'device_id': 'PENDING',
                'device_owner': DEVICE_OWNER_FLOATINGIP,
                'status': n_const.PORT_STATUS_NOTAPPLICABLE,
                'name': ''}
        if fip.get('floating_ip_address'):
            port['fixed_ips'] = [
                {'ip_address': fip['floating_ip_address']}]

        if fip.get('subnet_id'):
            port['fixed_ips'] = [
                {'subnet_id': fip['subnet_id']}]

        # 'status' in port dict could not be updated by default, use
        # check_allow_post to stop the verification of system
        external_port = p_utils.create_port(self._core_plugin,
                                            context.elevated(),
                                            {'port': port},
                                            check_allow_post=False)

        with p_utils.delete_port_on_error(self._core_plugin,
                                          context.elevated(),
                                          external_port['id']),\
                context.session.begin(subtransactions=True):
            external_ips = self._port_fixed_ips_for_floatingip(external_port)
            if not external_ips:
                raise n_exc.ExternalIpAddressExhausted(net_id=f_net_id)

            floating_fixed_ip = external_ips[0]
            floating_ip_address = floating_fixed_ip['ip_address']
            floatingip_db = l3_models.FloatingIP(
                id=fip_id,
                tenant_id=fip['tenant_id'],
                status=initial_status,
                floating_network_id=fip['floating_network_id'],
                floating_ip_address=floating_ip_address,
                floating_port_id=external_port['id'],
                description=fip.get('description'))
            # Update association with internal port
            # and define external IP address
            assoc_result = self._update_fip_assoc(context, fip,
                                                  floatingip_db, external_port)
            context.session.add(floatingip_db)
            floatingip_dict = self._make_floatingip_dict(
                floatingip_db, process_extensions=False)
            if self._is_dns_integration_supported:
                dns_data = self._process_dns_floatingip_create_precommit(
                    context, floatingip_dict, fip)

        self._core_plugin.update_port(context.elevated(), external_port['id'],
                                      {'port': {'device_id': fip_id}})
        registry.notify(resources.FLOATING_IP,
                        events.AFTER_UPDATE,
                        self._update_fip_assoc,
                        **assoc_result)

        if self._is_dns_integration_supported:
            self._process_dns_floatingip_create_postcommit(context,
                                                           floatingip_dict,
                                                           dns_data)
        self._apply_dict_extend_functions(l3.FLOATINGIPS, floatingip_dict,
                                          floatingip_db)
        return floatingip_dict
