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

from neutron_lib.plugins import directory

from networking_l2gw.db.l2gateway import l2gateway_db
from networking_l2gw.db.l2gateway import l2gateway_models as models
from networking_l2gw.services.l2gateway.common import constants
from networking_l2gw.services.l2gateway import exceptions as l2gw_exc
from neutron.api import extensions as neutron_extensions

from midonet.neutron.common import constants as midonet_const
from midonet.neutron.services.l2gateway.common import l2gw_midonet_validators
from midonet.neutron.services.l2gateway import exceptions


class MidonetL2GatewayMixin(l2gateway_db.L2GatewayMixin):
    # Override L2GatewayMixin to customize for Midonet L2GW

    def _check_and_get_gw_dev_service(self):
        gw_plugin = directory.get_plugin(midonet_const.GATEWAY_DEVICE)
        if not gw_plugin:
            raise exceptions.MidonetL2GatewayUnavailable()
        return gw_plugin

    def _validate_any_seg_id_empty_in_interface_dict(self, devices):
        # HACK: Override this since this validation method is not
        # applicable in MidoNet.
        pass

    def validate_l2_gateway_connection_for_create(self, context,
                                                  l2_gateway_connection):
        # HACK: Override this since segmentation id validation is not
        # applicable in Midonet. After deactivating segmentation id validation
        # of l2gw_validators.validate_network_mapping_list in plugin side,
        # validate it in this method.
        super(MidonetL2GatewayMixin,
              self).validate_l2_gateway_connection_for_create(
                  context, l2_gateway_connection)

        # Validate l2 gateway existence before getting gateway device type
        gw_connection = l2_gateway_connection[self.connection_resource]
        l2gw = self.get_l2_gateway(context, gw_connection['l2_gateway_id'])
        if not l2gw:
            raise l2gw_exc.L2GatewayNotFound(
                gateway_id=gw_connection['l2_gateway_id'])
        if self._get_l2_gateway_connection_by_l2gw_id(
                context, gw_connection['l2_gateway_id']):
            raise exceptions.MidonetL2GatewayConnectionExists(
                l2_gateway_id=gw_connection['l2_gateway_id'])

        # Validate segmentation id range according to gateway device type
        gw_connection = l2_gateway_connection[
            constants.CONNECTION_RESOURCE_NAME]
        seg_id = gw_connection.get(constants.SEG_ID)
        if seg_id:
            gw_type = self.get_gateway_device_type_from_l2gw(context, l2gw)
            l2gw_midonet_validators.is_valid_segmentaion_id(gw_type, seg_id)

    def _get_l2_gateway_seg_id(self, context, l2_gw_id):
        seg_id = None
        l2_gw_dev = self.get_l2gateway_devices_by_gateway_id(
            context, l2_gw_id)
        interfaces = self.get_l2gateway_interfaces_by_device_id(
            context, l2_gw_dev[0]['id'])
        if interfaces:
            seg_id = interfaces[0][constants.SEG_ID]
        return seg_id

    def _get_l2gw_devices_by_device_id(self, context, device_id):
        return context.session.query(models.L2GatewayDevice).filter_by(
            device_name=device_id).all()

    def get_gateway_device_type_from_l2gw(self, context, l2gw):
        gw_id = (l2gw['devices'][0].get('device_id')) or (
            l2gw['devices'][0].get('device_name'))
        gw_db = (directory.get_plugin(midonet_const.GATEWAY_DEVICE).
                 get_gateway_device(context, gw_id))
        return gw_db['type']

    def create_l2_gateway(self, context, l2_gateway):
        # HACK: set the device_name to device_id so that the networking-l2gw
        # DB class does not throw an error.
        gw = l2_gateway[self.gateway_resource]

        gw_plugin = self._check_and_get_gw_dev_service()
        for device in gw['devices']:
            gw = gw_plugin.get_gateway_device(context, device['device_id'])
            device['device_name'] = device['device_id']
            if device.get(constants.SEG_ID):
                l2gw_midonet_validators.is_valid_segmentaion_id(
                    gw['type'], device[constants.SEG_ID])
                device['interfaces'].append(
                    {constants.SEG_ID: [str(device[constants.SEG_ID])]})
        return super(MidonetL2GatewayMixin, self).create_l2_gateway(
            context, l2_gateway)

    def _make_l2_gateway_dict(self, l2_gateway, fields=None):
        l2gw = super(MidonetL2GatewayMixin, self)._make_l2_gateway_dict(
            l2_gateway, fields=fields)

        # HACK: change the 'device_name' to 'device_id' to match the API that
        # Midonet L2GW expects
        if 'devices' in l2gw:
            for device in l2gw['devices']:
                device['device_id'] = device['device_name']
                if device['interfaces']:
                    interface = device['interfaces'][0]
                    device[constants.SEG_ID] = interface[constants.SEG_ID][0]
                del device['device_name']
                del device['id']
                del device['interfaces']
        return l2gw

    def create_l2_gateway_connection(self, context, l2_gateway_connection):
        gw_connection = l2_gateway_connection[self.connection_resource]

        # Validate only network existence since l2_gateway existence is
        # validated in validate_l2_gateway_connection_for_create method.
        if not self._core_plugin.get_network(
                context, gw_connection['network_id']):
            raise neutron_extensions.NetworkNotFound(
                net_id=gw_connection['network_id'])
        return super(MidonetL2GatewayMixin, self).create_l2_gateway_connection(
            context, l2_gateway_connection)

    def update_l2_gateway(self, context, id, l2_gateway):
        raise NotImplementedError()
