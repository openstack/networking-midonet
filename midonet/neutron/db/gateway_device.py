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

from midonet.neutron.common import constants as midonet_const
from midonet.neutron.extensions import gateway_device
from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.db import common_db_mixin
from neutron.db import model_base
from neutron.extensions import l3
from neutron import manager
from neutron.plugins.common import constants as service_constants
from oslo_utils import uuidutils

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import exc

GATEWAY_DEVICES = 'midonet_gateway_devices'
GATEWAY_HW_VTEP_DEVICES = 'midonet_gateway_hw_vtep_devices'
GATEWAY_OVERLAY_ROUTER_DEVICES = 'midonet_gateway_overlay_router_devices'
GATEWAY_TUNNEL_IPS = 'midonet_gateway_tunnel_ips'
GATEWAY_REMOTE_MAC_TABLES = 'midonet_gateway_remote_mac_tables'


class GatewayDevice(model_base.BASEV2):
    """Represents a gateway device."""

    __tablename__ = GATEWAY_DEVICES
    id = sa.Column(sa.String(36), primary_key=True)
    name = sa.Column(sa.String(255))
    type = sa.Column(sa.String(length=255), nullable=False)
    tenant_id = sa.Column(sa.String(length=255))


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


class GatewayOverlayRouterDevice(model_base.BASEV2):
    """Represents a gateway overlay router device."""

    __tablename__ = GATEWAY_OVERLAY_ROUTER_DEVICES
    device_id = sa.Column(sa.String(36),
                          sa.ForeignKey('midonet_gateway_devices.id',
                          ondelete="CASCADE"),
                          nullable=False, primary_key=True)
    resource_id = sa.Column(sa.String(length=36), nullable=False)
    gateway_device = orm.relationship(
        GatewayDevice,
        backref=orm.backref('overlay_router', cascade='delete', lazy='joined'),
        primaryjoin="GatewayDevice.id==GatewayOverlayRouterDevice.device_id")


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
                          nullable=False, primary_key=True)
    mac_address = sa.Column(sa.String(length=32), nullable=False,
                            unique=True)
    vtep_address = sa.Column(sa.String(length=64), nullable=False,
                             unique=True)
    segmentation_id = sa.Column(sa.Integer())
    gateway_device = orm.relationship(
        GatewayDevice,
        backref=orm.backref('mac_table_list', cascade='delete', lazy='joined'),
        primaryjoin="GatewayDevice.id==GatewayRemoteMacTable.device_id")


