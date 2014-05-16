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

    @classmethod
    def _update_dto(cls, dto, fields):
        return cls._fill_dto(dto, fields).update()

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
    def delete_port(self, id, delete_chains=False):
        """Delete a port

        :param id: id of the port
        """
        LOG.debug(_("MidoClient.delete_port called: id=%(id)s, "
                    "delete_chains=%(delete_chains)s"),
                  {'id': id, 'delete_chains': delete_chains})
        if delete_chains:
            self.delete_port_chains(id)

        self.mido_api.delete_port(id)

    @handle_api_error
    def get_port(self, id):
        """Get a port

        :param id: id of the port
        :returns: requested port. None if it does not exist
        """
        LOG.debug(_("MidoClient.get_port called: id=%(id)s"), {'id': id})
        try:
            return self.mido_api.get_port(id)
        except w_exc.HTTPNotFound:
            raise MidonetResourceNotFound(resource_type='Port', id=id)

    @handle_api_error
    def add_bridge_port(self, bridge, **kwargs):
        """Add a port on a bridge

        :param bridge: bridge to add a new port to
        :param \**kwargs: configuration of the new port
        :returns: newly created port
        """
        LOG.debug(_("MidoClient.add_bridge_port called: "
                    "bridge=%(bridge)s, kwargs=%(kwargs)s"),
                  {'bridge': bridge, 'kwargs': kwargs})
        return self._create_dto(self.mido_api.add_bridge_port(bridge), kwargs)

    @handle_api_error
    def add_router_port(self, router, **kwargs):
        """Add a new port to an existing router.

        :param router: router to add a new port to
        :param \**kwargs: configuration of the new port
        :returns: newly created port
        """
        return self._create_dto(self.mido_api.add_router_port(router), kwargs)

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
    def delete_router(self, id):
        """Delete a router

        :param id: id of the router
        """
        LOG.debug(_("MidoClient.delete_router called: id=%(id)s"), {'id': id})
        return self.mido_api.delete_router(id)

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
    def update_router(self, id, **kwargs):
        """Update a router of the given id with the new name

        :param id: id of the router
        :param \**kwargs: the fields to update and their values
        :returns: router object
        """
        LOG.debug(_("MidoClient.update_router called: "
                    "id=%(id)s, kwargs=%(kwargs)s"),
                  {'id': id, 'kwargs': kwargs})
        try:
            return self._update_dto(self.mido_api.get_router(id), kwargs)
        except w_exc.HTTPNotFound:
            raise MidonetResourceNotFound(resource_type='Router', id=id)

    @handle_api_error
    def delete_route(self, id):
        return self.mido_api.delete_route(id)

    @handle_api_error
    def link(self, port, peer_id):
        """Link a port to a given peerId."""
        self.mido_api.link(port, peer_id)

    @handle_api_error
    def delete_port_routes(self, routes, port_id):
        """Remove routes whose next hop port is the given port ID."""
        for route in routes:
            if route.get_next_hop_port() == port_id:
                self.mido_api.delete_route(route.get_id())

    @handle_api_error
    def get_router_routes(self, router_id):
        """Get all routes for the given router."""
        return self.mido_api.get_router_routes(router_id)

    @handle_api_error
    def unlink(self, port):
        """Unlink a port

        :param port: port object
        """
        LOG.debug(_("MidoClient.unlink called: port=%(port)s"),
                  {'port': port})
        if port.get_peer_id():
            self.mido_api.unlink(port)
        else:
            LOG.warn(_("Attempted to unlink a port that was not linked. %s"),
                     port.get_id())

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
    def add_router_chains(self, router, inbound_chain_name,
                          outbound_chain_name):
        """Create chains for a new router.

        Creates inbound and outbound chains for the router with the given
        names, and the new chains are set on the router.

        :param router: router to set chains for
        :param inbound_chain_name: Name of the inbound chain
        :param outbound_chain_name: Name of the outbound chain
        """
        LOG.debug(_("MidoClient.create_router_chains called: "
                    "router=%(router)s, inbound_chain_name=%(in_chain)s, "
                    "outbound_chain_name=%(out_chain)s"),
                  {"router": router, "in_chain": inbound_chain_name,
                   "out_chain": outbound_chain_name})
        tenant_id = router.get_tenant_id()

        inbound_chain = self.mido_api.add_chain().tenant_id(tenant_id).name(
            inbound_chain_name,).create()
        outbound_chain = self.mido_api.add_chain().tenant_id(tenant_id).name(
            outbound_chain_name).create()

        # set chains to in/out filters
        router.inbound_filter_id(inbound_chain.get_id()).outbound_filter_id(
            outbound_chain.get_id()).update()
        return inbound_chain, outbound_chain

    @handle_api_error
    def delete_router_chains(self, id):
        """Deletes chains of a router.

        :param id: router ID to delete chains of
        """
        LOG.debug(_("MidoClient.delete_router_chains called: "
                    "id=%(id)s"), {'id': id})
        router = self.get_router(id)
        if (router.get_inbound_filter_id()):
            self.mido_api.delete_chain(router.get_inbound_filter_id())

        if (router.get_outbound_filter_id()):
            self.mido_api.delete_chain(router.get_outbound_filter_id())

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
    def add_dynamic_snat(self, tenant_id, pre_chain_name, post_chain_name,
                         snat_ip, port_id, **kwargs):
        """Add SNAT masquerading rule

        MidoNet requires two rules on the router, one to do NAT to a range of
        ports, and another to retrieve back the original IP in the return
        flow.
        """
        pre_chain = self.get_chain_by_name(tenant_id, pre_chain_name)
        post_chain = self.get_chain_by_name(tenant_id, post_chain_name)

        pre_chain.add_rule().nw_dst_address(snat_ip).nw_dst_length(
            32).type('rev_snat').flow_action('accept').in_ports(
                [port_id]).properties(kwargs).position(1).create()

        nat_targets = []
        nat_targets.append(
            {'addressFrom': snat_ip, 'addressTo': snat_ip,
             'portFrom': 1, 'portTo': 65535})

        post_chain.add_rule().type('snat').flow_action(
            'accept').nat_targets(nat_targets).out_ports(
                [port_id]).properties(kwargs).position(1).create()

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

    @handle_api_error
    def create_chain(self, tenant_id, name):
        """Create a new chain."""
        LOG.debug(_("MidoClient.create_chain called: tenant_id=%(tenant_id)s "
                    " name=%(name)s"), {"tenant_id": tenant_id, "name": name})
        return self.mido_api.add_chain().tenant_id(tenant_id).name(
            name).create()

    @handle_api_error
    def delete_chain(self, id):
        """Delete chain matching the ID."""
        LOG.debug(_("MidoClient.delete_chain called: id=%(id)s"), {"id": id})
        self.mido_api.delete_chain(id)

    @handle_api_error
    def get_chain_by_name(self, tenant_id, name):
        """Get the chain by its name."""
        LOG.debug(_("MidoClient.get_chain_by_name called: "
                    "tenant_id=%(tenant_id)s name=%(name)s "),
                  {"tenant_id": tenant_id, "name": name})
        for c in self.mido_api.get_chains({'tenant_id': tenant_id}):
            if c.get_name() == name:
                return c
        return None

    @handle_api_error
    def add_chain_rule(self, chain, action='accept', **kwargs):
        """Create a new accept chain rule."""
        self.mido_api.add_chain_rule(chain, action, **kwargs)
