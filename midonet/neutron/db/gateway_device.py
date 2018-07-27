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

from neutron_lib.api import validators
from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib.callbacks import resources
from neutron_lib.db import model_base
from neutron_lib.db import utils as db_utils
from neutron_lib import exceptions as n_exc
from neutron_lib.exceptions import l3 as l3_exc
from neutron_lib.plugins import constants
from neutron_lib.plugins import directory
from oslo_db import exception as db_exc
from oslo_utils import uuidutils
import sqlalchemy as sa
from sqlalchemy.ext import declarative
from sqlalchemy import orm
from sqlalchemy.orm import exc

from neutron.db import common_db_mixin

from midonet.neutron.extensions import gateway_device as gw_device_ext

GATEWAY_DEVICES = 'midonet_gateway_devices'
GATEWAY_HW_VTEP_DEVICES = 'midonet_gateway_hw_vtep_devices'
GATEWAY_OVERLAY_ROUTER_DEVICES = 'midonet_gateway_overlay_router_devices'
GATEWAY_NETWORK_VLAN_DEVICES = 'midonet_gateway_network_vlan_devices'
GATEWAY_TUNNEL_IPS = 'midonet_gateway_tunnel_ips'
GATEWAY_REMOTE_MAC_TABLES = 'midonet_gateway_remote_mac_tables'


class GatewayDevice(model_base.BASEV2, model_base.HasProjectNoIndex):
    """Represents a gateway device."""

    __tablename__ = GATEWAY_DEVICES
    id = sa.Column(sa.String(36), primary_key=True)
    name = sa.Column(sa.String(255))
    type = sa.Column(sa.String(length=255), nullable=False)


class GatewayHwVtepDevice(model_base.BASEV2):
    """Represents a gateway hardware vtep device."""

    __tablename__ = GATEWAY_HW_VTEP_DEVICES
    device_id = sa.Column(sa.String(36),
                          sa.ForeignKey('midonet_gateway_devices.id',
                          ondelete="CASCADE"),
                          nullable=False, primary_key=True)
    management_ip = sa.Column(sa.String(length=64), nullable=False,
                              unique=True)
    management_port = sa.Column(sa.Integer(), nullable=False)
    management_protocol = sa.Column(sa.String(length=255),
                                    nullable=False)
    gateway_device = orm.relationship(
        GatewayDevice,
        backref=orm.backref('hw_vtep', cascade='delete', lazy='joined'),
        primaryjoin="GatewayDevice.id==GatewayHwVtepDevice.device_id")


class GatewayVirtualDevice(object):
    """Represents a virtual gateway device."""
    device_id = sa.Column(sa.String(36), nullable=False, primary_key=True)

    @declarative.declared_attr
    def __table_args__(cls):
        return (
            sa.ForeignKeyConstraint(['device_id'],
                                    ['midonet_gateway_devices.id'],
                                    ondelete="CASCADE"),
            model_base.BASEV2.__table_args__,
        )


def get_type_model_map():
    return {table.resource_type: table
            for table in GatewayVirtualDevice.__subclasses__()}


def _resource_id_column(foreign_key):
    return sa.Column(sa.String(36),
                     sa.ForeignKey(foreign_key),
                     nullable=False)


def _gateway_device_relation(class_name, ref_key):
    relation = "GatewayDevice.id==" + class_name + ".device_id"
    return orm.relationship(
        GatewayDevice,
        backref=orm.backref(ref_key, cascade='delete', lazy='joined'),
        primaryjoin=relation)


class GatewayOverlayRouterDevice(GatewayVirtualDevice, model_base.BASEV2):
    """Represents a gateway overlay router device."""

    __tablename__ = GATEWAY_OVERLAY_ROUTER_DEVICES
    resource_id = _resource_id_column('routers.id')
    gateway_device = _gateway_device_relation('GatewayOverlayRouterDevice',
                                              'overlay_router')
    resource_type = gw_device_ext.ROUTER_DEVICE_TYPE


class GatewayVlanNetworkDevice(GatewayVirtualDevice, model_base.BASEV2):
    """Represents a gateway vlan network device."""

    __tablename__ = GATEWAY_NETWORK_VLAN_DEVICES
    resource_id = _resource_id_column('networks.id')
    gateway_device = _gateway_device_relation('GatewayVlanNetworkDevice',
                                              'vlan_network')
    resource_type = gw_device_ext.NETWORK_VLAN_TYPE


