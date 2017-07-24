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

import functools

from neutron_lib.api.definitions import provider_net

from neutron.plugins.ml2 import driver_context as ctx

from midonet.neutron._i18n import _
from midonet.neutron.common import constants as const


def is_midonet_network(context):
    """Checks whether the context is mech driver context for MidoNet driver """

    if isinstance(context, ctx.NetworkContext):
        net = context.current
    elif isinstance(context, ctx.PortContext):
        net = context.network.current
    elif isinstance(context, ctx.SubnetContext):
        net = context.network.current
    else:
        raise ValueError(_("Invalid Mechanism driver context passed in."))

    return net.get(provider_net.NETWORK_TYPE) in const.MIDONET_NET_TYPES


def filter_midonet_network(func):
    """Decorator to filter out only the midonet network type"""
    @functools.wraps(func)
    def wrapper(self, context):
        if is_midonet_network(context):
            func(self, context)
    return wrapper
