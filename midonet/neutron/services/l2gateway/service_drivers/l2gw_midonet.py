# Copyright (C) 2015 Midokura SARL
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import abc

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils
import six

from networking_l2gw.services.l2gateway.common import constants
from networking_l2gw.services.l2gateway import service_drivers

from midonet.neutron.client import base as c_base
from midonet.neutron.common import config  # noqa

LOG = logging.getLogger(__name__)


# TODO(yamamoto): Update for the new driver API (See bug 1577339)
# and override precommit methods for task-based api.


@six.add_metaclass(abc.ABCMeta)
class MidonetL2gwDriver(service_drivers.L2gwDriver):
    """L2GW MidoNet Service Driver class."""

    def __init__(self, service_plugin, validator=None):
        super(MidonetL2gwDriver, self).__init__(service_plugin,
                                                validator=validator)
        self.service_plugin = service_plugin
        self.client = c_base.load_client(cfg.CONF.MIDONET)

    @property
    def service_type(self):
        return 'l2gw'

    def add_port_mac(self, context, port_dict):
        raise NotImplementedError()

    def delete_port_mac(self, context, port):
        raise NotImplementedError()

    def _validate_gw_connection(self, context, gw_connection):
        network_id = gw_connection.get(constants.NETWORK_ID)
        self.service_plugin._get_network(context, network_id)

    def _make_gateway_dict(self, context, gw_id):
        gw = self.service_plugin._get_l2_gateway(context, gw_id)
        return self.service_plugin._make_l2_gateway_dict(gw)

    def _make_gateway_conn_dict(self, context, gw_connection):
        gw_conn_dict = self.service_plugin._make_l2gw_connections_dict(
            gw_connection)
        gw_conn_dict['l2_gateway'] = self._make_gateway_dict(
            context, gw_connection["l2_gateway_id"])
        return gw_conn_dict

    def create_l2_gateway_connection(self, context, l2_gateway_connection):
        gw_connection = l2_gateway_connection.get(
            self.service_plugin.connection_resource)

        gw_conn_dict = self._make_gateway_conn_dict(context, gw_connection)
        self._validate_gw_connection(context, gw_conn_dict)
        if not gw_conn_dict[constants.SEG_ID]:
            seg_id = self.service_plugin._get_l2_gateway_seg_id(
                context, gw_conn_dict['l2_gateway_id'])
            gw_conn_dict[constants.SEG_ID] = seg_id
        try:
            self.client.create_l2_gateway_connection(context,
                                                     gw_conn_dict)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create L2GW Conn %(l2_gw_conn)s "
                          "in Midonet: %(err)s",
                          {"l2_gw_conn": gw_connection, "err": ex})

    def delete_l2_gateway_connection(self, context, l2_gateway_connection):
        try:
            self.client.delete_l2_gateway_connection(context,
                                                     l2_gateway_connection)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to delete a l2 Gateway Connection"
                          "%(l2_gw_conn_id)s in Midonet: %(err)s",
                          {"l2_gw_conn_id": l2_gateway_connection, "err": ex})
