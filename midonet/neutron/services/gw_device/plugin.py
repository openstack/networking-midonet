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

from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_utils import excutils

from neutron.api import extensions as neutron_extensions

from midonet.neutron.client import base as c_base
from midonet.neutron.common import config  # noqa
from midonet.neutron.common import constants as midonet_const
from midonet.neutron.db import gateway_device as gateway_device_db
from midonet.neutron import extensions
from midonet.neutron.extensions import gateway_device

LOG = logging.getLogger(__name__)


class MidonetGwDeviceServicePlugin(gateway_device_db.GwDeviceDbMixin):

    """Implements GatewayDevice service plugin for Midonet."""

    supported_extension_aliases = ["gateway-device"]

    def __init__(self):
        super(MidonetGwDeviceServicePlugin, self).__init__()

        # Instantiate MidoNet API client
        self.client = c_base.load_client(cfg.CONF.MIDONET)

        neutron_extensions.append_api_extensions_path(extensions.__path__)

    @classmethod
    def get_plugin_type(cls):
        return midonet_const.GATEWAY_DEVICE

    def get_plugin_description(self):
        """Returns string description of the plugin."""
        return "Midonet Gateway Device Service Plugin"

    @log_helpers.log_method_call
    def create_gateway_device(self, context, gateway_device):

        with context.session.begin(subtransactions=True):
            gw = super(MidonetGwDeviceServicePlugin,
                       self).create_gateway_device(context, gateway_device)
            self.client.create_gateway_device_precommit(context, gw)

        try:
            self.client.create_gateway_device_postcommit(gw)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create a gateway "
                          "device %(gw_id)s in Midonet: %(err)s",
                          {"gw_id": gw["id"], "err": ex})
                try:
                    self.delete_gateway_device(context, gw['id'])
                except Exception:
                    LOG.exception("Failed to delete a gateway device %s",
                                  gw["id"])
        return gw

    @log_helpers.log_method_call
    def update_gateway_device(self, context, id, gateway_device):
        backup = self.get_gateway_device(context, id)
        del backup['id']
        del backup['remote_mac_entries']
        backup_body = {'gateway_device': backup}
        with context.session.begin(subtransactions=True):
            gw = super(MidonetGwDeviceServicePlugin,
                       self).update_gateway_device(context, id, gateway_device)
            self.client.update_gateway_device_precommit(context, id, gw)

        try:
            self.client.update_gateway_device_postcommit(id, gw)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to update a gateway "
                          "device %(gw_id)s in Midonet:%(err)s",
                          {"gw_id": gw["id"], "err": ex})
                try:
                    super(
                        MidonetGwDeviceServicePlugin,
                        self).update_gateway_device(
                            context, gw['id'], backup_body)
                except Exception:
                    LOG.exception("Failed to update a gateway "
                                  "device for rollback %s", gw["id"])
        return gw

    @log_helpers.log_method_call
    def delete_gateway_device(self, context, id):
        with context.session.begin(subtransactions=True):
            super(MidonetGwDeviceServicePlugin,
                  self).delete_gateway_device(context, id)
            self.client.delete_gateway_device_precommit(context, id)

        self.client.delete_gateway_device_postcommit(id)

    @log_helpers.log_method_call
    def create_gateway_device_remote_mac_entry(self, context,
                                               remote_mac_entry,
                                               gateway_device_id):
        gw_device = self._get_gateway_device(context, gateway_device_id)

        if gw_device.type == gateway_device.NETWORK_VLAN_TYPE:
            raise gateway_device.OperationRemoteMacEntryNotSupported(
                type=gateway_device.NETWORK_VLAN_TYPE)

        with context.session.begin(subtransactions=True):
            rme = super(MidonetGwDeviceServicePlugin,
                        self).create_gateway_device_remote_mac_entry(
                context, gateway_device_id, remote_mac_entry)
            self.client.create_gateway_device_remote_mac_entry_precommit(
                context, rme)

        try:
            self.client.create_gateway_device_remote_mac_entry_postcommit(rme)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create a remote mac entry "
                          "%(rme_id)s for %(gw_id)s in Midonet:%(err)s",
                          {"rme_id": rme["id"], "gw_id": gateway_device_id,
                           "err": ex})
                try:
                    super(MidonetGwDeviceServicePlugin,
                          self).delete_gateway_device_remote_mac_entry(
                        context, rme["id"], gateway_device_id)
                except Exception:
                    LOG.exception("Failed to delete a remote mac entry %s",
                                  rme["id"])

        return rme

    @log_helpers.log_method_call
    def delete_gateway_device_remote_mac_entry(self, context, id,
                                               gateway_device_id):
        self._get_gateway_device(context, gateway_device_id)
        with context.session.begin(subtransactions=True):
            super(MidonetGwDeviceServicePlugin,
                  self).delete_gateway_device_remote_mac_entry(
                context, id, gateway_device_id)
            self.client.delete_gateway_device_remote_mac_entry_precommit(
                context, id)

        self.client.delete_gateway_device_remote_mac_entry_postcommit(id)
