# Copyright 2015 Midokura SARL
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

from midonet.neutron.common import constants as m_const
from neutron.api.v2 import attributes
from neutron.common import exceptions as n_exc
from neutron.db import model_base
from neutron.db import models_v2
from neutron.extensions import providernet as pnet
from neutron import i18n
from neutron.plugins.common import constants as p_const
from oslo_log import log as logging
import sqlalchemy as sa
from sqlalchemy import orm


LOG = logging.getLogger(__name__)
_LW = i18n._LW


_MIDONET_TYPES = [
    p_const.TYPE_LOCAL,
    m_const.TYPE_MIDONET,
]


class NetworkBinding(model_base.BASEV2):
    __tablename__ = 'midonet_network_bindings'

    network_id = sa.Column(sa.String(36), sa.ForeignKey('networks.id',
                           ondelete="CASCADE"), primary_key=True)
    network_type = sa.Column(sa.String(length=255), nullable=False)
    network = orm.relationship(models_v2.Network,
                               backref=orm.backref("network_binding",
                                                   lazy='joined',
                                                   uselist=False,
                                                   cascade='delete'))


class MidonetProviderNetworkMixin(object):

    def _get_net_type(self, session, network_id):
        net_binding = session.query(NetworkBinding).filter_by(
            network_id=network_id).first()
        if net_binding:
            return net_binding.network_type
        return None

    def _extend_provider_network_dict(self, context, network):
        id = network['id']
        net_type = self._get_net_type(context.session, id)
        if net_type:
            network[pnet.NETWORK_TYPE] = net_type

    def _process_provider_create(self, network):

        net_type = network.get(pnet.NETWORK_TYPE)
        if not attributes.is_attr_set(net_type):
            return None

        if net_type in _MIDONET_TYPES:
            # NOTE(yamamoto): Accept a few well-known types as
            # the default type.  This is a workaround for Horizon, which
            # currently doesn't have a way to specify MidoNet network types
            # or "no provider network".
            # REVISIT(yamamoto): Clean this up once Horizon is fixed
            if net_type != m_const.TYPE_MIDONET:
                LOG.warning(_LW('Unsupported network type %(type)s detected '
                                'in a create network request.'),
                            {'type': net_type})
            return None

        if net_type != m_const.TYPE_UPLINK:
            msg = _('Unsupported network type %(type)s detected '
                    'in a create network request.') % {'type': net_type}
            raise n_exc.InvalidInput(error_message=msg)

        return net_type

    def _create_provider_network(self, context, network):
        net_type = self._process_provider_create(network)
        if net_type:
            with context.session.begin(subtransactions=True):
                context.session.add(NetworkBinding(network_id=network['id'],
                                                   network_type=net_type))

    def _match_attrs(self, net, filters):
        return (not filters.get(pnet.NETWORK_TYPE) or
                net.get(pnet.NETWORK_TYPE) in filters[pnet.NETWORK_TYPE])

    def _provider_network_matches_filters(self, network, filters):
        if not filters:
            return True

        if attributes.is_attr_set(network.get(pnet.NETWORK_TYPE)):
            return self._match_attrs(network, filters)
        else:
            return True

    def _filter_nets_provider(self, networks, filters):
        return [network
                for network in networks
                if self._provider_network_matches_filters(network, filters)
                ]