class GatewayTunnelIp(model_base.BASEV2):
    """Represents a IP address for VTEP."""

    __tablename__ = GATEWAY_TUNNEL_IPS
    device_id = sa.Column(sa.String(36),
                          sa.ForeignKey('midonet_gateway_devices.id',
                          ondelete="CASCADE"),
                          nullable=False, primary_key=True)
    tunnel_ip = sa.Column(sa.String(64), nullable=False, unique=True)
    gateway_device = orm.relationship(
        GatewayDevice,
        backref=orm.backref('tunnel_ip_list', cascade='delete', lazy='joined'),
        primaryjoin="GatewayDevice.id==GatewayTunnelIp.device_id")


class GatewayRemoteMacTable(model_base.BASEV2):
    """Represents a mac table for vtep."""

    __tablename__ = GATEWAY_REMOTE_MAC_TABLES
    id = sa.Column(sa.String(36), primary_key=True)
    device_id = sa.Column(sa.String(36),
                          sa.ForeignKey('midonet_gateway_devices.id',
                          ondelete="CASCADE"),
                          nullable=False)
    mac_address = sa.Column(sa.String(length=32), nullable=False,
                            unique=True)
    vtep_address = sa.Column(sa.String(length=64), nullable=False)
    segmentation_id = sa.Column(sa.Integer())
    gateway_device = orm.relationship(
        GatewayDevice,
        backref=orm.backref('mac_table_list', cascade='delete', lazy='joined'),
        primaryjoin="GatewayDevice.id==GatewayRemoteMacTable.device_id")


