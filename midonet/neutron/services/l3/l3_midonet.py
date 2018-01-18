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

from neutron_lib.api.definitions import l3 as l3_apidef
from neutron_lib.api.definitions import multiprovidernet as mpnet_apidef
from neutron_lib.api.definitions import provider_net as pnet
from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib.callbacks import resources
from neutron_lib import constants as n_const
from neutron_lib import exceptions as n_exc
from neutron_lib.plugins import constants as plugin_constants
from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_utils import excutils

from neutron.api import extensions as neutron_extensions
from neutron.db import api as db_api
from neutron.db import common_db_mixin
from neutron.db import extraroute_db
# Import l3_dvr_db to get the config options required for FWaaS
from neutron.db import l3_dvr_db  # noqa

from midonet.neutron.client import base as c_base
from midonet.neutron.common import config  # noqa
from midonet.neutron.common import constants as m_const
from midonet.neutron.db import l3_db_midonet
from midonet.neutron import extensions
from midonet.neutron.extensions import routerinterfacefip

LOG = logging.getLogger(__name__)


@registry.has_registry_receivers
class MidonetL3ServicePlugin(common_db_mixin.CommonDbMixin,
                             extraroute_db.ExtraRoute_db_mixin,
                             l3_db_midonet.MidonetL3DBMixin):

    """Implements L3 Router service plugin for Midonet."""

    supported_extension_aliases = ["router", "extraroute", "ext-gw-mode",
                                   "router-interface-fip", "fip64"]

    __native_pagination_support = True
    __native_sorting_support = True

    def __init__(self):
        super(MidonetL3ServicePlugin, self).__init__()

        # Instantiate MidoNet API client
        self.client = c_base.load_client(cfg.CONF.MIDONET)

        # Avoid any side effect from DVR getting set to true
        cfg.CONF.set_override("router_distributed", False)
        neutron_extensions.append_api_extensions_path(extensions.__path__)

    @classmethod
    def get_plugin_type(cls):
        return plugin_constants.L3

    def get_plugin_description(self):
        """Returns string description of the plugin."""
        return ("Midonet L3 Router Service Plugin")

    @staticmethod
    def _segments(network):
        if pnet.NETWORK_TYPE in network:
            yield {
                pnet.NETWORK_TYPE: network[pnet.NETWORK_TYPE],
            }
        segments = network.get(mpnet_apidef.SEGMENTS)
        if segments:
            for seg in segments:
                yield seg

    def _validate_network_type(self, context, network_id):
        our_types = [m_const.TYPE_MIDONET, m_const.TYPE_UPLINK]
        network = self._core_plugin.get_network(context, network_id)
        for seg in self._segments(network):
            if seg[pnet.NETWORK_TYPE] in our_types:
                return
        LOG.warning("Incompatible network %s", network)
        raise n_exc.BadRequest(resource='router', msg='Incompatible network')

    def _validate_router_gw_network(self, context, r):
        ext_gw_info = r.get(l3_apidef.EXTERNAL_GW_INFO)
        if ext_gw_info:
            self._validate_network_type(context, ext_gw_info['network_id'])

    @log_helpers.log_method_call
    @db_api.retry_if_session_inactive()
    def create_router(self, context, router):
        with db_api.context_manager.writer.using(context):
            # REVISIT(yamamoto): This should not call create_port inside
            # of a transaction.
            setattr(context, 'GUARD_TRANSACTION', False)
            r = super(MidonetL3ServicePlugin, self).create_router(context,
                                                                  router)
            self._validate_router_gw_network(context, r)
            self.client.create_router_precommit(context, r)

        try:
            self.client.create_router_postcommit(r)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create a router %(r_id)s in Midonet:"
                          "%(err)s", {"r_id": r["id"], "err": ex})
                try:
                    self.delete_router(context, r['id'])
                except Exception:
                    LOG.exception("Failed to delete a router %s", r["id"])
        return r

    @log_helpers.log_method_call
    @db_api.retry_if_session_inactive()
    def update_router(self, context, id, router):
        with db_api.context_manager.writer.using(context):
            # REVISIT(yamamoto): Updating external_gateway_info causes
            # create_port/delete_port.  This should not call them inside of
            # a transaction.
            setattr(context, 'GUARD_TRANSACTION', False)
            r = super(MidonetL3ServicePlugin, self).update_router(context, id,
                                                                  router)
            self._validate_router_gw_network(context, r)
            self.client.update_router_precommit(context, id, r)

        try:
            self.client.update_router_postcommit(id, r)
            if r['status'] != m_const.ROUTER_STATUS_ACTIVE:
                data = {'router': {'status': m_const.ROUTER_STATUS_ACTIVE}}
                r = super(MidonetL3ServicePlugin, self).update_router(
                    context, id, data)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to update a router %(r_id)s in MidoNet: "
                          "%(err)s", {"r_id": id, "err": ex})
                try:
                    data = {'router': {'status': m_const.ROUTER_STATUS_ERROR}}
                    super(MidonetL3ServicePlugin, self).update_router(
                        context, id, data)
                except Exception:
                    LOG.exception("Failed to update a router status %s", id)
        return r

    @log_helpers.log_method_call
    @db_api.retry_if_session_inactive()
    def delete_router(self, context, id):
        self._check_router_not_in_use(context, id)

        with db_api.context_manager.writer.using(context):
            # REVISIT(yamamoto): This should not call delete_port inside
            # of a transaction.
            setattr(context, 'GUARD_TRANSACTION', False)
            super(MidonetL3ServicePlugin, self).delete_router(context, id)
            self.client.delete_router_precommit(context, id)

        self.client.delete_router_postcommit(id)

    @log_helpers.log_method_call
    @db_api.retry_if_session_inactive()
    def add_router_interface(self, context, router_id, interface_info):
        by_port = bool(interface_info.get('port_id'))
        with db_api.context_manager.writer.using(context):
            # REVISIT(yamamoto): This should not call create_port/update_port
            # inside of a transaction.
            setattr(context, 'GUARD_TRANSACTION', False)
            info = super(MidonetL3ServicePlugin, self).add_router_interface(
                context, router_id, interface_info)
            self._validate_network_type(context, info['network_id'])
            self.client.add_router_interface_precommit(context, router_id,
                                                       info)

        try:
            self.client.add_router_interface_postcommit(router_id, info)
        except Exception as ex:
            LOG.error("Failed to create MidoNet resources to add router "
                      "interface. info=%(info)s, router_id=%(router_id)s, "
                      "error=%(err)r",
                      {"info": info, "router_id": router_id, "err": ex})
            with excutils.save_and_reraise_exception():
                if not by_port:
                    self.remove_router_interface(context, router_id, info)

        return info

    @log_helpers.log_method_call
    @db_api.retry_if_session_inactive()
    def remove_router_interface(self, context, router_id, interface_info):
        with db_api.context_manager.writer.using(context):
            # REVISIT(yamamoto): This should not call delete_port inside
            # of a transaction.
            setattr(context, 'GUARD_TRANSACTION', False)
            info = super(MidonetL3ServicePlugin, self).remove_router_interface(
                context, router_id, interface_info)
            self.client.remove_router_interface_precommit(context, router_id,
                                                          info)

        self.client.remove_router_interface_postcommit(router_id, info)
        return info

    @log_helpers.log_method_call
    @db_api.retry_if_session_inactive()
    def create_floatingip(self, context, floatingip):
        with db_api.context_manager.writer.using(context):
            # REVISIT(yamamoto): This should not call create_port inside
            # of a transaction.
            setattr(context, 'GUARD_TRANSACTION', False)
            fip = super(MidonetL3ServicePlugin, self).create_floatingip(
                context, floatingip)
            self.client.create_floatingip_precommit(context, fip)

        try:
            self.client.create_floatingip_postcommit(fip)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create floating ip %(fip)s: %(err)s",
                          {"fip": fip, "err": ex})
                try:
                    self.delete_floatingip(context, fip['id'])
                except Exception:
                    LOG.exception("Failed to delete a floating ip %s",
                                  fip['id'])
        return fip

    @log_helpers.log_method_call
    @db_api.retry_if_session_inactive()
    def delete_floatingip(self, context, id):
        with db_api.context_manager.writer.using(context):
            # REVISIT(yamamoto): This should not call delete_port inside
            # of a transaction.
            setattr(context, 'GUARD_TRANSACTION', False)
            super(MidonetL3ServicePlugin, self).delete_floatingip(context, id)
            self.client.delete_floatingip_precommit(context, id)

        self.client.delete_floatingip_postcommit(id)

    @log_helpers.log_method_call
    @db_api.retry_if_session_inactive()
    def update_floatingip(self, context, id, floatingip):
        with db_api.context_manager.writer.using(context):
            fip = super(MidonetL3ServicePlugin, self).update_floatingip(
                context, id, floatingip)
            self.client.update_floatingip_precommit(context, id, fip)

            # Update status based on association
            if fip.get('port_id') is None:
                new_status = n_const.FLOATINGIP_STATUS_DOWN
            else:
                new_status = n_const.FLOATINGIP_STATUS_ACTIVE
            self.update_floatingip_status(context, id, new_status)

        try:
            self.client.update_floatingip_postcommit(id, fip)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to update a floating ip "
                          "%(fip_id)s in MidoNet: %(err)s",
                          {"fip_id": id, "err": ex})
                try:
                    self.update_floatingip_status(
                        context, id, n_const.FLOATINGIP_STATUS_ERROR)
                except Exception:
                    LOG.exception("Failed to update floating ip status %s",
                                  id)
        return fip

    @registry.receives(resources.ROUTER_INTERFACE, [events.BEFORE_DELETE])
    def _check_router_interface_used_as_gw_for_fip(self, resource,
                                                   event, trigger, **kwargs):
        context = kwargs['context']
        router_id = kwargs['router_id']
        subnet_id = kwargs['subnet_id']
        if self._subnet_has_fip(context, router_id, subnet_id):
            raise routerinterfacefip.RouterInterfaceInUseAsGatewayByFloatingIP(
                router_id=router_id, subnet_id=subnet_id)
