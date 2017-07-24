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

from neutron_lib.api import validators
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_utils import excutils

from networking_l2gw import extensions as l2gateway_ext
from networking_l2gw.services.l2gateway.common import l2gw_validators
from networking_l2gw.services.l2gateway import plugin as l2gw_plugin
from neutron.api import extensions as neutron_extensions

from midonet.neutron.common import constants as mido_const
from midonet.neutron.db import l2gateway_midonet as l2gw_db
from midonet.neutron.services.l2gateway.common import l2gw_midonet_validators

LOG = logging.getLogger(__name__)


class MidonetL2GatewayPlugin(l2gw_plugin.L2GatewayPlugin,
                             l2gw_db.MidonetL2GatewayMixin):
    """Implementation of the Neutron l2 gateway Service Plugin.

    This class manages the workflow of Midonet l2 Gateway request/response.
    The base plugin methods are overridden because the MidoNet driver requires
    specific ordering of events.  For creation, the Neutron data must be
    created first, with the resource UUID generated.  Also, for both creation
    and deletion, by invoking the Neutron DB methods first, all the
    validations, such as 'check_admin()' are executed prior to attempting to
    modify the MidoNet data, preventing potential data inconsistency.
    """

    def __init__(self):
        # Dynamically change the validators so that they are applicable to
        # the MidoNet implementation of L2GW.
        # REVISIT(yamamoto): These validator modifications should not
        # have been here in the first place.  We should either put them
        # in upstream or remove them.
        l2gw_validators.validate_gwdevice_list = (l2gw_midonet_validators.
                                                  validate_gwdevice_list)
        val_type = validators._to_validation_type('l2gwdevice_list')
        validators.validators.pop(val_type, None)
        validators.add_validator(
            val_type,
            l2gw_midonet_validators.validate_gwdevice_list)
        l2gw_validators.validate_network_mapping_list = (
            l2gw_midonet_validators.
            validate_network_mapping_list_without_seg_id_validation)
        neutron_extensions.append_api_extensions_path(l2gateway_ext.__path__)
        super(MidonetL2GatewayPlugin, self).__init__()

    def add_port_mac(self, context, port_dict):
        # This function is not implemented now in MidoNet plugin.
        # We block this function in plugin level to prevent from loading
        # l2gw driver in upstream.
        self._get_driver_for_provider(mido_const.MIDONET_L2GW_PROVIDER
                                      ).add_port_mac(context, port_dict)

    def delete_port_mac(self, context, port):
        # This function is not implemented now in MidoNet plugin.
        # We block this function in plugin level to prevent from loading
        # l2gw driver in upstream.
        self._get_driver_for_provider(mido_const.MIDONET_L2GW_PROVIDER
                                      ).delete_port_mac(context, port)

    def create_l2_gateway(self, context, l2_gateway):
        # Gateway Device Management Service must be enabled
        # when Midonet L2 Gateway is used.
        self._check_and_get_gw_dev_service()
        self.validate_l2_gateway_for_create(context, l2_gateway)

        return l2gw_db.MidonetL2GatewayMixin.create_l2_gateway(
            self, context, l2_gateway)

    @log_helpers.log_method_call
    def create_l2_gateway_connection(self, context, l2_gateway_connection):

        self.validate_l2_gateway_connection_for_create(
            context, l2_gateway_connection)
        l2_gw_conn = (l2gw_db.MidonetL2GatewayMixin.
                      create_l2_gateway_connection(
                          self, context, l2_gateway_connection))

        # Copy over the ID so that the MidoNet driver knows about it.  ID is
        # necessary for MidoNet to process its translation.
        gw_connection = l2_gateway_connection[self.connection_resource]
        gw_connection["id"] = l2_gw_conn["id"]

        try:
            self._get_driver_for_provider(mido_const.MIDONET_L2GW_PROVIDER
                                          ).create_l2_gateway_connection(
                context, l2_gateway_connection)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create a l2 gateway connection "
                          "%(gw_conn_id)s in Midonet:%(err)s",
                          {"gw_conn_id": l2_gw_conn["id"], "err": ex})
                try:
                    l2gw_db.MidonetL2GatewayMixin.delete_l2_gateway_connection(
                        self, context, l2_gw_conn["id"])
                except Exception:
                    LOG.exception("Failed to delete a l2 gateway conn %s",
                                  l2_gw_conn["id"])
        return l2_gw_conn

    @log_helpers.log_method_call
    def delete_l2_gateway_connection(self, context, l2_gateway_connection):
        l2gw_db.MidonetL2GatewayMixin.delete_l2_gateway_connection(
            self, context, l2_gateway_connection)
        self._get_driver_for_provider(mido_const.MIDONET_L2GW_PROVIDER
                                      ).delete_l2_gateway_connection(
            context, l2_gateway_connection)