@registry.has_registry_receivers
class GwDeviceDbMixin(gw_device_ext.GwDevicePluginBase,
                      common_db_mixin.CommonDbMixin):
    """Mixin class to add gateway device."""

    __native_bulk_support = False

    def _ensure_gateway_device_not_in_use(self, context, gw_dev_id):
        """Ensure that gateway_device is not in use."""

        l2gw_plugin = directory.get_plugin('L2GW')
        if l2gw_plugin:
            if l2gw_plugin._get_l2gw_devices_by_device_id(context, gw_dev_id):
                raise gw_device_ext.GatewayDeviceInUse(id=gw_dev_id)
        gw_dev = self._get_gateway_device(context, gw_dev_id)

        return gw_dev

    def _get_gateway_device(self, context, id):
        try:
            query = self._model_query(context, GatewayDevice)
            gw_dev_db = query.filter(GatewayDevice.id == id).one()

        except exc.NoResultFound:
            raise gw_device_ext.GatewayDeviceNotFound(id=id)

        return gw_dev_db

    def _get_gateway_device_from_resource(self, context, resource_type,
                                          resource_id):
        try:
            device_model = get_type_model_map()[resource_type]
            query = self._model_query(context, device_model)
            gw_dev_db = query.filter(
                device_model.resource_id == resource_id).one()

        except exc.NoResultFound:
            pass

        else:
            return gw_dev_db

    def _get_hw_vtep_from_management_ip(self, context, management_ip):
        try:
            query = self._model_query(context, GatewayHwVtepDevice)
            gw_hw_vtep_db = query.filter(
                GatewayHwVtepDevice.management_ip == management_ip).one()

        except exc.NoResultFound:
            pass

        else:
            return gw_hw_vtep_db

    def _get_remote_mac_entry(self, context, id, gateway_device_id):
        try:
            query = self._model_query(context, GatewayRemoteMacTable)
            rmt_db = query.filter(GatewayRemoteMacTable.id == id).one()
            if rmt_db.device_id != gateway_device_id:
                raise gw_device_ext.RemoteMacEntryWrongGatewayDevice(
                    id=id, gateway_device_id=gateway_device_id)

        except exc.NoResultFound:
            raise gw_device_ext.RemoteMacEntryNotFound(id=id)

        return rmt_db

    def _get_tunnel_ip_from_ip_address(self, context, ip):
        try:
            query = self._model_query(context, GatewayTunnelIp)
            gw_tun_ip_db = query.filter(
                GatewayTunnelIp.tunnel_ip == ip).one()

        except exc.NoResultFound:
            pass

        else:
            return gw_tun_ip_db

    def _make_gateway_device_dict(self, gw_dev_db, fields=None):
        res = {'id': gw_dev_db['id'],
               'name': gw_dev_db['name'],
               'type': gw_dev_db['type'],
               'tenant_id': gw_dev_db['tenant_id'],
               'tunnel_ips': [],
               'remote_mac_entries': []}
        if gw_dev_db['type'] == gw_device_ext.NETWORK_VLAN_TYPE:
            res['management_ip'] = None
            res['management_port'] = None
            res['management_protocol'] = None
            res['resource_id'] = gw_dev_db.vlan_network[0]['resource_id']
            # tunnel_ips and remote_mac_entries are not set
            return self._fields(res, fields)

        if gw_dev_db['type'] == gw_device_ext.HW_VTEP_TYPE:
            hw_vtep = gw_dev_db.hw_vtep[0]
            res['management_ip'] = hw_vtep['management_ip']
            res['management_port'] = hw_vtep['management_port']
            res['management_protocol'] = hw_vtep['management_protocol']
            res['resource_id'] = ""
        if gw_dev_db['type'] == gw_device_ext.ROUTER_DEVICE_TYPE:
            res['management_ip'] = None
            res['management_port'] = None
            res['management_protocol'] = None
            res['resource_id'] = gw_dev_db.overlay_router[0]['resource_id']
        res['tunnel_ips'] = list(map(
            lambda n: n['tunnel_ip'], gw_dev_db.tunnel_ip_list))
        for item in gw_dev_db.mac_table_list:
            entry = {'id': item['id'],
                     'mac_address': item['mac_address'],
                     'vtep_address': item['vtep_address'],
                     'segmentation_id': item['segmentation_id']}
            res['remote_mac_entries'].append(entry)

        return self._fields(res, fields)

    def _make_remote_mac_dict(self, gw_rme_db, fields=None):
        res = {'id': gw_rme_db['id'],
               'mac_address': gw_rme_db['mac_address'],
               'vtep_address': gw_rme_db['vtep_address'],
               'segmentation_id': gw_rme_db['segmentation_id'],
               'device_id': gw_rme_db['device_id']}
        return self._fields(res, fields)

    def _tunnel_ip_db_add(self, context, gw_dev_id, add_ips):
        for ip in add_ips:
            tun_ip_db = GatewayTunnelIp(
                device_id=gw_dev_id,
                tunnel_ip=ip)
            context.session.add(tun_ip_db)

    def _tunnel_ip_db_delete(self, context, gw_dev_id, delete_ips):
        for ip in delete_ips:
            tun_ip_db = self._get_tunnel_ip_from_ip_address(context, ip)
            context.session.delete(tun_ip_db)

    def _update_gateway_device_db(self, context, gw_dev_id, data):
        """Update the DB object.

        following parameter can be updated.
            name, tunnel_ips
        """

        add_ips, delete_ips = [], []
        with context.session.begin(subtransactions=True):
            gw_dev_db = self._get_gateway_device(context, gw_dev_id)
            if data.get('tunnel_ips'):
                exist_ips = list(map(
                    lambda n: n['tunnel_ip'], gw_dev_db.tunnel_ip_list))
                add_ips = set(data['tunnel_ips']) - set(exist_ips)
                delete_ips = set(exist_ips) - set(data['tunnel_ips'])
            if delete_ips:
                self._tunnel_ip_db_delete(context, gw_dev_id, delete_ips)
            if add_ips:
                self._tunnel_ip_db_add(context, gw_dev_id, add_ips)
            if data:
                gw_dev_db.update(data)
        context.session.refresh(gw_dev_db)

        return gw_dev_db

    def _validate_gateway_device(self, context, gw_dev):
        if gw_dev['type'] == gw_device_ext.HW_VTEP_TYPE:
            self._validate_hw_vtep(gw_dev, context)
        if gw_dev['type'] == gw_device_ext.ROUTER_DEVICE_TYPE:
            self._validate_router_vtep(gw_dev, context)
        if gw_dev['type'] == gw_device_ext.NETWORK_VLAN_TYPE:
            self._validate_vlan_network(gw_dev, context)

    def _validate_hw_vtep(self, gw_dev, context):
        if not gw_dev['management_ip'] or not gw_dev['management_port']:
            raise gw_device_ext.HwVtepTypeInvalid(type=gw_dev['type'])
        if self._get_hw_vtep_from_management_ip(
                context, gw_dev['management_ip']):
            raise gw_device_ext.GatewayDeviceParamDuplicate(
                param_name='management_ip',
                param_value=gw_dev['management_ip'])

    def _validate_resource_router_vtep(self, context, router_id):
        # Check specified router existence
        l3plugin = directory.get_plugin(constants.L3)

        try:
            l3plugin.get_router(context, router_id)
        except l3_exc.RouterNotFound:
            raise gw_device_ext.ResourceNotFound(resource_id=router_id)

        if self._get_gateway_device_from_resource(
                context, gw_device_ext.ROUTER_DEVICE_TYPE, router_id):
            raise gw_device_ext.DeviceInUseByGatewayDevice(
                resource_id=router_id, resource_type='router')

    def _validate_router_vtep(self, gw_dev, context):
        if not gw_dev['resource_id']:
            raise gw_device_ext.RouterVtepTypeInvalid(type=gw_dev['type'])
        self._validate_resource_router_vtep(context,
                                            gw_dev['resource_id'])

    def _validate_resource_vlan_network(self, context, network_id):
        # Check specified netowrk existence
        core_plugin = directory.get_plugin()

        try:
            core_plugin.get_network(context, network_id)
        except n_exc.NetworkNotFound:
            raise gw_device_ext.ResourceNotFound(resource_id=network_id)

        if self._get_gateway_device_from_resource(
                context, gw_device_ext.NETWORK_VLAN_TYPE, network_id):
            raise gw_device_ext.DeviceInUseByGatewayDevice(
                resource_id=network_id, resource_type='network')

    def _validate_vlan_network(self, gw_dev, context):
        if not gw_dev['resource_id']:
            raise gw_device_ext.NetworkVlanTypeInvalid(type=gw_dev['type'])
        self._validate_resource_vlan_network(context,
                                             gw_dev['resource_id'])

    def _validate_tunnel_ips(self, tunnel_ips, gw_type):
        if len(tunnel_ips) > 1:
            raise gw_device_ext.TunnelIPsExhausted()
        if len(tunnel_ips) == 0:
            raise gw_device_ext.TunnelIPsRequired(gw_type=gw_type)

    def create_gateway_device(self, context, gw_device):
        """Create a gateway device"""
        gw_dev = gw_device['gateway_device']
        tenant_id = gw_dev['tenant_id']
        self._validate_gateway_device(context, gw_dev)
        if gw_dev['type'] != gw_device_ext.NETWORK_VLAN_TYPE:
            self._validate_tunnel_ips(gw_dev.get('tunnel_ips') or [],
                                      gw_dev['type'])

        with context.session.begin(subtransactions=True):
            gw_dev_db = GatewayDevice(
                id=uuidutils.generate_uuid(),
                name=gw_dev['name'],
                type=(gw_dev['type'] or gw_device_ext.HW_VTEP_TYPE),
                tenant_id=tenant_id)
            context.session.add(gw_dev_db)
            if gw_dev_db['type'] == gw_device_ext.HW_VTEP_TYPE:
                gw_hw_vtep_db = GatewayHwVtepDevice(
                    device_id=gw_dev_db['id'],
                    management_ip=gw_dev['management_ip'],
                    management_port=gw_dev['management_port'],
                    management_protocol=(
                        gw_dev['management_protocol'] or gw_device_ext.OVSDB))
                context.session.add(gw_hw_vtep_db)

            device_model = get_type_model_map().get(gw_dev_db['type'])
            if device_model:
                gw_vlan_db = device_model(
                    device_id=gw_dev_db['id'],
                    resource_id=gw_dev['resource_id'])
                context.session.add(gw_vlan_db)

            # In network vlan type gateway device, tunnel_ips should be None
            if gw_dev.get('tunnel_ips'):
                self._tunnel_ip_db_add(context,
                                       gw_dev_db['id'], gw_dev['tunnel_ips'])

        return self._make_gateway_device_dict(gw_dev_db)

    def create_gateway_device_remote_mac_entry(self, context,
                                               gateway_device_id,
                                               remote_mac_entry):
        rme = remote_mac_entry['remote_mac_entry']

        try:
            with context.session.begin(subtransactions=True):
                gw_rmt_db = GatewayRemoteMacTable(
                    id=uuidutils.generate_uuid(),
                    device_id=gateway_device_id,
                    mac_address=rme['mac_address'],
                    segmentation_id=rme['segmentation_id'],
                    vtep_address=rme['vtep_address'])
                context.session.add(gw_rmt_db)
        except db_exc.DBDuplicateEntry:
            raise gw_device_ext.DuplicateRemoteMacEntry(
                mac_address=rme['mac_address'])

        return self._make_remote_mac_dict(gw_rmt_db)

    def delete_gateway_device(self, context, id):
        gw_dev = self._ensure_gateway_device_not_in_use(context, id)
        with context.session.begin(subtransactions=True):
            context.session.delete(gw_dev)

    def delete_gateway_device_remote_mac_entry(self, context, id,
                                               gateway_device_id):
        rmt_db = self._get_remote_mac_entry(context, id, gateway_device_id)
        with context.session.begin(subtransactions=True):
            context.session.delete(rmt_db)

    def get_gateway_device(self, context, id, fields=None):
        gw_dev = self._get_gateway_device(context, id)
        return self._make_gateway_device_dict(gw_dev, fields)

    def get_gateway_devices(self, context, filters=None, fields=None,
                            sorts=None, limit=None, marker=None,
                            page_reverse=False):
        marker_obj = db_utils.get_marker_obj(self, context, 'gateway_device',
                                             limit, marker)

        return self._get_collection(context,
                                    GatewayDevice,
                                    self._make_gateway_device_dict,
                                    filters=filters, fields=fields,
                                    sorts=sorts,
                                    limit=limit, marker_obj=marker_obj,
                                    page_reverse=page_reverse)

    def get_gateway_device_remote_mac_entries(self, context, gateway_device_id,
                                              filters=None, fields=None,
                                              sorts=None, limit=None,
                                              marker=None, page_reverse=False):
        marker_obj = db_utils.get_marker_obj(self, context, 'remote_mac_entry',
                                             limit, marker)
        filters['device_id'] = [gateway_device_id]
        return self._get_collection(context,
                                    GatewayRemoteMacTable,
                                    self._make_remote_mac_dict,
                                    filters=filters, fields=fields,
                                    sorts=sorts,
                                    limit=limit, marker_obj=marker_obj,
                                    page_reverse=page_reverse)

    def get_gateway_device_remote_mac_entry(self, context, id,
                                            gateway_device_id, fields=None):
        rme = self._get_remote_mac_entry(context, id, gateway_device_id)
        return self._make_remote_mac_dict(rme, fields)

    def update_gateway_device(self, context, id, gw_device):
        gw_dev = gw_device['gateway_device']
        gw_dev_db = self._get_gateway_device(context, id)
        if gw_dev_db.type == gw_device_ext.NETWORK_VLAN_TYPE:
            del gw_device['gateway_device']['tunnel_ips']
        elif validators.is_attr_set(gw_dev.get('tunnel_ips')):
            self._validate_tunnel_ips(gw_dev.get('tunnel_ips'),
                                      gw_dev_db.type)
        gw_dev_db = self._update_gateway_device_db(context, id, gw_dev)
        return self._make_gateway_device_dict(gw_dev_db)

    @registry.receives(resources.ROUTER, [events.BEFORE_DELETE])
    def _gateway_router_device_callback(self, resource, event,
                                        trigger, payload=None):
        # TODO(boden): refactor this back into _gateway_device_callback once
        # NETWORK resources use paylaods
        if resource == resources.ROUTER:
            resource_id = payload.resource_id
            gw_dev_type = gw_device_ext.ROUTER_DEVICE_TYPE
            resource_type = 'router'
        else:
            return
        context = payload.context
        if self._get_gateway_device_from_resource(context,
                                                  gw_dev_type,
                                                  resource_id):
            raise gw_device_ext.DeviceInUseByGatewayDevice(
                resource_id=resource_id, resource_type=resource_type)

    @registry.receives(resources.NETWORK, [events.PRECOMMIT_DELETE])
    def _gateway_device_callback(self, resource, event, trigger, **kwargs):
        if resource == resources.NETWORK:
            resource_id = kwargs['network_id']
            gw_dev_type = gw_device_ext.NETWORK_VLAN_TYPE
            resource_type = 'network'
        else:
            return
        context = kwargs.get('context')
        if self._get_gateway_device_from_resource(context,
                                                  gw_dev_type,
                                                  resource_id):
            raise gw_device_ext.DeviceInUseByGatewayDevice(
                resource_id=resource_id, resource_type=resource_type)
