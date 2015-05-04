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

from midonet.neutron.common import config  # noqa
from midonet.neutron.common import util
from midonet.neutron.db import loadbalancer_db as mn_lb_db
from midonet.neutron import extensions
from midonetclient import client
from neutron.api import extensions as neutron_extensions
from neutron.api.rpc.handlers import dhcp_rpc
from neutron.common import constants as n_const
from neutron.common import exceptions as n_exc
from neutron.common import rpc as n_rpc
from neutron.common import topics
from neutron.common import utils
from neutron.db import agents_db
from neutron.db import agentschedulers_db
from neutron.db import db_base_plugin_v2
from neutron.db import external_net_db
from neutron.db import extradhcpopt_db
from neutron.db import extraroute_db
from neutron.db import l3_gwmode_db
from neutron.db import portbindings_db
from neutron.db import securitygroups_db
from neutron.extensions import extra_dhcp_opt as edo_ext
from neutron.extensions import portbindings
from neutron.extensions import securitygroup as ext_sg
from neutron import i18n
from neutron.plugins.common import constants
from neutron_lbaas.db.loadbalancer import loadbalancer_db
from oslo_config import cfg
from oslo_db import exception as db_exc
from oslo_log import log as logging
from oslo_utils import excutils
from oslo_utils import importutils


LOG = logging.getLogger(__name__)
_LE = i18n._LE
_LI = i18n._LI


