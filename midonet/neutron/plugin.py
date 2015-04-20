# Copyright (C) 2012 Midokura Japan K.K.
# Copyright (C) 2013 Midokura PTE LTD
# Copyright (C) 2014 Midokura SARL.
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
from midonet.neutron.db import db_util
from midonet.neutron.db import port_binding_db as pb_db
from midonet.neutron.db import task_db as task
from midonet.neutron import extensions
from midonet.neutron import plugin_api
from midonet.neutron.rpc import topology_client as top
from neutron.api import extensions as neutron_extensions
from neutron.api.rpc.handlers import dhcp_rpc
from neutron.api.v2 import attributes
from neutron.common import constants as n_const
from neutron.common import exceptions as n_exc
from neutron.common import rpc as n_rpc
from neutron.common import topics
from neutron.db import agents_db
from neutron.db import agentschedulers_db
import neutron.db.api as db
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
                   pb_db.MidonetPortBindingMixin,
                   portbindings_db.PortBindingMixin,
                   securitygroups_db.SecurityGroupDbMixin):

    supported_extension_aliases = ['agent-membership',
                                   'extra_dhcp_opt',
                                   'extraroute',
                                   'lbaas']

    def __init__(self):
        super(MidonetMixin, self).__init__()

        # Instantiate MidoNet API client
        neutron_extensions.append_api_extensions_path(extensions.__path__)
        self.setup_rpc()
        task.create_config_task(db.get_session(), dict(cfg.CONF.MIDONET))

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

    def create_network(self, context, network):
        """Create Neutron network.

        Create a new Neutron network and its corresponding MidoNet bridge.
        """
        LOG.debug('MidonetMixin.create_network called: network=%r', network)

        net_data = network['network']
        tenant_id = self._get_tenant_id_for_create(context, net_data)
        net_data['tenant_id'] = tenant_id
        self._ensure_default_security_group(context, tenant_id)

        with context.session.begin(subtransactions=True):
            net = super(MidonetMixin, self).create_network(context, network)
            self._process_l3_create(context, net, net_data)
            task.create_task(context, task.CREATE, data_type=task.NETWORK,
                             resource_id=net['id'], data=net)

        LOG.debug("MidonetMixin.create_network exiting: net=%r", net)
        return net

    def update_network(self, context, id, network):
        """Update Neutron network.

        Update an existing Neutron network and its corresponding MidoNet
        bridge.
        """
        LOG.debug("MidonetMixin.update_network called: id=%(id)r, "
                  "network=%(network)r", {'id': id, 'network': network})

        with context.session.begin(subtransactions=True):
            net = super(MidonetMixin, self).update_network(
                context, id, network)
            self._process_l3_update(context, net, network['network'])
            task.create_task(context, task.UPDATE, data_type=task.NETWORK,
                             resource_id=id, data=net)

        LOG.debug("MidonetMixin.update_network exiting: net=%r", net)
        return net

    def delete_network(self, context, id):
        """Delete a network and its corresponding MidoNet bridge. """
        LOG.debug("MidonetMixin.delete_network called: id=%r", id)

        with context.session.begin(subtransactions=True):
            self._process_l3_delete(context, id)
            task.create_task(context, task.DELETE, data_type=task.NETWORK,
                             resource_id=id)
            super(MidonetMixin, self).delete_network(context, id)

        LOG.debug("MidonetMixin.delete_network exiting: id=%r", id)

    def create_subnet(self, context, subnet):
        """Create Neutron subnet.

        Creates a Neutron subnet and a DHCP entry in MidoNet bridge.
        """
        LOG.debug("MidonetMixin.create_subnet called: subnet=%r", subnet)
        sn_entry = super(MidonetMixin, self).create_subnet(context, subnet)
        task.create_task(context, task.CREATE, data_type=task.SUBNET,
                         resource_id=sn_entry['id'], data=sn_entry)

        LOG.debug("MidonetMixin.create_subnet exiting: sn_entry=%r", sn_entry)
        return sn_entry

    def delete_subnet(self, context, id):
        """Delete Neutron subnet.

        Delete neutron network and its corresponding MidoNet bridge.
        """
        LOG.debug("MidonetMixin.delete_subnet called: id=%s", id)

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_subnet(context, id)
            task.create_task(context, task.DELETE, data_type=task.SUBNET,
                             resource_id=id)

        LOG.debug("MidonetMixin.delete_subnet exiting")

    def update_subnet(self, context, id, subnet):
        """Update the subnet with new info.
        """
        LOG.debug("MidonetMixin.update_subnet called: id=%s", id)

        with context.session.begin(subtransactions=True):
            s = super(MidonetMixin, self).update_subnet(context, id, subnet)
            task.create_task(context, task.UPDATE, data_type=task.SUBNET,
                             resource_id=id, data=s)

        return s

    def create_port(self, context, port):
        """Create a L2 port in Neutron/MidoNet."""
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

            self._process_portbindings_create_and_update(context, port_data,
                                                         new_port)
            self._process_port_create_extra_dhcp_opts(context, new_port,
                                                      dhcp_opts)
            self._create_midonet_port_binding(context, new_port['id'],
                                              port_data, new_port)

            task.create_task(context, task.CREATE, data_type=task.PORT,
                             resource_id=new_port['id'], data=new_port)

            if not self._is_driver_bound(new_port['device_owner']):
                host, name = self._get_port_info(new_port)

                def is_set(field):
                    return attributes.is_attr_set(field)
                if is_set(host) and is_set(name):
                    task.create_port_binding_task(
                        context, new_port['id'],
                        self._get_interface_name(new_port),
                        self._get_host_name(new_port))

        LOG.debug("MidonetMixin.create_port exiting: port=%r", new_port)
        return new_port

    def delete_port(self, context, id, l3_port_check=True):
        """Delete a neutron port and corresponding MidoNet bridge port."""
        LOG.debug("MidonetMixin.delete_port called: id=%(id)s "
                  "l3_port_check=%(l3_port_check)r",
                  {'id': id, 'l3_port_check': l3_port_check})

        # if needed, check to see if this is a port owned by
        # and l3-router.  If so, we should prevent deletion.
        if l3_port_check:
            self.prevent_l3_port_deletion(context, id)

        with context.session.begin(subtransactions=True):
            port = db_util.get_port(context, id)
            super(MidonetMixin, self).disassociate_floatingips(
                context, id, do_notify=False)
            super(MidonetMixin, self).delete_port(context, id)
            if not self._is_driver_bound(port['device_owner']):
                host, name = self._get_port_info(port)

                def is_set(field):
                    return attributes.is_attr_set(field)
                if is_set(host) and is_set(name):
                    task.delete_port_binding_task(context, port['id'])
            task.create_task(context, task.DELETE, data_type=task.PORT,
                             resource_id=id)

        LOG.debug("MidonetMixin.delete_port exiting: id=%r", id)

    def _unbind_needed(self, old_port, new_port):
        if self._is_driver_bound(old_port['device_owner']):
            return False
        old_host, old_name = self._get_port_info(old_port)
        if not attributes.is_attr_set(old_host):
            return False
        if not attributes.is_attr_set(old_name):
            return False
        new_host, new_name = self._get_port_info(new_port)
        if new_host != old_host and new_host != attributes.ATTR_NOT_SPECIFIED:
            return True
        if new_name != old_name and new_name != attributes.ATTR_NOT_SPECIFIED:
            return True
        return False

    def _bind_needed(self, old_port, new_port):
        if self._is_driver_bound(new_port['device_owner']):
            return False
        old_host, old_name = self._get_port_info(old_port)
        if old_host == attributes.ATTR_NOT_SPECIFIED:
            old_host = None
        if old_name == attributes.ATTR_NOT_SPECIFIED:
            old_name = None
        new_host, new_name = self._get_port_info(new_port)
        if new_host != old_host and new_host != attributes.ATTR_NOT_SPECIFIED:
            return True
        if new_name != old_name and new_name != attributes.ATTR_NOT_SPECIFIED:
            return True
        return False

    def update_port(self, context, id, port):
        """Handle port update, including security groups and fixed IPs."""
        LOG.debug("MidonetMixin.update_port called: id=%(id)s port=%(port)r",
                  {'id': id, 'port': port})
        with context.session.begin(subtransactions=True):

            # update the port DB
            old_port = db_util.get_port(context, id)
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
            self._update_midonet_port_binding(context, p['id'], old_port,
                                              port['port'], p)

            if self._unbind_needed(old_port, p):
                task.delete_port_binding_task(context, old_port['id'])

            task.create_task(context, task.UPDATE, data_type=task.PORT,
                             resource_id=id, data=p)

            if self._bind_needed(old_port, p):
                task.create_port_binding_task(context, old_port['id'],
                                              self._get_interface_name(p),
                                              self._get_host_name(p))

        LOG.debug("MidonetMixin.update_port exiting: p=%r", p)
        return p

    def create_router(self, context, router):
        """Handle router creation.

        When a new Neutron router is created, its corresponding MidoNet router
        is also created.  In MidoNet, this router is initialized with chains
        for inbound and outbound traffic, which will be used to hold other
        chains that include various rules, such as NAT.

        :param router: Router information provided to create a new router.
        """
        LOG.debug("MidonetMixin.create_router called: router=%(router)s",
                  {"router": router})
        r = super(MidonetMixin, self).create_router(context, router)
        task.create_task(context, task.CREATE, data_type=task.ROUTER,
                         resource_id=r['id'], data=r)

        LOG.debug("MidonetMixin.create_router exiting: router=%(router)s.",
                  {"router": r})
        return r

    def update_router(self, context, id, router):
        """Handle router updates."""
        LOG.debug("MidonetMixin.update_router called: id=%(id)s "
                  "router=%(router)r", {"id": id, "router": router})

        with context.session.begin(subtransactions=True):
            r = super(MidonetMixin, self).update_router(context, id, router)
            task.create_task(context, task.UPDATE, data_type=task.ROUTER,
                             resource_id=id, data=r)

        LOG.debug("MidonetMixin.update_router exiting: router=%r", r)
        return r

    def delete_router(self, context, id):
        """Handler for router deletion.

        Deleting a router on Neutron simply means deleting its corresponding
        router in MidoNet.

        :param id: router ID to remove
        """
        LOG.debug("MidonetMixin.delete_router called: id=%s", id)

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_router(context, id)
            task.create_task(context, task.DELETE, data_type=task.ROUTER,
                             resource_id=id)

        LOG.debug("MidonetMixin.delete_router exiting: id=%s", id)

    def add_router_interface(self, context, router_id, interface_info):
        """Handle router linking with network."""
        LOG.debug("MidonetMixin.add_router_interface called: "
                  "router_id=%(router_id)s, interface_info=%(interface_info)r",
                  {'router_id': router_id, 'interface_info': interface_info})

        info = super(MidonetMixin, self).add_router_interface(
            context, router_id, interface_info)

        LOG.debug("MidonetMixin.add_router_interface exiting: info=%r", info)
        return info

    def remove_router_interface(self, context, router_id, interface_info):
        """Handle router un-linking with network."""
        LOG.debug("MidonetMixin.remove_router_interface called: "
                  "router_id=%(router_id)s, interface_info=%(interface_info)r",
                  {'router_id': router_id, 'interface_info': interface_info})

        with context.session.begin(subtransactions=True):
            info = super(MidonetMixin, self).remove_router_interface(
                context, router_id, interface_info)

        LOG.debug("MidonetMixin.remove_router_interface exiting: info=%r",
                  info)
        return info

    def create_floatingip(self, context, floatingip):
        """Handle floating IP creation."""
        LOG.debug("MidonetMixin.create_floatingip called: ip=%r", floatingip)

        fip = super(MidonetMixin, self).create_floatingip(context,
                                                          floatingip)
        task.create_task(context, task.CREATE, data_type=task.FLOATING_IP,
                         resource_id=fip['id'], data=fip)

        LOG.debug("MidonetMixin.create_floatingip exiting: fip=%r", fip)
        return fip

    def delete_floatingip(self, context, id):
        """Handle floating IP deletion."""
        LOG.debug("MidonetMixin.delete_floatingip called: id=%s", id)

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_floatingip(context, id)
            task.create_task(context, task.DELETE,
                             data_type=task.FLOATING_IP, resource_id=id)

        LOG.debug("MidonetMixin.delete_floatingip exiting: id=%r", id)

    def update_floatingip(self, context, id, floatingip):
        """Handle floating IP association and disassociation."""
        LOG.debug("MidonetMixin.update_floatingip called: id=%(id)s "
                  "floatingip=%(floatingip)s ",
                  {'id': id, 'floatingip': floatingip})

        with context.session.begin(subtransactions=True):
            fip = super(MidonetMixin, self).update_floatingip(context, id,
                                                              floatingip)
            task.create_task(context, task.UPDATE,
                             data_type=task.FLOATING_IP, resource_id=id,
                             data=fip)

            # Update status based on association
            if fip.get('port_id') is None:
                fip['status'] = n_const.FLOATINGIP_STATUS_DOWN
            else:
                fip['status'] = n_const.FLOATINGIP_STATUS_ACTIVE
            self.update_floatingip_status(context, id, fip['status'])

        LOG.debug("MidonetMixin.update_floating_ip exiting: fip=%s", fip)
        return fip

    def create_security_group(self, context, security_group, default_sg=False):
        """Create security group.

        Create a new security group, including the default security group.
        In MidoNet, this means creating a pair of chains, inbound and outbound,
        as well as a new port group.
        """
        LOG.debug("MidonetMixin.create_security_group called: "
                  "security_group=%(security_group)s "
                  "default_sg=%(default_sg)s ",
                  {'security_group': security_group, 'default_sg': default_sg})

        sg = security_group.get('security_group')
        tenant_id = self._get_tenant_id_for_create(context, sg)
        if not default_sg:
            self._ensure_default_security_group(context, tenant_id)

        # Create the Neutron sg first
        sg = super(MidonetMixin, self).create_security_group(
            context, security_group, default_sg)
        task.create_task(context, task.CREATE, data_type=task.SECURITY_GROUP,
                         resource_id=sg['id'], data=sg)

        LOG.debug("MidonetMixin.create_security_group exiting: sg=%r", sg)
        return sg

    def delete_security_group(self, context, id):
        """Delete chains for Neutron security group."""
        LOG.debug("MidonetMixin.delete_security_group called: id=%s", id)

        sg = super(MidonetMixin, self).get_security_group(context, id)
        if not sg:
            raise ext_sg.SecurityGroupNotFound(id=id)

        if sg["name"] == 'default' and not context.is_admin:
            raise ext_sg.SecurityGroupCannotRemoveDefault()

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_security_group(context, id)
            task.create_task(context, task.DELETE,
                             data_type=task.SECURITY_GROUP, resource_id=id)

        LOG.debug("MidonetMixin.delete_security_group exiting: id=%r", id)

    def create_security_group_rule(self, context, security_group_rule):
        """Create a security group rule

        Create a security group rule in the Neutron DB and corresponding
        MidoNet resources in its data store.
        """
        LOG.debug("MidonetMixin.create_security_group_rule called: "
                  "security_group_rule=%(security_group_rule)r",
                  {'security_group_rule': security_group_rule})

        rule = super(MidonetMixin, self).create_security_group_rule(
            context, security_group_rule)
        task.create_task(context, task.CREATE,
                         data_type=task.SECURITY_GROUP_RULE,
                         resource_id=rule['id'], data=rule)

        LOG.debug("MidonetMixin.create_security_group_rule exiting: rule=%r",
                  rule)
        return rule

    def create_security_group_rule_bulk(self, context, security_group_rules):
        """Create multiple security group rules

        Create multiple security group rules in the Neutron DB and
        corresponding MidoNet resources in its data store.
        """
        LOG.debug("MidonetMixin.create_security_group_rule_bulk called: "
                  "security_group_rules=%(security_group_rules)r",
                  {'security_group_rules': security_group_rules})

        rules = super(
            MidonetMixin,
            self).create_security_group_rule_bulk_native(context,
                                                         security_group_rules)

        LOG.debug("MidonetMixin.create_security_group_rule_bulk exiting: "
                  "rules=%r", rules)
        return rules

    def delete_security_group_rule(self, context, sg_rule_id):
        """Delete a security group rule

        Delete a security group rule from the Neutron DB and corresponding
        MidoNet resources from its data store.
        """
        LOG.debug("MidonetMixin.delete_security_group_rule called: "
                  "sg_rule_id=%s", sg_rule_id)

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_security_group_rule(context,
                                                                 sg_rule_id)
            task.create_task(context, task.DELETE,
                             data_type=task.SECURITY_GROUP_RULE,
                             resource_id=sg_rule_id)

        LOG.debug("MidonetMixin.delete_security_group_rule exiting: id=%r",
                  id)

    def _validate_vip_subnet(self, context, subnet_id, pool_id):
        # ensure that if the vip subnet is public, the router has its
        # gateway set.
        subnet = self._get_subnet(context, subnet_id)
        if db_util.is_subnet_external(context, subnet):
            router_id = db_util.get_router_from_pool(context, pool_id)
            # router_id should never be None because it was already validated
            # when we created the pool
            assert router_id is not None

            router = self._get_router(context, router_id)
            if router.get('gw_port_id') is None:
                msg = (_LE("The router must have its gateway set if the "
                           "VIP subnet is external"))
                raise n_exc.BadRequest(resource='router', msg=msg)

    def create_vip(self, context, vip):
        LOG.debug("MidonetMixin.create_vip called: %(vip)r",
                  {'vip': vip})
        with context.session.begin(subtransactions=True):

            self._validate_vip_subnet(context, vip['vip']['subnet_id'],
                                      vip['vip']['pool_id'])

            v = super(MidonetMixin, self).create_vip(context, vip)
            task.create_task(context, task.CREATE, data_type=task.VIP,
                             resource_id=v['id'], data=v)
            v['status'] = constants.ACTIVE
            self.update_status(context, loadbalancer_db.Vip, v['id'],
                               v['status'])

        LOG.debug("MidonetMixin.create_vip exiting: id=%r", v['id'])
        return v

    def delete_vip(self, context, id):
        LOG.debug("MidonetMixin.delete_vip called: id=%(id)r",
                  {'id': id})

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_vip(context, id)
            task.create_task(context, task.DELETE, data_type=task.VIP,
                             resource_id=id)

        LOG.debug("MidonetMixin.delete_vip existing: id=%(id)r",
                  {'id': id})

    def update_vip(self, context, id, vip):
        LOG.debug("MidonetMixin.update_vip called: id=%(id)r, "
                  "vip=%(vip)r", {'id': id, 'vip': vip})

        with context.session.begin(subtransactions=True):
            v = super(MidonetMixin, self).update_vip(context, id, vip)
            task.create_task(context, task.UPDATE, data_type=task.VIP,
                             resource_id=id, data=v)

        LOG.debug("MidonetMixin.update_vip exiting: id=%(id)r, "
                  "vip=%(vip)r", {'id': id, 'vip': v})
        return v

    def create_pool(self, context, pool):
        LOG.debug("MidonetMixin.create_pool called: %(pool)r", {'pool': pool})

        subnet = db_util.get_subnet(context, pool['pool']['subnet_id'])
        if subnet is None:
            msg = (_LE("subnet does not exist"))
            raise n_exc.BadRequest(resource='pool', msg=msg)

        if db_util.is_subnet_external(context, subnet):
            msg = (_LE("pool subnet must not be public"))
            raise n_exc.BadRequest(resource='subnet', msg=msg)

        router_id = db_util.get_router_from_subnet(context, subnet)

        if not router_id:
            msg = (_LE("pool subnet must be associated with router"))
            raise n_exc.BadRequest(resource='router', msg=msg)

        pool['pool'].update({'router_id': router_id})

        with context.session.begin(subtransactions=True):
            p = super(MidonetMixin, self).create_pool(context, pool)
            p['status'] = constants.ACTIVE
            self.update_status(context, loadbalancer_db.Pool, p['id'],
                               p['status'])

            task.create_task(context, task.CREATE, data_type=task.POOL,
                             resource_id=p['id'], data=p)

        LOG.debug("MidonetMixin.create_pool exiting: %(pool)r", {'pool': p})
        return p

    def update_pool(self, context, id, pool):
        LOG.debug("MidonetMixin.update_pool called: id=%(id)r, pool=%(pool)r",
                  {'id': id, 'pool': pool})

        with context.session.begin(subtransactions=True):
            p = super(MidonetMixin, self).update_pool(context, id, pool)
            task.create_task(context, task.UPDATE, data_type=task.POOL,
                             resource_id=id, data=p)

        LOG.debug("MidonetMixin.update_pool exiting: id=%(id)r, pool=%(pool)r",
                  {'id': id, 'pool': p})
        return p

    def delete_pool(self, context, id):
        LOG.debug("MidonetMixin.delete_pool called: %(id)r", {'id': id})

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_pool(context, id)
            task.create_task(context, task.DELETE, data_type=task.POOL,
                             resource_id=id)

        LOG.debug("MidonetMixin.delete_pool exiting: %(id)r", {'id': id})

    def create_member(self, context, member):
        LOG.debug("MidonetMixin.create_member called: %(member)r",
                  {'member': member})

        with context.session.begin(subtransactions=True):
            m = super(MidonetMixin, self).create_member(context, member)
            task.create_task(context, task.CREATE, data_type=task.MEMBER,
                             resource_id=m['id'], data=m)
            m['status'] = constants.ACTIVE
            self.update_status(context, loadbalancer_db.Member, m['id'],
                               m['status'])

        LOG.debug("MidonetMixin.create_member exiting: %(member)r",
                  {'member': m})
        return m

    def update_member(self, context, id, member):
        LOG.debug("MidonetMixin.update_member called: id=%(id)r, "
                  "member=%(member)r", {'id': id, 'member': member})

        with context.session.begin(subtransactions=True):
            m = super(MidonetMixin, self).update_member(context, id, member)
            task.create_task(context, task.UPDATE, data_type=task.MEMBER,
                             resource_id=id, data=m)

        LOG.debug("MidonetMixin.update_member exiting: id=%(id)r, "
                  "member=%(member)r", {'id': id, 'member': m})
        return m

    def delete_member(self, context, id):
        LOG.debug("MidonetMixin.delete_member called: %(id)r", {'id': id})

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_member(context, id)
            task.create_task(context, task.DELETE,
                             data_type=task.MEMBER, resource_id=id)

        LOG.debug("MidonetMixin.delete_member exiting: %(id)r", {'id': id})

    def create_health_monitor(self, context, health_monitor):
        LOG.debug("MidonetMixin.create_health_monitor called: "
                  " %(health_monitor)r", {'health_monitor': health_monitor})

        with context.session.begin(subtransactions=True):
            hm = super(MidonetMixin, self).create_health_monitor(
                context, health_monitor)
            task.create_task(context, task.CREATE,
                             data_type=task.HEALTH_MONITOR,
                             resource_id=hm['id'], data=hm)

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
            task.create_task(context, task.UPDATE,
                             data_type=task.HEALTH_MONITOR,
                             resource_id=id, data=hm)

        LOG.debug("MidonetMixin.update_health_monitor exiting: id=%(id)r, "
                  "health_monitor=%(health_monitor)r",
                  {'id': id, 'health_monitor': hm})
        return hm

    def delete_health_monitor(self, context, id):
        LOG.debug("MidonetMixin.delete_health_monitor called: %(id)r",
                  {'id': id})

        with context.session.begin(subtransactions=True):
            super(MidonetMixin, self).delete_health_monitor(context, id)
            task.create_task(context, task.DELETE,
                             data_type=task.HEALTH_MONITOR, resource_id=id)

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

        LOG.debug("MidonetMixin.delete_pool_health_monitor exiting: "
                  "%(id)r, %(pool_id)r", {'id': id, 'pool_id': pool_id})

    def create_agent_membership(self, context, agent_membership):
        LOG.debug("MidonetMixin.create_agent_membership called: "
                  " %(agent_membership)r",
                  {'agent_membership': agent_membership})

        with context.session.begin(subtransactions=True):
            am = super(MidonetMixin, self).create_agent_membership(
                context, agent_membership)
            task.create_task(context, task.CREATE,
                             data_type=task.AGENT_MEMBERSHIP,
                             resource_id=am['id'], data=am)

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
            task.create_task(context, task.DELETE,
                             data_type=task.AGENT_MEMBERSHIP, resource_id=id)

        LOG.debug("MidonetMixin.delete_agent_membership exiting: %(id)r",
                  {'id': id})

    def get_agents(self, context, filters=None, fields=None):
        LOG.debug("MidonetMixin.get_agents called")

        neutron_agents = super(MidonetMixin, self).get_agents(
            context, filters, fields)
        for mido_host in top.get_all_midonet_hosts(
                cfg.CONF.MIDONET.cluster_ip, cfg.CONF.MIDONET.cluster_port):
            mido_agent = top.midonet_host_to_neutron_agent(mido_host)
            neutron_agents = neutron_agents + [mido_agent]
        return neutron_agents

    def get_agent(self, context, id, fields=None):
        LOG.debug("MidonetMixin.get_agent called: %(id)r", {'id': id})

        for mido_host in top.get_all_midonet_hosts(
                cfg.CONF.MIDONET.cluster_ip, cfg.CONF.MIDONET.cluster_port):
            if mido_host.get('id') == id:
                return top.midonet_host_to_neutron_agent(mido_host)
        return super(MidonetMixin, self).get_agent(context, id, fields)


if not cfg.CONF.MIDONET.use_cluster:
    MidonetMixin = plugin_api.MidonetApiMixin
