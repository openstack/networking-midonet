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

from midonet.neutron.client import base as c_base
from midonet.neutron.common import config  # noqa
from midonet.neutron import extensions

from neutron.api import extensions as neutron_extensions
from neutron.common import constants as n_const
from neutron.db import common_db_mixin
from neutron.db import extraroute_db
# Import l3_dvr_db to get the config options required for FWaaS
from neutron.db import l3_dvr_db  # noqa
from neutron.db import l3_gwmode_db
from neutron import i18n
from neutron.plugins.common import constants
from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_utils import excutils

LOG = logging.getLogger(__name__)
_LE = i18n._LE
_LW = i18n._LW


class MidonetL3ServicePlugin(common_db_mixin.CommonDbMixin,
                             extraroute_db.ExtraRoute_db_mixin,
                             l3_gwmode_db.L3_NAT_db_mixin):

    """
    Implements L3 Router service plugin for Midonet.
    """

    supported_extension_aliases = ["router", "extraroute", "ext-gw-mode"]

    def __init__(self):
        super(MidonetL3ServicePlugin, self).__init__()

        # Instantiate MidoNet API client
        self.client = c_base.load_client(cfg.CONF.MIDONET)

        # Avoid any side effect from DVR getting set to true
        cfg.CONF.set_override("router_distributed", False)
        neutron_extensions.append_api_extensions_path(extensions.__path__)

    def get_plugin_type(self):
        return constants.L3_ROUTER_NAT

    def get_plugin_description(self):
        """Returns string description of the plugin."""
        return ("Midonet L3 Router Service Plugin")

    @log_helpers.log_method_call
    def create_router(self, context, router):
        with context.session.begin(subtransactions=True):
            r = super(MidonetL3ServicePlugin, self).create_router(context,
                                                                  router)
            self.client.create_router_precommit(context, r)

        try:
            self.client.create_router_postcommit(r)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to create a router %(r_id)s in Midonet:"
                              "%(err)s"), {"r_id": r["id"], "err": ex})
                try:
                    self.delete_router(context, r['id'])
                except Exception:
                    LOG.exception(_LE("Failed to delete a router %s"), r["id"])
        return r

    @log_helpers.log_method_call
    def update_router(self, context, id, router):
        with context.session.begin(subtransactions=True):
            r = super(MidonetL3ServicePlugin, self).update_router(context, id,
                                                                  router)
            self.client.update_router_precommit(context, id, r)

        self.client.update_router_postcommit(id, r)
        return r

    @log_helpers.log_method_call
    def delete_router(self, context, id):
        with context.session.begin(subtransactions=True):
            super(MidonetL3ServicePlugin, self).delete_router(context, id)
            self.client.delete_router_precommit(context, id)

        self.client.delete_router_postcommit(id)

    @log_helpers.log_method_call
    def add_router_interface(self, context, router_id, interface_info):
        by_port = bool(interface_info.get('port_id'))
        with context.session.begin(subtransactions=True):
            info = super(MidonetL3ServicePlugin, self).add_router_interface(
                context, router_id, interface_info)
            self.client.add_router_interface_precommit(context, router_id,
                                                       info)

        try:
            self.client.add_router_interface_postcommit(router_id, info)
        except Exception as ex:
            LOG.error(_LE("Failed to create MidoNet resources to add router "
                          "interface. info=%(info)s, router_id=%(router_id)s, "
                          "error=%(err)r"),
                      {"info": info, "router_id": router_id, "err": ex})
            with excutils.save_and_reraise_exception():
                if not by_port:
                    self.remove_router_interface(context, router_id, info)

        return info

    @log_helpers.log_method_call
    def remove_router_interface(self, context, router_id, interface_info):
        with context.session.begin(subtransactions=True):
            info = super(MidonetL3ServicePlugin, self).remove_router_interface(
                context, router_id, interface_info)
            self.client.remove_router_interface_precommit(context, router_id,
                                                          info)

        self.client.remove_router_interface_postcommit(router_id, info)
        return info

    @log_helpers.log_method_call
    def create_floatingip(self, context, floatingip):
        with context.session.begin(subtransactions=True):
            fip = super(MidonetL3ServicePlugin, self).create_floatingip(
                context, floatingip)
            self.client.create_floatingip_precommit(context, fip)

        try:
            self.client.create_floatingip_postcommit(fip)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to create floating ip %(fip)s: %(err)s"),
                          {"fip": fip, "err": ex})
                try:
                    self.delete_floatingip(context, fip['id'])
                except Exception:
                    LOG.exception(_LE("Failed to delete a floating ip %s"),
                                  fip['id'])
        return fip

    @log_helpers.log_method_call
    def delete_floatingip(self, context, id):
        with context.session.begin(subtransactions=True):
            super(MidonetL3ServicePlugin, self).delete_floatingip(context, id)
            self.client.delete_floatingip_precommit(context, id)

        self.client.delete_floatingip_postcommit(id)

    @log_helpers.log_method_call
    def update_floatingip(self, context, id, floatingip):
        with context.session.begin(subtransactions=True):
            fip = super(MidonetL3ServicePlugin, self).update_floatingip(
                context, id, floatingip)
            self.client.update_floatingip_precommit(context, id, fip)

            # Update status based on association
            if fip.get('port_id') is None:
                fip['status'] = n_const.FLOATINGIP_STATUS_DOWN
            else:
                fip['status'] = n_const.FLOATINGIP_STATUS_ACTIVE
            self.update_floatingip_status(context, id, fip['status'])

        self.client.update_floatingip_postcommit(id, fip)
        return fip
