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

from networking_l2gw.db.l2gateway import l2gateway_db


class MidonetL2GatewayMixin(l2gateway_db.L2GatewayMixin):
    # Override L2GatewayMixin to customize for Midonet L2GW

    def _validate_any_seg_id_empty_in_interface_dict(self, devices):
        # HACK: Override this since this validation method is not
        # applicable in MidoNet.
        pass

    def create_l2_gateway(self, context, l2_gateway):
        # HACK: set the device_name to device_id so that the networking-l2gw
        # DB class does not throw an error.
        gw = l2_gateway[self.gateway_resource]
        for device in gw['devices']:
            device['device_name'] = device['device_id']
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
                del device['device_name']
                del device['id']
                del device['interfaces']
        return l2gw

    def update_l2_gateway(self, context, id, l2_gateway):
        raise NotImplementedError()
