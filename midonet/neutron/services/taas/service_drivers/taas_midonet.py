# Copyright (C) 2016 Midokura SARL
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

from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_utils import excutils

from neutron_taas.services.taas import service_drivers as taas_service_drivers

from midonet.neutron.client import base as c_base
from midonet.neutron.common import config  # noqa

LOG = logging.getLogger(__name__)


class MidonetTaasDriver(taas_service_drivers.TaasBaseDriver):
    """Midonet Taas Service Driver class"""

    def __init__(self, service_plugin):
        LOG.debug("Loading MidonetTaasDriver.")
        self.client = c_base.load_client(cfg.CONF.MIDONET)
        super(MidonetTaasDriver, self).__init__(service_plugin)

    @log_helpers.log_method_call
    def create_tap_service_precommit(self, context):
        # TODO(yamamoto): Call self.client for task-based api
        pass

    @log_helpers.log_method_call
    def create_tap_service_postcommit(self, context):
        try:
            ts = context.tap_service
            self.client.create_tap_service(context._plugin_context, ts)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create tap service %(tap_service)s "
                          "in Midonet: %(err)s",
                          {"tap_service": ts, "err": ex})

    @log_helpers.log_method_call
    def delete_tap_service_precommit(self, context):
        # TODO(yamamoto): Call self.client for task-based api
        pass

    @log_helpers.log_method_call
    def delete_tap_service_postcommit(self, context):
        try:
            ts = context.tap_service
            self.client.delete_tap_service(context._plugin_context, ts['id'])
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to delete a tap service"
                          "%(tap_service)s in Midonet: %(err)s",
                          {"tap_service": ts['id'], "err": ex})

    @log_helpers.log_method_call
    def create_tap_flow_precommit(self, context):
        # TODO(yamamoto): Call self.client for task-based api
        pass

    @log_helpers.log_method_call
    def create_tap_flow_postcommit(self, context):
        try:
            tf = context.tap_flow
            self.client.create_tap_flow(context._plugin_context, tf)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create tap flow %(tap_flow)s "
                          "in Midonet: %(err)s",
                          {"tap_flow": tf, "err": ex})

    @log_helpers.log_method_call
    def delete_tap_flow_precommit(self, context):
        # TODO(yamamoto): Call self.client for task-based api
        pass

    @log_helpers.log_method_call
    def delete_tap_flow_postcommit(self, context):
        try:
            tf = context.tap_flow
            self.client.delete_tap_flow(context._plugin_context, tf['id'])
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to delete a tap flow"
                          "%(tap_flow)s in Midonet: %(err)s",
                          {"tap_flow": tf['id'], "err": ex})
