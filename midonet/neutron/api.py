# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright (C) 2014 Midokura SARL.
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

from midonet.neutron.common import util
from midonet.neutron.extensions import bridge
from midonet.neutron.extensions import chain_rule
from midonet.neutron.extensions import host
from midonet.neutron.extensions import ip_addr_group
from midonet.neutron.extensions import license
from midonet.neutron.extensions import port
from midonet.neutron.extensions import routing_table

from neutron.api.v2 import base

CREATE = base.Controller.CREATE
DELETE = base.Controller.DELETE
LIST = base.Controller.LIST
SHOW = base.Controller.SHOW
UPDATE = base.Controller.UPDATE


@util.generate_methods(LIST, SHOW, CREATE, DELETE)
class BgpHandlerMixin(object):
    """The mixin of the request handler for the BGP."""


@util.generate_methods(LIST, SHOW, CREATE, DELETE)
class AdRouteHandlerMixin(object):
    """The mixin of the request handler for the advertised routes."""
    ALIAS = 'ad_route'


@util.generate_methods(LIST, SHOW, UPDATE, DELETE)
class HostHandlerMixin(host.HostPluginBase):
    """The mixin of the request handler for the hosts."""


@util.generate_methods(LIST, SHOW, CREATE, UPDATE, DELETE)
class BridgeHandlerMixin(bridge.BridgePluginBase):
    """The mixin of the request handler for the bridges."""


@util.generate_methods(LIST, SHOW, CREATE, UPDATE, DELETE)
class ChainHandlerMixin(chain_rule.ChainPluginBase):
    """The mixin of the request handler for the chains."""


@util.generate_methods(LIST, SHOW, CREATE, DELETE)
class RuleHandlerMixin(chain_rule.RulePluginBase):
    """The mixin of the request handler for the rules."""


@util.generate_methods(LIST, SHOW, CREATE, DELETE)
class IpAddrGroupHandlerMixin(ip_addr_group.IpAddrGroupPluginBase):
    ALIAS = 'ip_addr_group'


@util.generate_methods(LIST, SHOW, CREATE, DELETE)
class IpAddrGrouAddrHandlerMixin(ip_addr_group.IpAddrGroupAddrPluginBase):
    ALIAS = 'ip_addr_group_addr'


@util.generate_methods(LIST, SHOW, UPDATE, DELETE)
class LicenseHandlerMixin(license.LicensePluginBase):
    """The mixin of the request handler for the licenses."""


@util.generate_methods(LIST, SHOW, CREATE, UPDATE, DELETE)
class PortHandlerMixin(port.PortPluginBase):
    """The mixin of the request handler for the ports."""
    ALIAS = 'midonet_port'


@util.generate_methods(LIST, SHOW, CREATE, UPDATE, DELETE)
class RoutingTableHandlerMixin(routing_table.RoutingTablePluginBase):
    """The mixin of the request handler for the routing  tables."""
    ALIAS = 'routing_table'


@util.generate_methods(LIST, SHOW, CREATE, UPDATE, DELETE)
class TunnelzoneHandlerMixin(object):
    """The mixin of the request handler for the tunnel zones."""


@util.generate_methods(LIST, SHOW, CREATE, UPDATE, DELETE)
class TunnelzonehostHandlerMixin(object):
    """The mixin of the request handler for the tunnel zone hosts."""
    PARENT = TunnelzoneHandlerMixin.ALIAS


class MidoNetApiMixin(AdRouteHandlerMixin,
                      BgpHandlerMixin,
                      BridgeHandlerMixin,
                      ChainHandlerMixin,
                      RuleHandlerMixin,
                      HostHandlerMixin,
                      IpAddrGroupHandlerMixin,
                      IpAddrGrouAddrHandlerMixin,
                      LicenseHandlerMixin,
                      RoutingTableHandlerMixin,
                      TunnelzoneHandlerMixin,
                      TunnelzonehostHandlerMixin):
    """MidoNet REST API plugin."""