class MidonetApiMixin(agentschedulers_db.DhcpAgentSchedulerDbMixin,
                      db_base_plugin_v2.NeutronDbPluginV2,
                      external_net_db.External_net_db_mixin,
                      extradhcpopt_db.ExtraDhcpOptMixin,
                      extraroute_db.ExtraRoute_db_mixin,
                      l3_gwmode_db.L3_NAT_db_mixin,
                      loadbalancer_db.LoadBalancerPluginDb,
                      mn_lb_db.LoadBalancerMixin,
                      portbindings_db.PortBindingMixin,
                      securitygroups_db.SecurityGroupDbMixin):

    supported_extension_aliases = ['extra_dhcp_opt', 'lbaas']

    def __init__(self):
        super(MidonetApiMixin, self).__init__()

        # Instantiate MidoNet API client
        conf = cfg.CONF.MIDONET
        neutron_extensions.append_api_extensions_path(extensions.__path__)
        self.api_cli = client.MidonetClient(conf.midonet_uri, conf.username,
                                            conf.password,
                                            project_id=conf.project_id)

        self.setup_rpc()

        self.base_binding_dict = {
            portbindings.VIF_TYPE: portbindings.VIF_TYPE_MIDONET,
            portbindings.VNIC_TYPE: portbindings.VNIC_NORMAL,
            portbindings.VIF_DETAILS: {
                # TODO(rkukura): Replace with new VIF security details
                portbindings.CAP_PORT_FILTER:
                'security-group' in self.supported_extension_aliases}}
        self.network_scheduler = importutils.import_object(
            cfg.CONF.network_scheduler_driver
        )

    def setup_rpc(self):
        # RPC support
        self.topic = topics.PLUGIN
        self.conn = n_rpc.create_connection(new=True)
        self.endpoints = [dhcp_rpc.DhcpRpcCallback(),
                          agents_db.AgentExtRpcCallback()]
        self.conn.create_consumer(self.topic, self.endpoints,
                                  fanout=False)
        # Consume from all consumers in a thread
        self.conn.consume_in_threads()

    def _process_create_network(self, context, network):

        net_data = network['network']
        tenant_id = self._get_tenant_id_for_create(context, net_data)
        net_data['tenant_id'] = tenant_id
        self._ensure_default_security_group(context, tenant_id)

        with context.session.begin(subtransactions=True):
            net = super(MidonetApiMixin, self).create_network(context, network)
            self._process_l3_create(context, net, net_data)

        return net

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def create_network(self, context, network):
        """Create Neutron network.

        Create a new Neutron network and its corresponding MidoNet bridge.
        """
        LOG.debug('MidonetApiMixin.create_network called: network=%r',
                  network)

        net = self._process_create_network(context, network)

        try:
            self.api_cli.create_network(net)
        except Exception as ex:
            LOG.error(_LE("Failed to create a network %(net_id)s in Midonet:"
                          "%(err)s"), {"net_id": net["id"], "err": ex})
            with excutils.save_and_reraise_exception():
                super(MidonetApiMixin, self).delete_network(context, net['id'])

        LOG.debug("MidonetApiMixin.create_network exiting: net=%r", net)
        return net

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def update_network(self, context, id, network):
        """Update Neutron network.

        Update an existing Neutron network and its corresponding MidoNet
        bridge.
        """
        LOG.debug("MidonetApiMixin.update_network called: id=%(id)r, "
                  "network=%(network)r", {'id': id, 'network': network})

        with context.session.begin(subtransactions=True):
            net = super(MidonetApiMixin, self).update_network(
                context, id, network)

            self._process_l3_update(context, net, network['network'])
            self.api_cli.update_network(id, net)

        LOG.debug("MidonetApiMixin.update_network exiting: net=%r", net)
        return net

    @util.handle_api_error
    @utils.synchronized('midonet-network-lock', external=True)
    @util.retry_on_error(2, 1, db_exc.DBError)
    def delete_network(self, context, id):
        """Delete a network and its corresponding MidoNet bridge.

        This method is wrapped by 'retry_on_error' decorator because concurrent
        requests to the API server often causes DB deadlock error because
        eventlet green threads do not yield properly when they block inside
        the transaction.  This hack should no longer become available once
        we moved to the model where API requests are asynchronous or when
        eventlet-compatible mysqlconnector is used for the DB driver instead.
        """
        LOG.debug("MidonetApiMixin.delete_network called: id=%r", id)

        with context.session.begin(subtransactions=True):
            self._process_l3_delete(context, id)
            super(MidonetApiMixin, self).delete_network(context, id)

            self.api_cli.delete_network(id)

        LOG.debug("MidonetApiMixin.delete_network exiting: id=%r", id)

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def create_subnet(self, context, subnet):
        """Create Neutron subnet.

        Creates a Neutron subnet and a DHCP entry in MidoNet bridge.
        """
        LOG.debug("MidonetApiMixin.create_subnet called: subnet=%r", subnet)

        sn_entry = super(MidonetApiMixin, self).create_subnet(context, subnet)

        try:
            self.api_cli.create_subnet(sn_entry)
        except Exception as ex:
            LOG.error(_LE("Failed to create a subnet %(s_id)s in Midonet:"
                          "%(err)s"), {"s_id": sn_entry["id"], "err": ex})
            with excutils.save_and_reraise_exception():
                super(MidonetApiMixin, self).delete_subnet(
                    context, sn_entry['id'])

        LOG.debug("MidonetApiMixin.create_subnet exiting: sn_entry=%r",
                  sn_entry)
        return sn_entry

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def delete_subnet(self, context, id):
        """Delete Neutron subnet.

        Delete neutron network and its corresponding MidoNet bridge.
        """
        LOG.debug("MidonetApiMixin.delete_subnet called: id=%s", id)

        with context.session.begin(subtransactions=True):
            super(MidonetApiMixin, self).delete_subnet(context, id)
            self.api_cli.delete_subnet(id)

        LOG.debug("MidonetApiMixin.delete_subnet exiting")

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def update_subnet(self, context, id, subnet):
        """Update the subnet with new info.
        """
        LOG.debug("MidonetApiMixin.update_subnet called: id=%s", id)

        with context.session.begin(subtransactions=True):
            s = super(MidonetApiMixin, self).update_subnet(context, id, subnet)
            self.api_cli.update_subnet(id, s)

        return s

    def _process_create_port(self, context, port):
        """Create a L2 port in Neutron/MidoNet."""
        port_data = port['port']
        with context.session.begin(subtransactions=True):
            # Create a Neutron port
            new_port = super(MidonetApiMixin, self).create_port(context, port)
            dhcp_opts = port['port'].get(edo_ext.EXTRADHCPOPTS, [])

            # Make sure that the port created is valid
            if "id" not in new_port:
                raise n_exc.BadRequest(resource='port',
                                       msg="Invalid port created")

            # Update fields
            port_data.update(new_port)

            # Bind security groups to the port
            self._ensure_default_security_group_on_port(context, port)
            sg_ids = self._get_security_groups_on_port(context, port)
            self._process_port_create_security_group(context, new_port, sg_ids)

            self._process_portbindings_create_and_update(context, port_data,
                                                         new_port)

            self._process_port_create_extra_dhcp_opts(context, new_port,
                                                      dhcp_opts)
        return new_port

    @util.handle_api_error
    @utils.synchronized('midonet-port-lock', external=True)
    @util.retry_on_error(2, 1, db_exc.DBError)
    def create_port(self, context, port):
        """Create a L2 port in Neutron/MidoNet."""
        LOG.debug("MidonetApiMixin.create_port called: port=%r", port)

        new_port = self._process_create_port(context, port)

        try:
            self.api_cli.create_port(new_port)
        except Exception as ex:
            LOG.error(_LE("Failed to create a port %(new_port)s: %(err)s"),
                      {"new_port": new_port, "err": ex})
            with excutils.save_and_reraise_exception():
                super(MidonetApiMixin, self).delete_port(context,
                                                         new_port['id'])

        LOG.debug("MidonetApiMixin.create_port exiting: port=%r", new_port)
        return new_port

    @util.handle_api_error
    @utils.synchronized('midonet-port-lock', external=True)
    @util.retry_on_error(2, 1, db_exc.DBError)
    def _process_port_delete(self, context, id):
        """Delete the Neutron and MidoNet ports

        This method is wrapped by 'retry_on_error' decorator.  See the
        explanation in the 'delete_network' comment.
        """
        with context.session.begin(subtransactions=True):
            super(MidonetApiMixin, self).disassociate_floatingips(
                context, id, do_notify=False)
            super(MidonetApiMixin, self).delete_port(context, id)
            self.api_cli.delete_port(id)

    @util.retry_on_error(2, 1, db_exc.DBError)
    def delete_port(self, context, id, l3_port_check=True):
        """Delete a neutron port and corresponding MidoNet bridge port."""
        LOG.debug("MidonetApiMixin.delete_port called: id=%(id)s "
                  "l3_port_check=%(l3_port_check)r",
                 {'id': id, 'l3_port_check': l3_port_check})

        # if needed, check to see if this is a port owned by
        # and l3-router.  If so, we should prevent deletion.
        if l3_port_check:
            self.prevent_l3_port_deletion(context, id)

        self._process_port_delete(context, id)
        LOG.debug("MidonetApiMixin.delete_port exiting: id=%r", id)

    def _process_port_update(self, context, id, in_port, out_port):

        has_sg = self._check_update_has_security_groups(in_port)
        delete_sg = self._check_update_deletes_security_groups(in_port)

        if delete_sg or has_sg:
            # delete the port binding and read it with the new rules.
            self._delete_port_security_group_bindings(context, id)
            sg_ids = self._get_security_groups_on_port(context, in_port)
            self._process_port_create_security_group(context, out_port, sg_ids)

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def update_port(self, context, id, port):
        """Handle port update, including security groups and fixed IPs."""
        LOG.debug("MidonetApiMixin.update_port called: id=%(id)s "
                  "port=%(port)r"), {'id': id, 'port': port}
        with context.session.begin(subtransactions=True):

            # update the port DB
            p = super(MidonetApiMixin, self).update_port(context, id, port)

            self._process_port_update(context, id, port, p)
            self._update_extra_dhcp_opts_on_port(context, id, port, p)
            self._process_portbindings_create_and_update(context,
                                                         port['port'], p)
            self.api_cli.update_port(id, p)

        LOG.debug("MidonetApiMixin.update_port exiting: p=%r", p)
        return p

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def create_router(self, context, router):
        """Handle router creation.

        When a new Neutron router is created, its corresponding MidoNet router
        is also created.  In MidoNet, this router is initialized with chains
        for inbound and outbound traffic, which will be used to hold other
        chains that include various rules, such as NAT.

        :param router: Router information provided to create a new router.
        """
        LOG.debug("MidonetApiMixin.create_router called: router=%(router)s",
                  {"router": router})
        r = super(MidonetApiMixin, self).create_router(context, router)

        try:
            self.api_cli.create_router(r)
        except Exception as ex:
            LOG.error(_LE("Failed to create a router %(r_id)s in Midonet:"
                          "%(err)s"), {"r_id": r["id"], "err": ex})
            with excutils.save_and_reraise_exception():
                super(MidonetApiMixin, self).delete_router(context, r['id'])

        LOG.debug("MidonetApiMixin.create_router exiting: router=%(router)s.",
                  {"router": r})
        return r

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def update_router(self, context, id, router):
        """Handle router updates."""
        LOG.debug("MidonetApiMixin.update_router called: id=%(id)s "
                  "router=%(router)r", {"id": id, "router": router})

        with context.session.begin(subtransactions=True):
            r = super(MidonetApiMixin, self).update_router(context, id, router)
            self.api_cli.update_router(id, r)

        LOG.debug("MidonetApiMixin.update_router exiting: router=%r", r)
        return r

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def delete_router(self, context, id):
        """Handler for router deletion.

        Deleting a router on Neutron simply means deleting its corresponding
        router in MidoNet.

        :param id: router ID to remove
        """
        LOG.debug("MidonetApiMixin.delete_router called: id=%s", id)

        with context.session.begin(subtransactions=True):
            super(MidonetApiMixin, self).delete_router(context, id)
            self.api_cli.delete_router(id)

        LOG.debug("MidonetApiMixin.delete_router exiting: id=%s", id)

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def add_router_interface(self, context, router_id, interface_info):
        """Handle router linking with network."""
        LOG.debug("MidonetApiMixin.add_router_interface called: "
                  "router_id=%(router_id)s, interface_info=%(interface_info)r",
                  {'router_id': router_id, 'interface_info': interface_info})

        info = super(MidonetApiMixin, self).add_router_interface(
            context, router_id, interface_info)

        try:
            self.api_cli.add_router_interface(router_id, info)
        except Exception:
            LOG.error(_LE("Failed to create MidoNet resources to add router "
                          "interface. info=%(info)s, router_id=%(router_id)s"),
                      {"info": info, "router_id": router_id})
            with excutils.save_and_reraise_exception():
                self.remove_router_interface(context, router_id, info)

        LOG.debug("MidonetApiMixin.add_router_interface exiting: info=%r",
                  info)
        return info

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def remove_router_interface(self, context, router_id, interface_info):
        """Handle router un-linking with network."""
        LOG.debug("MidonetApiMixin.remove_router_interface called: "
                  "router_id=%(router_id)s, interface_info=%(interface_info)r",
                  {'router_id': router_id, 'interface_info': interface_info})

        with context.session.begin(subtransactions=True):
            info = super(MidonetApiMixin, self).remove_router_interface(
                context, router_id, interface_info)
            self.api_cli.remove_router_interface(router_id, interface_info)

        LOG.debug("MidonetApiMixin.remove_router_interface exiting: info=%r",
                  info)
        return info

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def create_floatingip(self, context, floatingip):
        """Handle floating IP creation."""
        LOG.debug("MidonetApiMixin.create_floatingip called: ip=%r",
                 floatingip)

        fip = super(MidonetApiMixin, self).create_floatingip(context,
                                                             floatingip)

        try:
            self.api_cli.create_floating_ip(fip)
        except Exception as ex:
            LOG.error(_LE("Failed to create floating ip %(fip)s: %(err)s"),
                      {"fip": fip, "err": ex})
            with excutils.save_and_reraise_exception():
                # Try removing the fip
                self.delete_floatingip(context, fip['id'])

        LOG.debug("MidonetApiMixin.create_floatingip exiting: fip=%r", fip)
        return fip

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def delete_floatingip(self, context, id):
        """Handle floating IP deletion."""
        LOG.debug("MidonetApiMixin.delete_floatingip called: id=%s", id)

        with context.session.begin(subtransactions=True):
            super(MidonetApiMixin, self).delete_floatingip(context, id)
            self.api_cli.delete_floating_ip(id)

        LOG.debug("MidonetApiMixin.delete_floatingip exiting: id=%r", id)

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def update_floatingip(self, context, id, floatingip):
        """Handle floating IP association and disassociation."""
        LOG.debug("MidonetApiMixin.update_floatingip called: id=%(id)s "
                  "floatingip=%(floatingip)s ",
                  {'id': id, 'floatingip': floatingip})

        with context.session.begin(subtransactions=True):
            fip = super(MidonetApiMixin, self).update_floatingip(context, id,
                                                                 floatingip)

            # Update status based on association
            if fip.get('port_id') is None:
                fip['status'] = n_const.FLOATINGIP_STATUS_DOWN
            else:
                fip['status'] = n_const.FLOATINGIP_STATUS_ACTIVE
            self.update_floatingip_status(context, id, fip['status'])

            self.api_cli.update_floating_ip(id, fip)

        LOG.debug("MidonetApiMixin.update_floating_ip exiting: fip=%s", fip)
        return fip

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def create_security_group(self, context, security_group, default_sg=False):
        """Create security group.

        Create a new security group, including the default security group.
        In MidoNet, this means creating a pair of chains, inbound and outbound,
        as well as a new port group.
        """
        LOG.debug("MidonetApiMixin.create_security_group called: "
                  "security_group=%(security_group)s "
                  "default_sg=%(default_sg)s ",
                  {'security_group': security_group, 'default_sg': default_sg})

        sg = security_group.get('security_group')
        tenant_id = self._get_tenant_id_for_create(context, sg)
        if not default_sg:
            self._ensure_default_security_group(context, tenant_id)

        # Create the Neutron sg first
        sg = super(MidonetApiMixin, self).create_security_group(
            context, security_group, default_sg)

        try:
            # Process the MidoNet side
            self.api_cli.create_security_group(sg)
        except Exception:
            LOG.error(_LE("Failed to create MidoNet resources for sg %(sg)r"),
                      {"sg": sg})
            with excutils.save_and_reraise_exception():
                super(MidonetApiMixin, self).delete_security_group(context,
                                                                   sg['id'])

        LOG.debug("MidonetApiMixin.create_security_group exiting: sg=%r", sg)
        return sg

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def delete_security_group(self, context, id):
        """Delete chains for Neutron security group."""
        LOG.debug("MidonetApiMixin.delete_security_group called: id=%s", id)

        sg = super(MidonetApiMixin, self).get_security_group(context, id)
        if not sg:
            raise ext_sg.SecurityGroupNotFound(id=id)

        if sg["name"] == 'default' and not context.is_admin:
            raise ext_sg.SecurityGroupCannotRemoveDefault()

        with context.session.begin(subtransactions=True):
            super(MidonetApiMixin, self).delete_security_group(context, id)

            self.api_cli.delete_security_group(id)

        LOG.debug("MidonetApiMixin.delete_security_group exiting: id=%r", id)

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def create_security_group_rule(self, context, security_group_rule):
        """Create a security group rule

        Create a security group rule in the Neutron DB and corresponding
        MidoNet resources in its data store.
        """
        LOG.debug("MidonetApiMixin.create_security_group_rule called: "
                  "security_group_rule=%(security_group_rule)r",
                  {'security_group_rule': security_group_rule})

        rule = super(MidonetApiMixin, self).create_security_group_rule(
            context, security_group_rule)

        try:
            self.api_cli.create_security_group_rule(rule)
        except Exception as ex:
            LOG.error(_LE('Failed to create security group rule %(sg)s,'
                      'error: %(err)s'), {'sg': rule, 'err': ex})
            with excutils.save_and_reraise_exception():
                super(MidonetApiMixin, self).delete_security_group_rule(
                    context, rule['id'])

        LOG.debug("MidonetApiMixin.create_security_group_rule exiting: "
                  "rule=%r", rule)
        return rule

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def create_security_group_rule_bulk(self, context, security_group_rules):
        """Create multiple security group rules

        Create multiple security group rules in the Neutron DB and
        corresponding MidoNet resources in its data store.
        """
        LOG.debug("MidonetApiMixin.create_security_group_rule_bulk called: "
                  "security_group_rules=%(security_group_rules)r",
                 {'security_group_rules': security_group_rules})

        rules = super(
            MidonetApiMixin,
            self).create_security_group_rule_bulk_native(context,
                                                         security_group_rules)
        try:
            self.api_cli.create_security_group_rule_bulk(rules)
        except Exception as ex:
            LOG.error(_LE("Failed to create bulk security group rules %(sg)s, "
                          "error: %(err)s"), {"sg": rules, "err": ex})
            with excutils.save_and_reraise_exception():
                for rule in rules:
                    super(MidonetApiMixin, self).delete_security_group_rule(
                        context, rule['id'])

        LOG.debug("MidonetApiMixin.create_security_group_rule_bulk exiting:"
                  " rules=%r", rules)
        return rules

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def delete_security_group_rule(self, context, sg_rule_id):
        """Delete a security group rule

        Delete a security group rule from the Neutron DB and corresponding
        MidoNet resources from its data store.
        """
        LOG.debug("MidonetApiMixin.delete_security_group_rule called: "
                  "sg_rule_id=%s", sg_rule_id)

        with context.session.begin(subtransactions=True):
            super(MidonetApiMixin, self).delete_security_group_rule(
                context, sg_rule_id)
            self.api_cli.delete_security_group_rule(sg_rule_id)

        LOG.debug("MidonetApiMixin.delete_security_group_rule exiting: id=%r",
                  id)

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def create_vip(self, context, vip):
        LOG.debug("MidonetApiMixin.create_vip called: %(vip)r",
                  {'vip': vip})

        with context.session.begin(subtransactions=True):

            self._validate_vip_subnet(context, vip)

            v = super(MidonetApiMixin, self).create_vip(context, vip)
            self.api_cli.create_vip(v)
            v['status'] = constants.ACTIVE
            self.update_status(context, loadbalancer_db.Vip, v['id'],
                               v['status'])

        LOG.debug("MidonetApiMixin.create_vip exiting: id=%r", v['id'])
        return v

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def delete_vip(self, context, id):
        LOG.debug("MidonetApiMixin.delete_vip called: id=%(id)r",
                  {'id': id})

        with context.session.begin(subtransactions=True):
            super(MidonetApiMixin, self).delete_vip(context, id)
            self.api_cli.delete_vip(id)

        LOG.debug("MidonetApiMixin.delete_vip existing: id=%(id)r",
                  {'id': id})

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def update_vip(self, context, id, vip):
        LOG.debug("MidonetApiMixin.update_vip called: id=%(id)r, "
                  "vip=%(vip)r", {'id': id, 'vip': vip})

        with context.session.begin(subtransactions=True):
            v = super(MidonetApiMixin, self).update_vip(context, id, vip)
            self.api_cli.update_vip(id, v)

        LOG.debug("MidonetApiMixin.update_vip exiting: id=%(id)r, "
                  "vip=%(vip)r", {'id': id, 'vip': v})
        return v

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def create_pool(self, context, pool):
        LOG.debug("MidonetApiMixin.create_pool called: %(pool)r",
                  {'pool': pool})

        router_id = self._check_and_get_router_id_for_pool(
            context, pool['pool']['subnet_id'])
        pool['pool'].update({'router_id': router_id})

        with context.session.begin(subtransactions=True):
            p = super(MidonetApiMixin, self).create_pool(context, pool)

            self.api_cli.create_pool(p)

            p['status'] = constants.ACTIVE
            self.update_status(context, loadbalancer_db.Pool, p['id'],
                               p['status'])

        LOG.debug("MidonetApiMixin.create_pool exiting: %(pool)r",
                  {'pool': p})
        return p

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def update_pool(self, context, id, pool):
        LOG.debug("MidonetApiMixin.update_pool called: id=%(id)r, "
                  "pool=%(pool)r", {'id': id, 'pool': pool})

        with context.session.begin(subtransactions=True):
            p = super(MidonetApiMixin, self).update_pool(context, id, pool)
            self.api_cli.update_pool(id, p)

        LOG.debug("MidonetApiMixin.update_pool exiting: id=%(id)r, "
                  "pool=%(pool)r", {'id': id, 'pool': pool})
        return p

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def delete_pool(self, context, id):
        LOG.debug("MidonetApiMixin.delete_pool called: %(id)r", {'id': id})

        with context.session.begin(subtransactions=True):
            super(MidonetApiMixin, self).delete_pool(context, id)
            self.api_cli.delete_pool(id)

        LOG.debug("MidonetApiMixin.delete_pool exiting: %(id)r", {'id': id})

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def create_member(self, context, member):
        LOG.debug("MidonetApiMixin.create_member called: %(member)r",
                  {'member': member})

        with context.session.begin(subtransactions=True):
            m = super(MidonetApiMixin, self).create_member(context, member)
            self.api_cli.create_member(m)
            m['status'] = constants.ACTIVE
            self.update_status(context, loadbalancer_db.Member, m['id'],
                               m['status'])

        LOG.debug("MidonetApiMixin.create_member exiting: %(member)r",
                  {'member': m})
        return m

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def update_member(self, context, id, member):
        LOG.debug("MidonetApiMixin.update_member called: id=%(id)r, "
                  "member=%(member)r", {'id': id, 'member': member})

        with context.session.begin(subtransactions=True):
            m = super(MidonetApiMixin, self).update_member(context, id, member)
            self.api_cli.update_member(id, m)

        LOG.debug("MidonetApiMixin.update_member exiting: id=%(id)r, "
                  "member=%(member)r", {'id': id, 'member': m})
        return m

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def delete_member(self, context, id):
        LOG.debug("MidonetApiMixin.delete_member called: %(id)r",
                  {'id': id})

        with context.session.begin(subtransactions=True):
            super(MidonetApiMixin, self).delete_member(context, id)
            self.api_cli.delete_member(id)

        LOG.debug("MidonetApiMixin.delete_member exiting: %(id)r",
                  {'id': id})

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def create_health_monitor(self, context, health_monitor):
        LOG.debug("MidonetApiMixin.create_health_monitor called: "
                  " %(health_monitor)r", {'health_monitor': health_monitor})

        with context.session.begin(subtransactions=True):
            hm = super(MidonetApiMixin, self).create_health_monitor(
                context, health_monitor)
            self.api_cli.create_health_monitor(hm)

        LOG.debug("MidonetApiMixin.create_health_monitor exiting: "
                  "%(health_monitor)r", {'health_monitor': hm})
        return hm

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def update_health_monitor(self, context, id, health_monitor):
        LOG.debug("MidonetApiMixin.update_health_monitor called: id=%(id)r, "
                  "health_monitor=%(health_monitor)r",
                  {'id': id, 'health_monitor': health_monitor})

        with context.session.begin(subtransactions=True):
            hm = super(MidonetApiMixin, self).update_health_monitor(
                context, id, health_monitor)
            self.api_cli.update_health_monitor(id, hm)

        LOG.debug("MidonetApiMixin.update_health_monitor exiting: id=%(id)r, "
                  "health_monitor=%(health_monitor)r",
                  {'id': id, 'health_monitor': hm})
        return hm

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def delete_health_monitor(self, context, id):
        LOG.debug("MidonetApiMixin.delete_health_monitor called: %(id)r",
                  {'id': id})

        with context.session.begin(subtransactions=True):
            super(MidonetApiMixin, self).delete_health_monitor(context, id)
            self.api_cli.delete_health_monitor(id)

        LOG.debug("MidonetApiMixin.delete_health_monitor exiting: %(id)r",
                  {'id': id})

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def create_pool_health_monitor(self, context, health_monitor, pool_id):
        LOG.debug("MidonetApiMixin.create_pool_health_monitor called: "
                  "hm=%(health_monitor)r, pool_id=%(pool_id)r",
                  {'health_monitor': health_monitor, 'pool_id': pool_id})

        pool = self.get_pool(context, pool_id)
        monitors = pool.get('health_monitors')
        if len(monitors) > 0:
            msg = (_LE("MidoNet right now can only support one monitor per "
                       "pool"))
            raise n_exc.BadRequest(resource='pool_health_monitor', msg=msg)

        hm = health_monitor['health_monitor']
        with context.session.begin(subtransactions=True):
            monitors = super(MidonetApiMixin, self).create_pool_health_monitor(
                context, health_monitor, pool_id)
            self.api_cli.create_pool_health_monitor(hm, pool_id)

        LOG.debug("MidonetApiMixin.create_pool_health_monitor exiting: "
                  "%(health_monitor)r, %(pool_id)r",
                  {'health_monitor': health_monitor, 'pool_id': pool_id})
        return monitors

    @util.handle_api_error
    @util.retry_on_error(2, 1, db_exc.DBError)
    def delete_pool_health_monitor(self, context, id, pool_id):
        LOG.debug("MidonetApiMixin.delete_pool_health_monitor called: "
                  "id=%(id)r, pool_id=%(pool_id)r",
                  {'id': id, 'pool_id': pool_id})

        with context.session.begin(subtransactions=True):
            super(MidonetApiMixin, self).delete_pool_health_monitor(
                context, id, pool_id)
            self.api_cli.delete_pool_health_monitor(id, pool_id)

        LOG.debug("MidonetApiMixin.delete_pool_health_monitor exiting: "
                  "%(id)r, %(pool_id)r", {'id': id, 'pool_id': pool_id})
