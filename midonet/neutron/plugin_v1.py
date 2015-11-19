# Copyright (C) 2012 Midokura Japan K.K.
# Copyright (C) 2013 Midokura PTE LTD
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
from oslo_db import exception as oslo_db_exc
from oslo_log import log as logging
from oslo_utils import excutils

from neutron.common import constants as n_const
from neutron.common import exceptions as n_exc
from neutron.db import api as db_api
from neutron.db import l3_gwmode_db
from neutron.extensions import extra_dhcp_opt as edo_ext
from neutron.extensions import securitygroup as ext_sg
from neutron import i18n

from midonet.neutron import plugin


LOG = logging.getLogger(__name__)
_LE = i18n._LE
_LW = i18n._LW


midonet_opts = [
    cfg.StrOpt('midonet_uri', default='http://localhost:8080/midonet-api',
               help=_('MidoNet API server URI.')),
    cfg.StrOpt('username', default='admin',
               help=_('MidoNet admin username.')),
    cfg.StrOpt('password', default='passw0rd',
               secret=True,
               help=_('MidoNet admin password.')),
    cfg.StrOpt('project_id',
               default='77777777-7777-7777-7777-777777777777',
               help=_('ID of the project that MidoNet admin user '
                      'belongs to.'))
]


cfg.CONF.register_opts(midonet_opts, "MIDONET")


class MidonetMixin(plugin.MidonetMixinBase,
                   l3_gwmode_db.L3_NAT_db_mixin):

    supported_extension_aliases = ['ext-gw-mode', 'extra_dhcp_opt']

    def create_network(self, context, network):
        LOG.debug('MidonetMixin.create_network called: network=%r', network)

        net_data = network['network']
        tenant_id = self._get_tenant_id_for_create(context, net_data)
        net_data['tenant_id'] = tenant_id
        self._ensure_default_security_group(context, tenant_id)

        with context.session.begin(subtransactions=True):
            net = super(MidonetMixin, self).create_network(context, network)
            net_data['id'] = net['id']
            self._process_l3_create(context, net, net_data)
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
            try:
                super(MidonetMixin, self).delete_network(context, id)
            except n_exc.NetworkInUse as ex:
                LOG.warning(_LW("Error deleting network %(net)s, retrying..."),
                            {'net': id})
                # Contention for DHCP port deletion and network deletion occur
                # often which leads to NetworkInUse error.  Retry to get
                # around this problem.
                raise oslo_db_exc.RetryRequest(ex)

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
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to create a subnet %(s_id)s in Midonet:"
                              "%(err)s"), {"s_id": s["id"], "err": ex})
                try:
                    self.delete_subnet(context, s['id'])
                except Exception:
                    LOG.exception(_LE("Failed to delete subnet %s"), s['id'])

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
        # REVISIT(yamamoto): this nested transaction is a workaround
        # for bug #1490917.
        with db_api.autonested_transaction(context.session):
            # Create a Neutron port
            new_port = super(MidonetMixin, self).create_port(context, port)

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

            # Bind security groups to the port
            self._ensure_default_security_group_on_port(context, port)
            sg_ids = self._get_security_groups_on_port(context, port)
            self._process_port_create_security_group(context, new_port, sg_ids)

            # Process port bindings
            self._process_portbindings_create_and_update(context, port_data,
                                                         new_port)

            self._process_port_create_extra_dhcp_opts(context, new_port,
                                                      dhcp_opts)
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
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to create a router %(r_id)s in Midonet:"
                              "%(err)s"), {"r_id": r["id"], "err": ex})
                try:
                    self.delete_router(context, r['id'])
                except Exception:
                    LOG.exception(_LE("Failed to delete a router %s"), r["id"])

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

        by_port = bool(interface_info.get('port_id'))
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
                if not by_port:
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
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to create floating ip %(fip)s: %(err)s"),
                          {"fip": fip, "err": ex})
                try:
                    self.delete_floatingip(context, fip['id'])
                except Exception:
                    LOG.exception(_LE("Failed to delete a floating ip %s"),
                                  fip['id'])

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
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to create MidoNet resources for "
                              "sg %(sg)r, error=%(err)r"),
                          {"sg": sg, "err": ex})
                try:
                    self.delete_security_group(context, sg['id'])
                except Exception:
                    LOG.exception(_LE("Failed to delete a security group %s"),
                                  sg['id'])

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
            with excutils.save_and_reraise_exception():
                LOG.error(_LE('Failed to create security group rule %(sg)s,'
                          'error: %(err)s'), {'sg': rule, 'err': ex})
                try:
                    self.delete_security_group_rule(context, rule['id'])
                except Exception:
                    LOG.exception(_LE("Failed to delete "
                                      "a security group rule %s"), rule['id'])

        LOG.debug("MidonetMixin.create_security_group_rule exiting: rule=%r",
                  rule)
        return rule

    def create_security_group_rule_bulk(self, context, security_group_rules):
        LOG.debug("MidonetMixin.create_security_group_rule_bulk called: "
                  "security_group_rules=%(security_group_rules)r",
                  {'security_group_rules': security_group_rules})

        with context.session.begin(subtransactions=True):
            rules = super(
                MidonetMixin, self).create_security_group_rule_bulk_native(
                    context, security_group_rules)
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


class MidonetPluginV2(MidonetMixin):

    vendor_extensions = MidonetMixin.supported_extension_aliases
    # NOTE(yamamoto): While the order in this list doesn't matter
    # functionality-wise, it's alphabetically sorted for easier comparison.
    supported_extension_aliases = [
        'agent',
        'binding',
        'dhcp_agent_scheduler',
        'external-net',
        'quotas',
        'router',
        'security-group',
        'subnet_allocation',
    ] + vendor_extensions

    __native_bulk_support = True

    def __init__(self):
        super(MidonetPluginV2, self).__init__()


def list_opts():
    return [
        ('midonet', midonet_opts),
    ]
