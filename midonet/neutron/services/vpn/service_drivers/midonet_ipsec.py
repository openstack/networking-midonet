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

from neutron_lib import constants as const
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils

from neutron_vpnaas.services.vpn import plugin
from neutron_vpnaas.services.vpn.service_drivers import base_ipsec
from neutron_vpnaas.services.vpn.service_drivers import ipsec_validator

from midonet.neutron.client import base as c_base
from midonet.neutron.common import config  # noqa

LOG = logging.getLogger(__name__)


# TODO(yamamoto): Introduce VPNaaS PRECOMMIT callbacks and
# subscribe them for task-based api.
class MidonetIPsecVPNDriver(base_ipsec.BaseIPsecVPNDriver):
    def __init__(self, service_plugin):
        super(MidonetIPsecVPNDriver, self).__init__(
            service_plugin, ipsec_validator.IpsecVpnValidator(self))
        self.plugin = plugin.VPNPlugin()
        self.client = c_base.load_client(cfg.CONF.MIDONET)

    def create_rpc_conn(self):
        pass

    def create_vpnservice(self, context, vpnservice_dict):
        super(MidonetIPsecVPNDriver, self).create_vpnservice(
            context, vpnservice_dict)
        try:
            self.client.create_vpn_service(context, vpnservice_dict)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create a vpn_service %(service_id)s "
                          "in MidoNet: %(err)s",
                          {"service_id": vpnservice_dict["id"], "err": ex})
                try:
                    self.plugin.delete_vpnservice(
                        context, vpnservice_dict['id'])
                except Exception:
                    LOG.exception("Failed to delete vpn_service %s",
                                  vpnservice_dict['id'])

        self.update_vpn_service_status(context, vpnservice_dict['id'],
                                       const.ACTIVE)

    def update_vpnservice(self, context, old_vpnservice, vpnservice):
        try:
            self.client.update_vpn_service(
                context, vpnservice['id'], vpnservice)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to update a vpn_service %(service_id)s "
                          "in MidoNet: %(err)s",
                          {"service_id": vpnservice["id"], "err": ex})
                try:
                    self.update_vpn_service_status(
                        context, vpnservice['id'], const.ERROR)
                except Exception:
                    LOG.exception("Failed to update vpn_service status %s",
                                  vpnservice['id'])

    def delete_vpnservice(self, context, vpnservice):
        try:
            self.client.delete_vpn_service(context, vpnservice['id'])
        except Exception:
            LOG.exception("Failed to delete vpn_service %s",
                          vpnservice['id'])

    def create_ipsec_site_connection(self, context, ipsec_site_connection):
        ipsec_site_conn_info = self.make_ipsec_site_connection_dict(
            context, ipsec_site_connection['id'])
        try:
            self.client.create_ipsec_site_conn(context, ipsec_site_conn_info)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create a ipsec_site_connection "
                          "%(conn_id)s in MidoNet: %(err)s",
                          {"conn_id": ipsec_site_connection['id'], "err": ex})
                try:
                    self.plugin.delete_ipsec_site_connection(
                        context, ipsec_site_connection['id'])
                except Exception:
                    LOG.exception("Failed to delete ipsec_site_connection %s",
                                  ipsec_site_connection['id'])

        self.service_plugin.update_ipsec_site_conn_status(
            context, ipsec_site_connection['id'], const.ACTIVE)

    def update_ipsec_site_connection(self, context, old_ipsec_site_connection,
                                     ipsec_site_connection):
        ipsec_site_conn_info = self.make_ipsec_site_connection_dict(
            context, ipsec_site_connection['id'])
        try:
            self.client.update_ipsec_site_conn(
                context, ipsec_site_connection['id'], ipsec_site_conn_info)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to update a ipsec_site_connection "
                          "%(service_id)s in MidoNet: %(err)s",
                          {"service_id": ipsec_site_connection['id'],
                           "err": ex})
                try:
                    self.service_plugin.update_ipsec_site_conn_status(
                        context, ipsec_site_connection['id'], const.ERROR)
                except Exception:
                    LOG.exception("Failed to update ipsec_site_connection "
                                  "status %s",
                                  ipsec_site_connection['id'])

    def delete_ipsec_site_connection(self, context, ipsec_site_connection):
        try:
            self.client.delete_ipsec_site_conn(
                context, ipsec_site_connection['id'])
        except Exception:
            LOG.error("Failed to delete ipsec_site_connection %s",
                      ipsec_site_connection['id'])

    def make_ipsec_site_connection_dict(self, context, ipsec_site_conn_id):
        ipsec_site_conn = self.service_plugin._get_ipsec_site_connection(
            context, ipsec_site_conn_id)
        vpnservice = ipsec_site_conn.vpnservice

        local_cidr_map = self.service_plugin._build_local_subnet_cidr_map(
            context)
        vpnservice_dict = self.make_vpnservice_dict(vpnservice, local_cidr_map)
        ipsec_site_conn_dict = list(filter(
            lambda conn: conn['id'] == ipsec_site_conn_id,
            vpnservice_dict['ipsec_site_connections']))[0]
        del ipsec_site_conn_dict['vpnservice']

        return ipsec_site_conn_dict

    def update_vpn_service_status(self, context, vpnservice_id, status):
        # this method is used only for updating a vpn_service status
        self.service_plugin.update_status_by_agent(
            context,
            [{'id': vpnservice_id,
              'status': status,
              'updated_pending_status': True,
              'ipsec_site_connections': {}
              }])
