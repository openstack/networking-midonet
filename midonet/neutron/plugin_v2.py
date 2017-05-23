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

import sqlalchemy

from neutron_lib.api.definitions import extra_dhcp_opt as edo_ext
from neutron_lib.api.definitions import network as net_def
from neutron_lib.api.definitions import port as port_def
from neutron_lib.api.definitions import port_security as psec
from neutron_lib.api.definitions import subnet as subnet_def
from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib.callbacks import resources
from neutron_lib import constants as n_const
from neutron_lib import exceptions as n_exc
from neutron_lib.exceptions import port_security as psec_exc
from neutron_lib.plugins import directory

from midonet.neutron._i18n import _, _LE, _LW
from midonet.neutron.common import utils as c_utils
from midonet.neutron.db import port_binding_db as pb_db
from midonet.neutron.db import provider_network_db as pnet_db
from midonet.neutron.midonet_v2 import managers
from midonet.neutron.ml2 import sg_callback
from midonet.neutron import plugin
from midonet.neutron.services.qos import driver as qos_driver

from neutron.db import _resource_extend as resource_extend
from neutron.db import allowedaddresspairs_db as addr_pair_db
from neutron.db import api as db_api
from neutron.db import portsecurity_db as ps_db
from neutron.extensions import allowedaddresspairs as addr_pair
from neutron.extensions import providernet as pnet
from neutron.extensions import securitygroup as ext_sg
from oslo_db import exception as oslo_db_exc
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_utils import excutils


LOG = logging.getLogger(__name__)