class GwDeviceDbMixin(gateway_device.GwDevicePluginBase,
                      common_db_mixin.CommonDbMixin):
    """Mixin class to add gateway device."""

    __native_bulk_support = False

    def _check_for_router(self, context, gw_dev_id):
        l3plugin = manager.NeutronManager.get_service_plugins().get(
            service_constants.L3_ROUTER_NAT)

        try:
            gw_dev = self.get_gateway_device(context, gw_dev_id)
            l3plugin._ensure_router_not_in_use(context, gw_dev['resource_id'])
        except l3.RouterInUse:
            raise gateway_device.GatewayDeviceInUse(id=gw_dev['id'])

    def _check_gateway_device_exists(self, context, gateway_device_id):
        self._get_gateway_device(context, gateway_device_id)

    def _ensure_gateway_device_not_in_use(self, context, gw_dev_id):
        """Ensure that resource is not in use.
           Checking logic is different from gateway device type
           router: there are any interfaces or not.
           hw_vtep: NOP
        """
        gw_dev = self._get_gateway_device(context, gw_dev_id)
        if gw_dev['type'] == gateway_device.ROUTER_DEVICE_TYPE:
            self._check_for_router(context, gw_dev_id)

        return gw_dev

    def _get_gateway_device(self, context, id):
        try:
            query = self._model_query(context, GatewayDevice)
            gw_dev_db = query.filter(GatewayDevice.id == id).one()

        except exc.NoResultFound:
            raise gateway_device.GatewayDeviceNotFound(id=id)

        return gw_dev_db

    def _get_gateway_device_from_router(self, context, router_id):
        try:
            query = self._model_query(context, GatewayOverlayRouterDevice)
            gw_dev_db = query.filter(
                GatewayOverlayRouterDevice.resource_id == router_id).one()

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

    def _get_remote_mac_entry(self, context, id):
        try:
            query = self._model_query(context, GatewayRemoteMacTable)
            rmt_db = query.filter(GatewayRemoteMacTable.id == id).one()

        except exc.NoResultFound:
            raise gateway_device.RemoteMacEntryNotFound(id=id)

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
               'remote_mac_entries': []}
        if gw_dev_db['type'] == gateway_device.HW_VTEP_TYPE:
            res['management_ip'] = gw_dev_db.hw_vtep[0]['management_ip']
            res['management_port'] = gw_dev_db.hw_vtep[0]['management_port']
            res['management_protocol'] = \
                gw_dev_db.hw_vtep[0]['management_protocol']
            res['resource_id'] = ""
        if gw_dev_db['type'] == gateway_device.ROUTER_DEVICE_TYPE:
            res['management_ip'] = None
            res['management_port'] = None
            res['management_protocol'] = None
            res['resource_id'] = gw_dev_db.overlay_router[0]['resource_id']
        res['tunnel_ips'] = \
            list(map(lambda n: n['tunnel_ip'], gw_dev_db.tunnel_ip_list))
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
               'segmentation_id': gw_rme_db['segmentation_id']}
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
                exist_ips = list(map(lambda n: n['tunnel_ip'],
                            gw_dev_db.tunnel_ip_list))
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
        if gw_dev['type'] == gateway_device.HW_VTEP_TYPE:
            self._validate_hw_vtep(gw_dev, context)
        if gw_dev['type'] == gateway_device.ROUTER_DEVICE_TYPE:
            self._validate_router_vtep(gw_dev, context)

    def _validate_remote_mac_entry(self, context, rme, gateway_device_id):
        gw_dev_db = self._get_gateway_device(context, gateway_device_id)
        for item in gw_dev_db.mac_table_list:
            if item['mac_address'] == rme['mac_address']:
                raise gateway_device.GatewayDeviceParamDuplicate(
                    param_name='mac_address',
                    param_value=rme['mac_address'])
            if item['vtep_address'] == rme['vtep_address']:
                raise gateway_device.GatewayDeviceParamDuplicate(
                    param_name='vtep_address',
                    param_value=rme['vtep_address'])

    def _validate_hw_vtep(self, gw_dev, context):
        if not gw_dev['management_ip'] or not gw_dev['management_port']:
            raise gateway_device.HwVtepTypeInvalid(type=gw_dev['type'])
        if self._get_hw_vtep_from_management_ip(
            context, gw_dev['management_ip']):
            raise gateway_device.GatewayDeviceParamDuplicate(
                param_name='management_ip',
                param_value=gw_dev['management_ip'])

    def _validate_resource_router_vtep(self, context, router_id):
        # Check specified router existance
        l3plugin = manager.NeutronManager.get_service_plugins().get(
            service_constants.L3_ROUTER_NAT)

        try:
            l3plugin.get_router(context, router_id)
        except l3.RouterNotFound:
            raise gateway_device.ResourceNotFound(resource_id=router_id)

        if self._get_gateway_device_from_router(context, router_id):
            raise gateway_device.DeviceInUseByGatewayDevice(
                resource_id=router_id)

    def _validate_router_vtep(self, gw_dev, context):
        if not gw_dev['resource_id']:
            raise gateway_device.RouterVtepTypeInvalid(type=gw_dev['type'])
        self._validate_resource_router_vtep(context,
                                            gw_dev['resource_id'])

    def _validate_tunnel_ips(self, tunnel_ips):
        if len(tunnel_ips) > 1:
            raise gateway_device.TunnelIPsExhausted()

    def create_gateway_device(self, context, gw_device):
        """Create a gateway device"""
        gw_dev = gw_device['gateway_device']
        tenant_id = self._get_tenant_id_for_create(context, gw_dev)
        self._validate_gateway_device(context, gw_dev)
        self._validate_tunnel_ips(gw_dev.get('tunnel_ips') or [])

        with context.session.begin(subtransactions=True):
            gw_dev_db = GatewayDevice(id=uuidutils.generate_uuid(),
                name=gw_dev['name'],
                type=(gw_dev['type'] or gateway_device.HW_VTEP_TYPE),
                tenant_id=tenant_id)
            context.session.add(gw_dev_db)
            if gw_dev_db['type'] == gateway_device.HW_VTEP_TYPE:
                gw_hw_vtep_db = GatewayHwVtepDevice(
                    device_id=gw_dev_db['id'],
                    management_ip=gw_dev['management_ip'],
                    management_port=gw_dev['management_port'],
                    management_protocol=(
                        gw_dev['management_protocol'] or gateway_device.OVSDB))
                context.session.add(gw_hw_vtep_db)

            if gw_dev_db['type'] == gateway_device.ROUTER_DEVICE_TYPE:
                gw_router_db = GatewayOverlayRouterDevice(
                    device_id=gw_dev_db['id'],
                    resource_id=gw_dev['resource_id'])
                context.session.add(gw_router_db)

            if gw_dev.get('tunnel_ips'):
                self._tunnel_ip_db_add(context,
                                       gw_dev_db['id'], gw_dev['tunnel_ips'])

        return self._make_gateway_device_dict(gw_dev_db)

    def create_gateway_device_remote_mac_entry(self, context,
                                               remote_mac_entry,
                                               gateway_device_id):
        rme = remote_mac_entry['remote_mac_entry']
        self._validate_remote_mac_entry(context, rme, gateway_device_id)

        with context.session.begin(subtransactions=True):
            gw_rmt_db = GatewayRemoteMacTable(
                id=uuidutils.generate_uuid(),
                device_id=gateway_device_id,
                mac_address=rme['mac_address'],
                segmentation_id=rme['segmentation_id'],
                vtep_address=rme['vtep_address'])
            context.session.add(gw_rmt_db)

        return self._make_remote_mac_dict(gw_rmt_db)

    def delete_gateway_device(self, context, id):
        gw_dev = self._ensure_gateway_device_not_in_use(context, id)
        with context.session.begin(subtransactions=True):
            context.session.delete(gw_dev)

    def delete_gateway_device_remote_mac_entry(self, context, id,
                                               gateway_device_id):
        rmt_db = self._get_remote_mac_entry(context, id)
        with context.session.begin(subtransactions=True):
            context.session.delete(rmt_db)

    def get_gateway_device(self, context, id, fields=None):
        gw_dev = self._get_gateway_device(context, id)
        return self._make_gateway_device_dict(gw_dev, fields)

    def get_gateway_devices(self, context, filters=None, fields=None,
                            sorts=None, limit=None, marker=None,
                            page_reverse=False):
        marker_obj = self._get_marker_obj(context, 'gateway_device', limit,
                                          marker)

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
        marker_obj = self._get_marker_obj(context, 'remote_mac_entry', limit,
                                          marker)
        return self._get_collection(context,
                                    GatewayRemoteMacTable,
                                    self._make_remote_mac_dict,
                                    filters=filters, fields=fields,
                                    sorts=sorts,
                                    limit=limit, marker_obj=marker_obj,
                                    page_reverse=page_reverse)

    def get_gateway_device_remote_mac_entry(self, context, id,
                                            gateway_device_id, fields=None):
        rme = self._get_remote_mac_entry(context, id)
        return self._make_remote_mac_dict(rme, fields)

    def update_gateway_device(self, context, id, gw_device):
        gw_dev = gw_device['gateway_device']
        self._validate_tunnel_ips(gw_dev.get('tunnel_ips') or [])
        gw_dev_db = self._update_gateway_device_db(context, id, gw_dev)
        return self._make_gateway_device_dict(gw_dev_db)


def gateway_device_callback(resource, event, trigger, **kwargs):
    router_id = kwargs['router_id']
    gw_dev_plugin = manager.NeutronManager.get_service_plugins().get(
        midonet_const.GATEWAY_DEVICE)
    if gw_dev_plugin:
        context = kwargs.get('context')
        if gw_dev_plugin._get_gateway_device_from_router(context,
                                                         router_id):
            raise gateway_device.DeviceInUseByGatewayDevice(
                resource_id=router_id)


def subscribe():
    registry.subscribe(
        gateway_device_callback, resources.ROUTER, events.BEFORE_DELETE)
