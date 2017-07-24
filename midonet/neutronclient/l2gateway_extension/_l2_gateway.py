# Copyright (C) 2016 Midokura SARL
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
#

from neutron_lib.utils import helpers

from networking_l2gw.l2gatewayclient.l2gw_client_ext import _l2_gateway
from neutronclient.common import extension

from midonet.neutron._i18n import _


def add_known_arguments(self, parser):
    parser.add_argument(
        '--device',
        metavar='device_id=DEVICE_ID,segmentaion_id=SEGMENTAION_ID',
        action='append', dest='devices', type=helpers.str2dict,
        help=_('Device id and segmentation id of l2gateway. '
               '--device option can be repeated'))


def args2body(self, parsed_args):
        if parsed_args.devices:
            devices = parsed_args.devices
        else:
            devices = []
        body = {'l2_gateway': {'devices': devices}}
        if parsed_args.name:
            l2gw_name = parsed_args.name
            body['l2_gateway']['name'] = l2gw_name
        return body


class L2Gateway(_l2_gateway.L2Gateway):
    """L2Gateway resource class

    This class loads parameters for L2Gateway.
    """

    pass


class L2GatewayCreate(extension.ClientExtensionCreate, L2Gateway):
    """Create l2gateway information for midonet."""

    shell_command = 'midonet-l2-gateway-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='GATEWAY-NAME',
            help=_('Descriptive name for logical gateway.'))
        add_known_arguments(self, parser)

    def args2body(self, parsed_args):
        body = args2body(self, parsed_args)
        if parsed_args.tenant_id:
            body['l2_gateway']['tenant_id'] = parsed_args.tenant_id
        return body