@resource_extend.has_resource_extenders
class MidonetPluginV2(plugin.MidonetMixinBase,
                      addr_pair_db.AllowedAddressPairsMixin,
                      pnet_db.MidonetProviderNetworkMixin,
                      pb_db.MidonetPortBindingMixin,
                      ps_db.PortSecurityDbMixin):

    # REVISIT(yamamoto): Consider dropping agent and dhcp_agent_scheduler,
    # probably after a cycle. (for M release)
    # This plugin is for MidoNet v5.0 and later, where we have an
    # alternative metadata proxy which doesn't require Neutron agents.
    # NOTE(yamamoto): While the order in this list doesn't matter
    # functionality-wise, it's alphabetically sorted for easier comparison.
    _base_supported_extension_aliases = [
        'agent',
        'allowed-address-pairs',
        'binding',
        'dhcp_agent_scheduler',
        'external-net',
        'extra_dhcp_opt',
        'port-security',
        'provider',
        'quotas',
        'security-group',
        'subnet_allocation',
    ]

    @property
    def supported_extension_aliases(self):
        if not hasattr(self, '_aliases'):
            aliases = self._base_supported_extension_aliases
            aliases += self.extension_manager.extension_aliases()
            self._aliases = aliases
        return self._aliases

    __native_bulk_support = True
    __native_pagination_support = True
    __native_sorting_support = True

    def __init__(self):
        self.extension_manager = managers.ExtensionManager()
        self.extension_manager.initialize()
        super(MidonetPluginV2, self).__init__()
        self.client.initialize()
        qos_driver.register()
        self.sec_handler = sg_callback.MidonetSecurityGroupsHandler(
            self.client)

    @db_api.retry_if_session_inactive()
    def create_network(self, context, network):
        LOG.debug('MidonetPluginV2.create_network called: network=%r', network)

        net_data = network['network']
        tenant_id = net_data['tenant_id']
        self._ensure_default_security_group(context, tenant_id)

        with db_api.context_manager.writer.using(context):
            net_db = self.create_network_db(context, network)
            net = self._make_network_dict(net_db, process_extensions=False,
                                          context=context)
            self.extension_manager.process_create_network(context, net_data,
                                                          net)
            net_data['id'] = net['id']
            self._process_l3_create(context, net, net_data)
            self._create_provider_network(context, net_data)
            self._extend_provider_network_dict(context, net)
            if psec.PORTSECURITY in net_data:
                self._process_network_port_security_create(context, net_data,
                                                           net)
            registry.notify(resources.NETWORK, events.PRECOMMIT_CREATE, self,
                            context=context, request=net_data, network=net)
            self.client.create_network_precommit(context, net)

        try:
            self.client.create_network_postcommit(net)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to create a network %(net_id)s "
                              "in Midonet: %(err)s"),
                          {"net_id": net["id"], "err": ex})
                try:
                    self.delete_network(context, net['id'])
                except Exception:
                    LOG.exception(_LE("Failed to delete network %s"),
                                  net['id'])

        self._apply_dict_extend_functions('networks', net, net_db)

        LOG.debug("MidonetPluginV2.create_network exiting: net=%r", net)
        return net

    def get_network(self, context, id, fields=None):
        LOG.debug("MidonetPluginV2.get_network called: id=%(id)r", {'id': id})

        with db_api.context_manager.reader.using(context):
            net = super(MidonetPluginV2, self).get_network(context, id, None)
            self._extend_provider_network_dict(context, net)

        return self._fields(net, fields)

    def get_networks(self, context, filters=None, fields=None,
                     sorts=None, limit=None, marker=None, page_reverse=False):
        LOG.debug("MidonetPluginV2.get_networks called: filters=%(filters)r",
                  {'filters': filters})

        with db_api.context_manager.reader.using(context):
            nets = super(MidonetPluginV2,
                         self).get_networks(context, filters, None, sorts,
                                            limit, marker, page_reverse)
            for net in nets:
                self._extend_provider_network_dict(context, net)

            nets = self._filter_nets_provider(nets, filters)

        return [self._fields(net, fields) for net in nets]

    @db_api.retry_if_session_inactive()
    def update_network(self, context, id, network):
        LOG.debug("MidonetPluginV2.update_network called: id=%(id)r, "
                  "network=%(network)r", {'id': id, 'network': network})

        # Disallow update of provider net
        net_data = network['network']
        pnet._raise_if_updates_provider_attributes(net_data)

        with db_api.context_manager.writer.using(context):
            original_network = super(MidonetPluginV2, self).get_network(
                context, id)
            net = super(MidonetPluginV2, self).update_network(
                context, id, network)
            self.extension_manager.process_update_network(context, net_data,
                                                          net)
            self._process_l3_update(context, net, network['network'])
            self._extend_provider_network_dict(context, net)
            if psec.PORTSECURITY in network['network']:
                self._process_network_port_security_update(context,
                                                           network['network'],
                                                           net)
            # NOTE(yamamoto): Retrieve the db object to get the correct
            # revision
            # ToDO(QoS): This would change once EngineFacade moves out
            db_network = self._get_network(context, id)
            # Expire the db_network in current transaction, so that the join
            # relationship can be updated.
            context.session.expire(db_network)
            net = self._make_network_dict(db_network, context=context)
            registry.notify(resources.NETWORK, events.PRECOMMIT_UPDATE, self,
                            context=context, request=net_data, network=net,
                            original_network=original_network)
            self.client.update_network_precommit(context, id, net)

        self.client.update_network_postcommit(id, net)

        LOG.debug("MidonetPluginV2.update_network exiting: net=%r", net)
        return net

    @db_api.retry_if_session_inactive()
    def delete_network(self, context, id):
        LOG.debug("MidonetPluginV2.delete_network called: id=%r", id)

        with db_api.context_manager.writer.using(context):
            self._process_l3_delete(context, id)
            try:
                super(MidonetPluginV2, self).delete_network(context, id)
            except n_exc.NetworkInUse as ex:
                LOG.warning(_LW("Error deleting network %(net)s, retrying..."),
                            {'net': id})
                # Contention for DHCP port deletion and network deletion occur
                # often which leads to NetworkInUse error.  Retry to get
                # around this problem.
                raise oslo_db_exc.RetryRequest(ex)

            self.client.delete_network_precommit(context, id)

        self.client.delete_network_postcommit(id)

        LOG.debug("MidonetPluginV2.delete_network exiting: id=%r", id)

    @db_api.retry_if_session_inactive()
    def create_subnet(self, context, subnet):
        LOG.debug("MidonetPluginV2.create_subnet called: subnet=%r", subnet)

        with db_api.context_manager.writer.using(context):
            s, net_db, ipam_sub = self._create_subnet_precommit(
                context, subnet)
            self.extension_manager.process_create_subnet(context,
                subnet['subnet'], s)
            self.client.create_subnet_precommit(context, s)

        # db base plugin post commit ops
        self._create_subnet_postcommit(context, s, net_db, ipam_sub)
        try:
            self.client.create_subnet_postcommit(s)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to create a subnet %(s_id)s in Midonet:"
                              "%(err)s"), {"s_id": s["id"], "err": ex})
                try:
                    self.delete_subnet(context, s['id'])
                except Exception:
                    LOG.exception(_LE("Failed to delete subnet %s"), s['id'])

        LOG.debug("MidonetPluginV2.create_subnet exiting: subnet=%r", s)
        return s

    @db_api.retry_if_session_inactive()
    def delete_subnet(self, context, id):
        LOG.debug("MidonetPluginV2.delete_subnet called: id=%s", id)

        with db_api.context_manager.writer.using(context):
            super(MidonetPluginV2, self).delete_subnet(context, id)
            self.client.delete_subnet_precommit(context, id)

        self.client.delete_subnet_postcommit(id)

        LOG.debug("MidonetPluginV2.delete_subnet exiting")

    @db_api.retry_if_session_inactive()
    def update_subnet(self, context, id, subnet):
        LOG.debug("MidonetPluginV2.update_subnet called: id=%s", id)

        with db_api.context_manager.writer.using(context):
            s = super(MidonetPluginV2, self).update_subnet(context, id, subnet)
            self.extension_manager.process_update_subnet(context,
                subnet['subnet'], s)
            # NOTE(yamamoto): Retrieve the db object to get the correct
            # revision
            context.session.flush()
            s = self.get_subnet(context, id)
            self.client.update_subnet_precommit(context, id, s)

        self.client.update_subnet_postcommit(id, s)

        LOG.debug("MidonetPluginV2.update_subnet exiting: subnet=%r", s)
        return s

    @db_api.retry_if_session_inactive()
    def create_port(self, context, port):
        LOG.debug("MidonetPluginV2.create_port called: port=%r", port)

        port_data = port['port']
        tenant_id = port_data['tenant_id']
        self._ensure_default_security_group(context, tenant_id)
        with db_api.context_manager.writer.using(context):
            # Set status along admin_state_up if the parameter is specified.
            if port['port'].get('admin_state_up') is not None:
                if not port['port']['admin_state_up']:
                    port['port']['status'] = n_const.PORT_STATUS_DOWN
            # Create a Neutron port
            port_db = self.create_port_db(context, port)
            new_port = self._make_port_dict(port_db, process_extensions=False)
            self.extension_manager.process_create_port(context, port_data,
                                                       new_port)

            # Do not create a gateway port if it has no IP address assigned as
            # MidoNet does not yet handle this case.
            if (new_port.get('device_owner') == n_const.DEVICE_OWNER_ROUTER_GW
                    and not new_port['fixed_ips']):
                msg = (_("No IPs assigned to the gateway port for"
                         " router %s") % port_data['device_id'])
                raise n_exc.BadRequest(resource='router', msg=msg)

            dhcp_opts = port['port'].get(edo_ext.EXTRADHCPOPTS, [])

            # Make sure that the port created is valid
            if "id" not in new_port:
                raise n_exc.BadRequest(resource='port',
                                       msg="Invalid port created")

            # Update fields
            port_data.update(new_port)

            port_psec, has_ip = self._determine_port_security_and_has_ip(
                context, port['port'])
            port['port'][psec.PORTSECURITY] = port_psec
            self._process_port_port_security_create(context,
                                                    port['port'],
                                                    new_port)

            if port_psec is False:
                if self._check_update_has_security_groups(port):
                    raise psec_exc.PortSecurityAndIPRequiredForSecurityGroups()
                if self._check_update_has_allowed_address_pairs(port):
                    raise addr_pair.AddressPairAndPortSecurityRequired()
            else:
                # Bind security groups to the port
                self._ensure_default_security_group_on_port(context, port)

            sg_ids = self._get_security_groups_on_port(context, port)
            self._process_port_create_security_group(context, new_port, sg_ids)

            # Process port bindings
            self._process_portbindings_create_and_update(context, port_data,
                                                         new_port)
            self._process_mido_portbindings_create_and_update(context,
                                                              port_data,
                                                              new_port)

            self._process_port_create_extra_dhcp_opts(context, new_port,
                                                      dhcp_opts)

            new_port[addr_pair.ADDRESS_PAIRS] = (
                self._process_create_allowed_address_pairs(
                    context, new_port,
                    port_data.get(addr_pair.ADDRESS_PAIRS)))

            self.client.create_port_precommit(context, new_port)

        try:
            self.client.create_port_postcommit(new_port)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to create a port %(new_port)s: %(err)s"),
                          {"new_port": new_port, "err": ex})
                try:
                    self.delete_port(context, new_port['id'],
                                     l3_port_check=False)
                except Exception:
                    LOG.exception(_LE("Failed to delete port %s"),
                                  new_port['id'])

        self._apply_dict_extend_functions('ports', new_port, port_db)

        LOG.debug("MidonetPluginV2.create_port exiting: port=%r", new_port)
        return new_port

    @db_api.retry_if_session_inactive()
    def delete_port(self, context, id, l3_port_check=True):
        LOG.debug("MidonetPluginV2.delete_port called: id=%(id)s "
                  "l3_port_check=%(l3_port_check)r",
                  {'id': id, 'l3_port_check': l3_port_check})

        l3plugin = directory.get_plugin(n_const.L3)

        # if needed, check to see if this is a port owned by
        # and l3-router.  If so, we should prevent deletion.
        if l3_port_check and l3plugin:
            l3plugin.prevent_l3_port_deletion(context, id)

        with db_api.context_manager.writer.using(context):
            if l3plugin:
                l3plugin.disassociate_floatingips(context, id,
                                                  do_notify=False)
            super(MidonetPluginV2, self).delete_port(context, id)
            self.client.delete_port_precommit(context, id)

        self.client.delete_port_postcommit(id)

        LOG.debug("MidonetPluginV2.delete_port exiting: id=%r", id)

    @db_api.retry_if_session_inactive()
    def update_port(self, context, id, port):
        LOG.debug("MidonetPluginV2.update_port called: id=%(id)s "
                  "port=%(port)r", {'id': id, 'port': port})

        with db_api.context_manager.writer.using(context):

            # update the port DB
            original_port = super(MidonetPluginV2, self).get_port(context, id)
            p = super(MidonetPluginV2, self).update_port(context, id, port)
            c_utils.check_update_port(original_port, p)
            self.extension_manager.process_update_port(context, port['port'],
                                                       p)

            has_sg = self._check_update_has_security_groups(port)
            delete_sg = self._check_update_deletes_security_groups(port)

            if delete_sg or has_sg:
                # delete the port binding and read it with the new rules.
                self._delete_port_security_group_bindings(context, id)
                sg_ids = self._get_security_groups_on_port(context, port)
                self._process_port_create_security_group(context, p, sg_ids)
            self._update_extra_dhcp_opts_on_port(context, id, port, p)

            self._process_portbindings_create_and_update(context,
                                                         port['port'], p)
            self._process_mido_portbindings_create_and_update(context,
                                                              port['port'], p)
            self.update_address_pairs_on_port(context, id, port,
                                              original_port, p)

            self._process_port_port_security_update(context, port['port'], p)

            port_psec = p.get(psec.PORTSECURITY)
            if port_psec is False:
                if p.get(ext_sg.SECURITYGROUPS):
                    raise psec_exc.PortSecurityPortHasSecurityGroup()
                if p.get(addr_pair.ADDRESS_PAIRS):
                    raise addr_pair.AddressPairAndPortSecurityRequired()
            # NOTE(yamamoto): Retrieve the db object to get the correct
            # revision
            context.session.flush()
            context.session.expire_all()
            p = self.get_port(context, id)
            self.client.update_port_precommit(context, id, p)

        try:
            self.client.update_port_postcommit(id, p)
            if p['status'] != n_const.PORT_STATUS_NOTAPPLICABLE:
                # Set status along admin_state_up to update.
                if p['admin_state_up']:
                    update_status = n_const.PORT_STATUS_ACTIVE
                else:
                    update_status = n_const.PORT_STATUS_DOWN

                data = {'port': {'status': update_status}}
                new_port = super(MidonetPluginV2, self).update_port(
                    context, id, data)
                # prevent binding:profile information from lacking
                p['status'] = new_port['status']
                if 'revision_number' in new_port:
                    p['revision_number'] = new_port['revision_number']
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to update a port %(port_id)s in "
                              "MidoNet: %(err)s"), {"port_id": id, "err": ex})
                try:
                    data = {'port': {'status': n_const.PORT_STATUS_ERROR}}
                    super(MidonetPluginV2, self).update_port(context, id, data)
                except Exception:
                    LOG.exception(_LE("Failed to update port status %s"), id)

        LOG.debug("MidonetPluginV2.update_port exiting: p=%r", p)
        return p

    @log_helpers.log_method_call
    def create_security_group_rule_bulk(self, context, security_group_rules):
        return super(MidonetPluginV2,
                     self).create_security_group_rule_bulk_native(
                     context, security_group_rules)

    @staticmethod
    @resource_extend.extends([net_def.COLLECTION_NAME])
    def _midonet_v2_extend_network_dict(result, netdb):
        plugin = directory.get_plugin()
        session = plugin._object_session_or_new_session(netdb)
        plugin.extension_manager.extend_network_dict(session, netdb, result)

    @staticmethod
    @resource_extend.extends([port_def.COLLECTION_NAME])
    def _midonet_v2_extend_port_dict(result, portdb):
        plugin = directory.get_plugin()
        session = plugin._object_session_or_new_session(portdb)
        plugin.extension_manager.extend_port_dict(session, portdb, result)

    @staticmethod
    @resource_extend.extends([subnet_def.COLLECTION_NAME])
    def _midonet_v2_extend_subnet_dict(result, subnetdb):
        plugin = directory.get_plugin()
        session = plugin._object_session_or_new_session(subnetdb)
        plugin.extension_manager.extend_subnet_dict(session, subnetdb, result)

    @staticmethod
    def _object_session_or_new_session(sql_obj):
        session = sqlalchemy.inspect(sql_obj).session
        if not session:
            session = db_api.get_reader_session()
        return session
