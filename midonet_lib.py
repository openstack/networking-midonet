# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2012 Midokura Japan K.K.
# Copyright (C) 2013 Midokura PTE LTD
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
#
# @author: Tomoe Sugihara, Midokura Japan KK
# @author: Ryu Ishimoto, Midokura Japan KK
# @author: Rossella Sblendido, Midokura Japan KK
# @author: Duarte Nunes, Midokura Japan KK

from midonetclient import exc
from webob import exc as w_exc

from neutron.common import exceptions as n_exc
from neutron.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def handle_api_error(fn):
    """Wrapper for methods that throws custom exceptions."""
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (w_exc.HTTPException,
                exc.MidoApiConnectionError) as ex:
            raise MidonetApiException(msg=ex)
    return wrapped


class MidonetResourceNotFound(n_exc.NotFound):
    message = _('MidoNet %(resource_type)s %(id)s could not be found')


class MidonetApiException(n_exc.NeutronException):
    message = _("MidoNet API error: %(msg)s")


class MidoClient:

    def __init__(self, mido_api):
        self.mido_api = mido_api

    @classmethod
    def _fill_dto(cls, dto, fields):
        for field_name, field_value in fields.iteritems():
            # We assume the setters are named the
            # same way as the attributes themselves.
            try:
                getattr(dto, field_name)(field_value)
            except AttributeError:
                pass
        return dto

    @classmethod
    def _create_dto(cls, dto, fields):
        return cls._fill_dto(dto, fields).create()

    @handle_api_error
    def get_bridge(self, id):
        """Get a bridge

        :param id: id of the bridge
        :returns: requested bridge. None if bridge does not exist.
        """
        LOG.debug(_("MidoClient.get_bridge called: id=%s"), id)
        try:
            return self.mido_api.get_bridge(id)
        except w_exc.HTTPNotFound:
            raise MidonetResourceNotFound(resource_type='Bridge', id=id)

    @handle_api_error
    def create_router(self, **kwargs):
        """Create a new router

        :param \**kwargs: configuration of the new router
        :returns: newly created router
        """
        LOG.debug(_("MidoClient.create_router called: "
                    "kwargs=%(kwargs)s"), {'kwargs': kwargs})
        return self._create_dto(self.mido_api.add_router(), kwargs)

    @handle_api_error
    def get_router(self, id):
        """Get a router with the given id

        :param id: id of the router
        :returns: requested router object.  None if it does not exist.
        """
        LOG.debug(_("MidoClient.get_router called: id=%(id)s"), {'id': id})
        try:
            return self.mido_api.get_router(id)
        except w_exc.HTTPNotFound:
            raise MidonetResourceNotFound(resource_type='Router', id=id)

    @handle_api_error
    def remove_rules_by_property(self, tenant_id, chain_name, key, value):
        """Remove all the rules that match the provided key and value."""
        LOG.debug(_("MidoClient.remove_rules_by_property called: "
                    "tenant_id=%(tenant_id)s, chain_name=%(chain_name)s"
                    "key=%(key)s, value=%(value)s"),
                  {'tenant_id': tenant_id, 'chain_name': chain_name,
                   'key': key, 'value': value})
        chain = self.get_chain_by_name(tenant_id, chain_name)
        if chain is None:
            raise MidonetResourceNotFound(resource_type='Chain',
                                          id=chain_name)

        for r in chain.get_rules():
            if key in r.get_properties():
                if r.get_properties()[key] == value:
                    self.mido_api.delete_rule(r.get_id())

    @handle_api_error
    def get_link_port(self, router, peer_router_id):
        """Setup a route on the router to the next hop router."""
        LOG.debug(_("MidoClient.get_link_port called: "
                    "router=%(router)s, peer_router_id=%(peer_router_id)s"),
                  {'router': router, 'peer_router_id': peer_router_id})
        # Find the port linked between the two routers
        link_port = None
        for p in router.get_peer_ports():
            if p.get_device_id() == peer_router_id:
                link_port = p
                break
        return link_port

    @handle_api_error
    def add_router_route(self, router, type='Normal',
                         src_network_addr=None, src_network_length=None,
                         dst_network_addr=None, dst_network_length=None,
                         next_hop_port=None, next_hop_gateway=None,
                         weight=100):
        """Setup a route on the router."""
        return self.mido_api.add_router_route(
            router, route_type=type, src_network_addr=src_network_addr,
            src_network_length=src_network_length,
            dst_network_addr=dst_network_addr,
            dst_network_length=dst_network_length,
            next_hop_port=next_hop_port, next_hop_gateway=next_hop_gateway,
            weight=weight)

    @handle_api_error
    def add_static_nat(self, tenant_id, chain_name, from_ip, to_ip, port_id,
                       nat_type='dnat', **kwargs):
        """Add a static NAT entry

        :param tenant_id: owner fo the chain to add a NAT to
        :param chain_name: name of the chain to add a NAT to
        :param from_ip: IP to translate from
        :param from_ip: IP to translate from
        :param to_ip: IP to translate to
        :param port_id: port to match on
        :param nat_type: 'dnat' or 'snat'
        """
        LOG.debug(_("MidoClient.add_static_nat called: "
                    "tenant_id=%(tenant_id)s, chain_name=%(chain_name)s, "
                    "from_ip=%(from_ip)s, to_ip=%(to_ip)s, "
                    "port_id=%(port_id)s, nat_type=%(nat_type)s"),
                  {'tenant_id': tenant_id, 'chain_name': chain_name,
                   'from_ip': from_ip, 'to_ip': to_ip,
                   'portid': port_id, 'nat_type': nat_type})
        if nat_type not in ['dnat', 'snat']:
            raise ValueError(_("Invalid NAT type passed in %s") % nat_type)

        chain = self.get_chain_by_name(tenant_id, chain_name)
        nat_targets = []
        nat_targets.append(
            {'addressFrom': to_ip, 'addressTo': to_ip,
             'portFrom': 0, 'portTo': 0})

        rule = chain.add_rule().type(nat_type).flow_action('accept').position(
            1).nat_targets(nat_targets).properties(kwargs)

        if nat_type == 'dnat':
            rule = rule.nw_dst_address(from_ip).nw_dst_length(32).in_ports(
                [port_id])
        else:
            rule = rule.nw_src_address(from_ip).nw_src_length(32).out_ports(
                [port_id])

        return rule.create()

    @handle_api_error
    def remove_static_route(self, router, ip):
        """Remove static route for the IP

        :param router: next hop router to remove the routes to
        :param ip: IP address of the route to remove
        """
        LOG.debug(_("MidoClient.remote_static_route called: "
                    "router=%(router)s, ip=%(ip)s"),
                  {'router': router, 'ip': ip})
        for r in router.get_routes():
            if (r.get_dst_network_addr() == ip and
                    r.get_dst_network_length() == 32):
                self.mido_api.delete_route(r.get_id())
