# Copyright (C) 2016 Midokura SARL.
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

from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_utils import excutils

from neutron_lib.plugins import constants as const
from neutron_lib.plugins import directory

from midonet.neutron.client import base as c_base
from midonet.neutron.common import config  # noqa
from midonet.neutron.common import constants as midonet_const
from midonet.neutron.db import logging_resource_db as log_res_db

LOG = logging.getLogger(__name__)


class MidonetLoggingResourcePlugin(log_res_db.LoggingResourceDbMixin):

    """Implements Logging Resource service plugin for Midonet."""

    supported_extension_aliases = ["logging-resource"]

    def __init__(self):
        super(MidonetLoggingResourcePlugin, self).__init__()

        # Instantiate MidoNet API client
        self.client = c_base.load_client(cfg.CONF.MIDONET)

    def get_plugin_type(self):
        return midonet_const.LOGGING_RESOURCE

    def get_plugin_description(self):
        """Returns string description of the plugin."""
        return "Midonet Logging Resource Service Plugin"

    @log_helpers.log_method_call
    def update_logging_resource(self, context, id, logging_resource):
        backup = self.get_logging_resource(
            context, id, fields=['name', 'description', 'enabled'])
        backup_body = {'logging_resource': backup}
        with context.session.begin(subtransactions=True):
            has_logs = self._logging_resource_has_logs(context, id)
            log_res = super(
                MidonetLoggingResourcePlugin,
                self).update_logging_resource(context, id, logging_resource)
            if has_logs:
                self.client.update_logging_resource_precommit(
                    context, id, log_res)

        if not has_logs:
            return log_res
        try:
            self.client.update_logging_resource_postcommit(id, log_res)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to update a logging "
                          "resource %(log_res_id)s in MidoNet: %(err)s",
                          {"log_res_id": log_res["id"], "err": ex})
                try:
                    super(
                        MidonetLoggingResourcePlugin,
                        self).update_logging_resource(
                            context, log_res['id'], backup_body)
                except Exception:
                    LOG.exception("Failed to update a logging resource "
                                  "for rollback %s", log_res["id"])
        return log_res

    @log_helpers.log_method_call
    def delete_logging_resource(self, context, id):
        with context.session.begin(subtransactions=True):
            super(MidonetLoggingResourcePlugin,
                  self).delete_logging_resource(context, id)
            self.client.delete_logging_resource_precommit(context, id)

        self.client.delete_logging_resource_postcommit(id)

    @log_helpers.log_method_call
    def create_logging_resource_firewall_log(self, context,
                                             firewall_log,
                                             logging_resource_id):
        with context.session.begin(subtransactions=True):
            f_log = super(
                MidonetLoggingResourcePlugin,
                self).create_logging_resource_firewall_log(
                    context, firewall_log, logging_resource_id)
            f_log_info = self._make_info_for_midonet(
                context, f_log, logging_resource_id)
            self.client.create_firewall_log_precommit(context, f_log_info)

        try:
            self.client.create_firewall_log_postcommit(f_log_info)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create a firewall log %(f_log_id)s "
                          "for %(log_res_id)s in Midonet:%(err)s",
                          {"f_log_id": f_log["id"],
                           "log_res_id": logging_resource_id, "err": ex})
                try:
                    super(
                        MidonetLoggingResourcePlugin,
                        self).delete_logging_resource_firewall_log(
                            context, f_log["id"], logging_resource_id)
                except Exception:
                    LOG.exception("Failed to delete a firewall_log %s",
                                  f_log["id"])

        return f_log

    @log_helpers.log_method_call
    def update_logging_resource_firewall_log(
            self, context, id, logging_resource_id, firewall_log):
        backup = self.get_logging_resource_firewall_log(
            context, id, logging_resource_id,
            fields=['fw_event', 'description'])
        backup_body = {'firewall_log': backup}
        with context.session.begin(subtransactions=True):
            f_log = super(
                MidonetLoggingResourcePlugin,
                self).update_logging_resource_firewall_log(
                    context, id, logging_resource_id, firewall_log)
            f_log_info = self._make_info_for_midonet(
                context, f_log, logging_resource_id)
            self.client.update_firewall_log_precommit(context, id, f_log_info)

        try:
            self.client.update_firewall_log_postcommit(id, f_log_info)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to update a firewall log "
                          "%(f_log_id)s in Midonet:%(err)s",
                          {"f_log_id": f_log["id"], "err": ex})
                try:
                    super(
                        MidonetLoggingResourcePlugin,
                        self).update_logging_resource_firewall_log(
                            context, f_log['id'],
                            logging_resource_id, backup_body)
                except Exception:
                    LOG.exception("Failed to update a firewall log "
                                  "for rollback %s", f_log["id"])
        return f_log

    @log_helpers.log_method_call
    def delete_logging_resource_firewall_log(self, context, id,
                                             logging_resource_id):
        with context.session.begin(subtransactions=True):
            super(MidonetLoggingResourcePlugin,
                  self).delete_logging_resource_firewall_log(
                context, id, logging_resource_id)
            self.client.delete_firewall_log_precommit(context, id)

        self.client.delete_firewall_log_postcommit(id)

    def _make_info_for_midonet(self, context, f_log, logging_resource_id):
        f_log_info = f_log.copy()
        # Get firewall and logging resource object for backend.
        fw_plugin = directory.get_plugin(const.FIREWALL)
        f_log_info['firewall'] = fw_plugin.get_firewall(
            context, f_log_info['firewall_id'], fields=['id', 'tenant_id'])
        f_log_info['logging_resource'] = self.get_logging_resource(
            context, logging_resource_id)
        del f_log_info['logging_resource']['firewall_logs']

        return f_log_info
