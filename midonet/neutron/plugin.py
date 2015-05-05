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
from midonet.neutron.db import agent_membership_db as am_db
from midonet.neutron.db import loadbalancer_db as mn_lb_db
from midonet.neutron.db import port_binding_db as pb_db
from midonet.neutron import extensions
from neutron.api import extensions as neutron_extensions
from neutron.api.rpc.handlers import dhcp_rpc
from neutron.common import constants as n_const
from neutron.common import exceptions as n_exc
from neutron.common import rpc as n_rpc
from neutron.common import topics
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
from oslo_log import log as logging
from oslo_utils import excutils
from oslo_utils import importutils


LOG = logging.getLogger(__name__)
_LE = i18n._LE


class MidonetMixin(agentschedulers_db.DhcpAgentSchedulerDbMixin,
                   am_db.AgentMembershipDbMixin,
                   db_base_plugin_v2.NeutronDbPluginV2,
                   external_net_db.External_net_db_mixin,
                   extradhcpopt_db.ExtraDhcpOptMixin,
                   extraroute_db.ExtraRoute_db_mixin,
                   l3_gwmode_db.L3_NAT_db_mixin,
                   loadbalancer_db.LoadBalancerPluginDb,
                   mn_lb_db.LoadBalancerMixin,
                   pb_db.MidonetPortBindingMixin,
                   portbindings_db.PortBindingMixin,
                   securitygroups_db.SecurityGroupDbMixin):

    supported_extension_aliases = ['agent-membership',
                                   'extra_dhcp_opt',
                                   'extraroute',
                                   'lbaas']

    def __init__(self):
        super(MidonetMixin, self).__init__()

        neutron_extensions.append_api_extensions_path(extensions.__path__)
        self.setup_rpc()

        # Instantiate MidoNet client and initialize
        self._load_client()
        self.client.initialize()

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

    def _load_client(self):
        try:
            self.client = importutils.import_object(cfg.CONF.MIDONET.client)
            LOG.debug("Loaded midonet client '%(client)s'",
                      {'client': self.client})
        except ImportError:
            with excutils.save_and_reraise_exception():
                LOG.exception(_LE("Error loading midonet client '%(client)s'"),
                              {'client': self.client})

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

    def create_network(self, context, network):
        LOG.debug('MidonetMixin.create_network called: network=%r', network)

        net_data = network['network']
        tenant_id = self._get_tenant_id_for_create(context, net_data)
        net_data['tenant_id'] = tenant_id
        self._ensure_default_security_group(context, tenant_id)

        with context.session.begin(subtransactions=True):
            net = super(MidonetMixin, self).create_network(context, network)
            self._process_l3_create(context, net, net_data)
            self.client.create_network_precommit(context, net)

        try:
            self.client.create_network_postcommit(net)
        except Exception as ex:
            LOG.error(_LE("Failed to create a network %(net_id)s in Midonet:"
                          "%(err)s"), {"net_id": net["id"], "err": ex})
            with excutils.save_and_reraise_exception():
                self.delete_network(context, net['id'])

        LOG.debug("MidonetMixin.create_network exiting: net=%r", net)
        return net

    def update_network(self, context, id, network):
        LOG.debug("MidonetMixin.update_network called: id=%(id)r, "
                  "network=%(network)r", {'id': id, 'network': network})

        with context.session.begin(subtransactions=True):
            net = super(MidonetMixin, self).update_network(
                context, id, network)
            self._process_l3_update(context, net, network['network'])
            self.client.update_network_precommit(context, id, net)

        self.client.update_network_postcommit(id, net)

        LOG.debug("MidonetMixin.update_network exiting: net=%r", net)
        return net

    def delete_network(self, context, id):
        LOG.debug("MidonetMixin.delete_network called: id=%r", id)

        with context.session.begin(subtransactions=True):
            self._process_l3_delete(context, id)
            super(MidonetMixin, self).delete_network(context, id)
            self.client.delete_network_precommit(context, id)

        self.client.delete_network_postcommit(id)

        LOG.debug("MidonetMixin.delete_network exiting: id=%r", id)

    def create_subnet(self, context, subnet):
        LOG.debug("MidonetMixin.create_subnet called: subnet=%r", subnet)

        with context.session.begin(subtransactions=True):
            s = super(MidonetMixin, self).create_subnet(context, subnet)
            self.client.create_subnet_precommit(context, s)

        try:
            self.client.create_subnet_postcommit(s)
        except Exception as ex:
            LOG.error(_LE("Failed to create a subnet %(s_id)s in Midonet:"
                          "%(err)s"), {"s_id": s["id"], "err": ex})
            with excutils.save_and_reraise_exception():
                self.delete_subnet(context, s['id'])

        LOG.debug("MidonetMixin.create_subnet exiting: subnet=%r", s)
        return s

    def delete_subnet(self, context, id):
        LOG.debug("MidonetMixin.delete_subnet called: id=%s", id)

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_subnet(context, id)
            self.client.delete_subnet_precommit(context, id)

        self.client.delete_subnet_postcommit(id)

        LOG.debug("MidonetMixin.delete_subnet exiting")

    def update_subnet(self, context, id, subnet):
        LOG.debug("MidonetMixin.update_subnet called: id=%s", id)

        with context.session.begin(subtransactions=True):
            s = super(MidonetMixin, self).update_subnet(context, id, subnet)
            self.client.update_subnet_precommit(context, id, s)

        self.client.update_subnet_postcommit(id, s)

        LOG.debug("MidonetMixin.update_subnet exiting: subnet=%r", s)
        return s

    def create_port(self, context, port):
        LOG.debug("MidonetMixin.create_port called: port=%r", port)

        port_data = port['port']
        with context.session.begin(subtransactions=True):
            # Create a Neutron port
            new_port = super(MidonetMixin, self).create_port(context, port)
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

            # Process port bindings
            self._process_portbindings_create_and_update(context, port_data,
                                                         new_port)
            self._process_mido_portbindings_create_and_update(context,
                                                              port_data,
                                                              new_port)

            self._process_port_create_extra_dhcp_opts(context, new_port,
                                                      dhcp_opts)

            self.client.create_port_precommit(context, new_port)

        try:
            self.client.create_port_postcommit(new_port)
        except Exception as ex:
            LOG.error(_LE("Failed to create a port %(new_port)s: %(err)s"),
                      {"new_port": new_port, "err": ex})
            with excutils.save_and_reraise_exception():
                self.delete_port(context, new_port['id'])

        LOG.debug("MidonetMixin.create_port exiting: port=%r", new_port)
        return new_port

    def delete_port(self, context, id, l3_port_check=True):
        LOG.debug("MidonetMixin.delete_port called: id=%(id)s "
                  "l3_port_check=%(l3_port_check)r",
                  {'id': id, 'l3_port_check': l3_port_check})

        # if needed, check to see if this is a port owned by
        # and l3-router.  If so, we should prevent deletion.
        if l3_port_check:
            self.prevent_l3_port_deletion(context, id)

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).disassociate_floatingips(
                context, id, do_notify=False)
            super(MidonetMixin, self).delete_port(context, id)
            self.client.delete_port_precommit(context, id)

        self.client.delete_port_postcommit(id)

        LOG.debug("MidonetMixin.delete_port exiting: id=%r", id)

    def update_port(self, context, id, port):
        LOG.debug("MidonetMixin.update_port called: id=%(id)s port=%(port)r",
                  {'id': id, 'port': port})

        with context.session.begin(subtransactions=True):

            # update the port DB
            p = super(MidonetMixin, self).update_port(context, id, port)

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

            self.client.update_port_precommit(context, id, p)

        self.client.update_port_postcommit(id, p)

        LOG.debug("MidonetMixin.update_port exiting: p=%r", p)
        return p

    def create_router(self, context, router):
        LOG.debug("MidonetMixin.create_router called: router=%(router)s",
                  {"router": router})

        with context.session.begin(subtransactions=True):
            r = super(MidonetMixin, self).create_router(context, router)
            self.client.create_router_precommit(context, r)

        try:
            self.client.create_router_postcommit(r)
        except Exception as ex:
            LOG.error(_LE("Failed to create a router %(r_id)s in Midonet:"
                          "%(err)s"), {"r_id": r["id"], "err": ex})
            with excutils.save_and_reraise_exception():
                self.delete_router(context, r['id'])

        LOG.debug("MidonetMixin.create_router exiting: router=%(router)s.",
                  {"router": r})
        return r

    def update_router(self, context, id, router):
        LOG.debug("MidonetMixin.update_router called: id=%(id)s "
                  "router=%(router)r", {"id": id, "router": router})

        with context.session.begin(subtransactions=True):
            r = super(MidonetMixin, self).update_router(context, id, router)
            self.client.update_router_precommit(context, id, r)

        self.client.update_router_postcommit(id, r)

        LOG.debug("MidonetMixin.update_router exiting: router=%r", r)
        return r

    def delete_router(self, context, id):
        LOG.debug("MidonetMixin.delete_router called: id=%s", id)

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_router(context, id)
            self.client.delete_router_precommit(context, id)

        self.client.delete_router_postcommit(id)

        LOG.debug("MidonetMixin.delete_router exiting: id=%s", id)

    def add_router_interface(self, context, router_id, interface_info):
        LOG.debug("MidonetMixin.add_router_interface called: "
                  "router_id=%(router_id)s, interface_info=%(interface_info)r",
                  {'router_id': router_id, 'interface_info': interface_info})

        with context.session.begin(subtransactions=True):
            info = super(MidonetMixin, self).add_router_interface(
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
                self.remove_router_interface(context, router_id, info)

        LOG.debug("MidonetMixin.add_router_interface exiting: info=%r", info)
        return info

    def remove_router_interface(self, context, router_id, interface_info):
        LOG.debug("MidonetMixin.remove_router_interface called: "
                  "router_id=%(router_id)s, interface_info=%(interface_info)r",
                  {'router_id': router_id, 'interface_info': interface_info})

        with context.session.begin(subtransactions=True):
            info = super(MidonetMixin, self).remove_router_interface(
                context, router_id, interface_info)
            self.client.remove_router_interface_precommit(context, router_id,
                                                          info)

        self.client.remove_router_interface_postcommit(router_id, info)

        LOG.debug("MidonetMixin.remove_router_interface exiting: info=%r",
                  info)
        return info

    def create_floatingip(self, context, floatingip):
        LOG.debug("MidonetMixin.create_floatingip called: ip=%r", floatingip)

        with context.session.begin(subtransactions=True):
            fip = super(MidonetMixin, self).create_floatingip(context,
                                                              floatingip)
            self.client.create_floatingip_precommit(context, fip)

        try:
            self.client.create_floatingip_postcommit(fip)
        except Exception as ex:
            LOG.error(_LE("Failed to create floating ip %(fip)s: %(err)s"),
                      {"fip": fip, "err": ex})
            with excutils.save_and_reraise_exception():
                # Try removing the fip
                self.delete_floatingip(context, fip['id'])

        LOG.debug("MidonetMixin.create_floatingip exiting: fip=%r", fip)
        return fip

    def delete_floatingip(self, context, id):
        LOG.debug("MidonetMixin.delete_floatingip called: id=%s", id)

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_floatingip(context, id)
            self.client.delete_floatingip_precommit(context, id)

        self.client.delete_floatingip_postcommit(id)

        LOG.debug("MidonetMixin.delete_floatingip exiting: id=%r", id)

    def update_floatingip(self, context, id, floatingip):
        LOG.debug("MidonetMixin.update_floatingip called: id=%(id)s "
                  "floatingip=%(floatingip)s ",
                  {'id': id, 'floatingip': floatingip})

        with context.session.begin(subtransactions=True):
            fip = super(MidonetMixin, self).update_floatingip(context, id,
                                                              floatingip)
            self.client.update_floatingip_precommit(context, id, fip)

            # Update status based on association
            if fip.get('port_id') is None:
                fip['status'] = n_const.FLOATINGIP_STATUS_DOWN
            else:
                fip['status'] = n_const.FLOATINGIP_STATUS_ACTIVE
            self.update_floatingip_status(context, id, fip['status'])

        self.client.update_floatingip_postcommit(id, fip)

        LOG.debug("MidonetMixin.update_floating_ip exiting: fip=%s", fip)
        return fip

    def create_security_group(self, context, security_group, default_sg=False):
        LOG.debug("MidonetMixin.create_security_group called: "
                  "security_group=%(security_group)s "
                  "default_sg=%(default_sg)s ",
                  {'security_group': security_group, 'default_sg': default_sg})

        sg = security_group.get('security_group')
        tenant_id = self._get_tenant_id_for_create(context, sg)
        if not default_sg:
            self._ensure_default_security_group(context, tenant_id)

        # Create the Neutron sg first
        with context.session.begin(subtransactions=True):
            sg = super(MidonetMixin, self).create_security_group(
                context, security_group, default_sg)
            self.client.create_security_group_precommit(context, sg)

        try:
            self.client.create_security_group_postcommit(sg)
        except Exception as ex:
            LOG.error(_LE("Failed to create MidoNet resources for sg %(sg)r,"
                          "error=%(err)r"),
                      {"sg": sg, "err": ex})
            with excutils.save_and_reraise_exception():
                self.delete_security_group(context, sg['id'])

        LOG.debug("MidonetMixin.create_security_group exiting: sg=%r", sg)
        return sg

    def delete_security_group(self, context, id):
        LOG.debug("MidonetMixin.delete_security_group called: id=%s", id)

        sg = super(MidonetMixin, self).get_security_group(context, id)
        if not sg:
            raise ext_sg.SecurityGroupNotFound(id=id)

        if sg["name"] == 'default' and not context.is_admin:
            raise ext_sg.SecurityGroupCannotRemoveDefault()

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_security_group(context, id)
            self.client.delete_security_group_precommit(context, id)

        self.client.delete_security_group_postcommit(id)

        LOG.debug("MidonetMixin.delete_security_group exiting: id=%r", id)

    def create_security_group_rule(self, context, security_group_rule):
        LOG.debug("MidonetMixin.create_security_group_rule called: "
                  "security_group_rule=%(security_group_rule)r",
                  {'security_group_rule': security_group_rule})

        with context.session.begin(subtransactions=True):
            rule = super(MidonetMixin, self).create_security_group_rule(
                context, security_group_rule)
            self.client.create_security_group_rule_precommit(context, rule)

        try:
            self.client.create_security_group_rule_postcommit(rule)
        except Exception as ex:
            LOG.error(_LE('Failed to create security group rule %(sg)s,'
                      'error: %(err)s'), {'sg': rule, 'err': ex})
            with excutils.save_and_reraise_exception():
                self.delete_security_group_rule(context, rule['id'])

        LOG.debug("MidonetMixin.create_security_group_rule exiting: rule=%r",
                  rule)
        return rule

    def create_security_group_rule_bulk(self, context, rules):
        LOG.debug("MidonetMixin.create_security_group_rule_bulk called: "
                  "security_group_rules=%(security_group_rules)r",
                  {'security_group_rules': rules})

        with context.session.begin(subtransactions=True):
            rules = super(
                MidonetMixin, self).create_security_group_rule_bulk_native(
                    context, rules)
            self.client.create_security_group_rule_bulk_precommit(context,
                                                                  rules)

        try:
            self.client.create_security_group_rule_bulk_postcommit(rules)
        except Exception as ex:
            LOG.error(_LE("Failed to create bulk security group rules %(sg)s, "
                          "error: %(err)s"), {"sg": rules, "err": ex})
            with excutils.save_and_reraise_exception():
                for rule in rules:
                    self.delete_security_group_rule(context, rule['id'])

        LOG.debug("MidonetMixin.create_security_group_rule_bulk exiting: "
                  "rules=%r", rules)
        return rules

    def delete_security_group_rule(self, context, sg_rule_id):
        LOG.debug("MidonetMixin.delete_security_group_rule called: "
                  "sg_rule_id=%s", sg_rule_id)

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_security_group_rule(context,
                                                                 sg_rule_id)
            self.client.delete_security_group_rule_precommit(context,
                                                             sg_rule_id)

        self.client.delete_security_group_rule_postcommit(sg_rule_id)

        LOG.debug("MidonetMixin.delete_security_group_rule exiting: id=%r",
                  id)

    def create_vip(self, context, vip):
        LOG.debug("MidonetMixin.create_vip called: %(vip)r",
                  {'vip': vip})
        with context.session.begin(subtransactions=True):

            self._validate_vip_subnet(context, vip)

            v = super(MidonetMixin, self).create_vip(context, vip)
            self.client.create_vip_precommit(context, v)
            v['status'] = constants.ACTIVE
            self.update_status(context, loadbalancer_db.Vip, v['id'],
                               v['status'])

        try:
            self.client.create_vip_postcommit(v)
        except Exception as ex:
            LOG.error(_LE("Failed to create MidoNet resources for vip "
                          "%(vip)r, error: %(err)s"), {"vip": v, 'err': ex})
            with excutils.save_and_reraise_exception():
                self.delete_vip(context, v['id'])

        LOG.debug("MidonetMixin.create_vip exiting: id=%r", v['id'])
        return v

    def delete_vip(self, context, id):
        LOG.debug("MidonetMixin.delete_vip called: id=%(id)r",
                  {'id': id})

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_vip(context, id)
            self.client.delete_vip_precommit(context, id)

        self.client.delete_vip_postcommit(id)

        LOG.debug("MidonetMixin.delete_vip existing: id=%(id)r",
                  {'id': id})

    def update_vip(self, context, id, vip):
        LOG.debug("MidonetMixin.update_vip called: id=%(id)r, "
                  "vip=%(vip)r", {'id': id, 'vip': vip})

        with context.session.begin(subtransactions=True):
            v = super(MidonetMixin, self).update_vip(context, id, vip)
            self.client.update_vip_precommit(context, id, v)

        self.client.update_vip_postcommit(id, v)

        LOG.debug("MidonetMixin.update_vip exiting: id=%(id)r, "
                  "vip=%(vip)r", {'id': id, 'vip': v})
        return v

    def create_pool(self, context, pool):
        LOG.debug("MidonetMixin.create_pool called: %(pool)r", {'pool': pool})

        router_id = self._check_and_get_router_id_for_pool(
            context, pool['pool']['subnet_id'])
        pool['pool'].update({'router_id': router_id})

        with context.session.begin(subtransactions=True):
            p = super(MidonetMixin, self).create_pool(context, pool)
            p['status'] = constants.ACTIVE
            self.update_status(context, loadbalancer_db.Pool, p['id'],
                               p['status'])
            self.client.create_pool_precommit(context, p)

        try:
            self.client.create_pool_postcommit(p)
        except Exception as ex:
            LOG.error(_LE("Failed to create MidoNet resources for pool "
                          "%(pool)r, error: %(err)s"), {"pool": p, 'err': ex})
            with excutils.save_and_reraise_exception():
                self.delete_pool(context, p['id'])

        LOG.debug("MidonetMixin.create_pool exiting: %(pool)r", {'pool': p})
        return p

    def update_pool(self, context, id, pool):
        LOG.debug("MidonetMixin.update_pool called: id=%(id)r, pool=%(pool)r",
                  {'id': id, 'pool': pool})

        with context.session.begin(subtransactions=True):
            p = super(MidonetMixin, self).update_pool(context, id, pool)
            self.client.update_pool_precommit(context, id, p)

        self.client.update_pool_postcommit(id, p)

        LOG.debug("MidonetMixin.update_pool exiting: id=%(id)r, pool=%(pool)r",
                  {'id': id, 'pool': p})
        return p

    def delete_pool(self, context, id):
        LOG.debug("MidonetMixin.delete_pool called: %(id)r", {'id': id})

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_pool(context, id)
            self.client.delete_pool_precommit(context, id)

        self.client.delete_pool_postcommit(id)

        LOG.debug("MidonetMixin.delete_pool exiting: %(id)r", {'id': id})

    def create_member(self, context, member):
        LOG.debug("MidonetMixin.create_member called: %(member)r",
                  {'member': member})

        with context.session.begin(subtransactions=True):
            m = super(MidonetMixin, self).create_member(context, member)
            self.client.create_member_precommit(context, m)
            m['status'] = constants.ACTIVE
            self.update_status(context, loadbalancer_db.Member, m['id'],
                               m['status'])

        try:
            self.client.create_member_postcommit(m)
        except Exception as ex:
            LOG.error(_LE("Failed to create MidoNet resources for member "
                          "%(member)r, error: %(err)s"),
                      {"member": m, 'err': ex})
            with excutils.save_and_reraise_exception():
                self.delete_member(context, m['id'])

        LOG.debug("MidonetMixin.create_member exiting: %(member)r",
                  {'member': m})
        return m

    def update_member(self, context, id, member):
        LOG.debug("MidonetMixin.update_member called: id=%(id)r, "
                  "member=%(member)r", {'id': id, 'member': member})

        with context.session.begin(subtransactions=True):
            m = super(MidonetMixin, self).update_member(context, id, member)
            self.client.update_member_precommit(context, id, m)

        self.client.update_member_postcommit(id, m)

        LOG.debug("MidonetMixin.update_member exiting: id=%(id)r, "
                  "member=%(member)r", {'id': id, 'member': m})
        return m

    def delete_member(self, context, id):
        LOG.debug("MidonetMixin.delete_member called: %(id)r", {'id': id})

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_member(context, id)
            self.client.delete_member_precommit(context, id)

        self.client.delete_member_postcommit(id)

        LOG.debug("MidonetMixin.delete_member exiting: %(id)r", {'id': id})

    def create_health_monitor(self, context, health_monitor):
        LOG.debug("MidonetMixin.create_health_monitor called: "
                  " %(health_monitor)r", {'health_monitor': health_monitor})

        with context.session.begin(subtransactions=True):
            hm = super(MidonetMixin, self).create_health_monitor(
                context, health_monitor)
            self.client.create_health_monitor_precommit(context, hm)

        try:
            self.client.create_health_monitor_postcommit(hm)
        except Exception as ex:
            LOG.error(_LE("Failed to create MidoNet resources for health "
                          "monitor.  %(hm)r, error: %(err)s"),
                      {"hm": hm, 'err': ex})
            with excutils.save_and_reraise_exception():
                self.delete_health_monitor(context, hm['id'])

        LOG.debug("MidonetMixin.create_health_monitor exiting: "
                  "%(health_monitor)r", {'health_monitor': hm})
        return hm

    def update_health_monitor(self, context, id, health_monitor):
        LOG.debug("MidonetMixin.update_health_monitor called: id=%(id)r, "
                  "health_monitor=%(health_monitor)r",
                  {'id': id, 'health_monitor': health_monitor})

        with context.session.begin(subtransactions=True):
            hm = super(MidonetMixin, self).update_health_monitor(
                context, id, health_monitor)
            self.client.update_health_monitor_precommit(context, id, hm)

        self.client.update_health_monitor_postcommit(id, hm)

        LOG.debug("MidonetMixin.update_health_monitor exiting: id=%(id)r, "
                  "health_monitor=%(health_monitor)r",
                  {'id': id, 'health_monitor': hm})
        return hm

    def delete_health_monitor(self, context, id):
        LOG.debug("MidonetMixin.delete_health_monitor called: %(id)r",
                  {'id': id})

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_health_monitor(context, id)
            self.client.delete_health_monitor_precommit(context, id)

        self.client.delete_health_monitor_postcommit(id)

        LOG.debug("MidonetMixin.delete_health_monitor exiting: %(id)r",
                  {'id': id})

    def create_pool_health_monitor(self, context, health_monitor, pool_id):
        LOG.debug("MidonetMixin.create_pool_health_monitor called: "
                  "hm=%(health_monitor)r, pool_id=%(pool_id)r",
                  {'health_monitor': health_monitor, 'pool_id': pool_id})

        pool = self.get_pool(context, pool_id)
        monitors = pool.get('health_monitors')
        if len(monitors) > 0:
            msg = (_LE("MidoNet right now can only support one monitor per "
                       "pool"))
            raise n_exc.BadRequest(resource='pool_health_monitor', msg=msg)

        with context.session.begin(subtransactions=True):
            monitors = super(MidonetMixin,
                             self).create_pool_health_monitor(
                context, health_monitor, pool_id)
            self.client.create_pool_health_monitor_precommit(context,
                                                             health_monitor,
                                                             pool_id)

        try:
            self.client.create_pool_health_monitor_postcommit(health_monitor,
                                                              pool_id)
        except Exception as ex:
            LOG.error(_LE("Failed to create MidoNet resources for pool health "
                          "monitor.  hm: %(hm)r, pool_id: %(pool_id)s, "
                          "error: %(err)s"),
                      {'hm': health_monitor, 'pool_id': pool_id, 'err': ex})
            with excutils.save_and_reraise_exception():
                self.delete_pool_health_monitor(context, health_monitor['id'],
                                                pool_id)

        LOG.debug("MidonetMixin.create_pool_health_monitor exiting: "
                  "%(health_monitor)r, %(pool_id)r",
                  {'health_monitor': health_monitor, 'pool_id': pool_id})
        return monitors

    def delete_pool_health_monitor(self, context, id, pool_id):
        LOG.debug("MidonetMixin.delete_pool_health_monitor called: "
                  "id=%(id)r, pool_id=%(pool_id)r",
                  {'id': id, 'pool_id': pool_id})

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_pool_health_monitor(
                context, id, pool_id)
            self.client.delete_pool_health_monitor_precommit(context,
                                                             id, pool_id)

        self.client.delete_pool_health_monitor_postcommit(id, pool_id)

        LOG.debug("MidonetMixin.delete_pool_health_monitor exiting: "
                  "%(id)r, %(pool_id)r", {'id': id, 'pool_id': pool_id})

    def create_agent_membership(self, context, agent_membership):
        LOG.debug("MidonetMixin.create_agent_membership called: "
                  " %(agent_membership)r",
                  {'agent_membership': agent_membership})

        with context.session.begin(subtransactions=True):
            am = super(MidonetMixin, self).create_agent_membership(
                context, agent_membership)
            self.client.create_agent_membership_precommit(context, am)

        try:
            self.client.create_agent_membership_postcommit(am)
        except Exception as ex:
            LOG.error(_LE("Failed to create agent membership. am: %(am)r, "
                          "error: %(err)s"), {'am': am, 'err': ex})
            with excutils.save_and_reraise_exception():
                self.delete_agent_membership(context, am['id'])

        LOG.debug("MidonetMixin.create_agent_membership exiting: "
                  "%(agent_membership)r", {'agent_membership': am})
        return am

    def get_agent_membership(self, context, id, filters=None, fields=None):
        LOG.debug("MidonetMixin.get_agent_membership called: id=%(id)r",
                  {'id': id})

        with context.session.begin(subtransactions=True):
            am = super(MidonetMixin, self).get_agent_membership(context, id)

        LOG.debug("MidonetMixin.get_agent_membership exiting: id=%(id)r, "
                  "agent_membership=%(agent_membership)r",
                  {'id': id, 'agent_membership': am})
        return am

    def get_agent_memberships(self, context, filters=None, fields=None,
                              sorts=None, limit=None, marker=None,
                              page_reverse=False):
        LOG.debug("MidonetMixin.get_agent_memberships called")

        with context.session.begin(subtransactions=True):
            ams = super(MidonetMixin, self).get_agent_memberships(
                context, filters, fields, sorts, limit, marker, page_reverse)

        LOG.debug("MidonetMixin.get_agent_memberships exiting")
        return ams

    def delete_agent_membership(self, context, id):
        LOG.debug("MidonetMixin.delete_agent_membership called: %(id)r",
                  {'id': id})

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_agent_membership(context, id)
            self.client.delete_agent_membership_precommit(context, id)

        self.client.delete_agent_membership_postcommit(id)

        LOG.debug("MidonetMixin.delete_agent_membership exiting: %(id)r",
                  {'id': id})

    def get_agents(self, context, filters=None, fields=None):
        LOG.debug("MidonetMixin.get_agents called")

        agents = super(MidonetMixin, self).get_agents(context, filters, fields)
        return agents + self.client.get_agents()

    def get_agent(self, context, id, fields=None):
        LOG.debug("MidonetMixin.get_agent called: %(id)r", {'id': id})

        agent = self.client.get_agent(id)
        if not agent:
            agent = super(MidonetMixin, self).get_agent(context, id, fields)
        return agent
