# Copyright (c) 2016 Midokura SARL
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

import netaddr
import testtools

from tempest.common import utils
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
import tempest.lib.exceptions as lib_exc

from neutron_tempest_plugin.api import base


class ExpectedException(testtools.ExpectedException):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if super(ExpectedException, self).__exit__(exc_type, exc_value, tb):
            self.exception = exc_value
            return True
        return False


class RouterInterfaceFip(base.BaseAdminNetworkTest):
    @classmethod
    @utils.requires_ext(extension="router-interface-fip", service="network")
    def resource_setup(cls):
        super(RouterInterfaceFip, cls).resource_setup()

    @decorators.idempotent_id('943ab44d-0ea7-4c6a-bdfd-8ba759622992')
    def test_router_interface_fip(self):
        # +-------------+
        # | router1     |
        # +-+--------+--+
        #   |        |
        # +-+--+   +-+--------+
        # |net1|   |net2      |
        # |    |   |(external)|
        # +-+--+   +--+-------+
        #   |         |
        #  port1     fip2
        cidr1 = netaddr.IPNetwork('192.2.1.0/24')
        cidr2 = netaddr.IPNetwork('192.2.2.0/24')
        router1_name = data_utils.rand_name('router1')
        router1 = self.create_router(router1_name)
        net1 = self.create_network()
        subnet1 = self.create_subnet(net1, cidr=cidr1)
        self.create_router_interface(router1['id'], subnet1['id'])
        net2 = self.admin_client.create_network(
            project_id=self.client.tenant_id,
            **{'router:external': True})['network']
        self.networks.append(net2)
        subnet2 = self.create_subnet(net2, cidr=cidr2)
        self.create_router_interface(router1['id'], subnet2['id'])
        port1 = self.create_port(net1)
        fip2 = self.create_floatingip(net2['id'])
        fip2_updated = self.client.update_floatingip(
            fip2['id'], port_id=port1['id'])['floatingip']
        expected = {
            'floating_network_id': net2['id'],
            'port_id': port1['id'],
            'router_id': router1['id'],
        }
        for k, v in expected.items():
            self.assertIn(k, fip2_updated)
            self.assertEqual(v, fip2_updated[k])
        if 'revision_number' in fip2:
            self.assertGreater(fip2_updated['revision_number'],
                               fip2['revision_number'])
        # NOTE(yamamoto): The status can be updated asynchronously.
        fip2_shown = self.client.show_floatingip(fip2['id'])['floatingip']
        if 'revision_number' in fip2:
            self.assertGreaterEqual(fip2_shown['revision_number'],
                                    fip2_updated['revision_number'])
        fip2_shown.pop('status')
        fip2_shown.pop('updated_at')
        fip2_shown.pop('revision_number')
        fip2_updated.pop('status')
        fip2_updated.pop('updated_at')
        fip2_updated.pop('revision_number')
        self.assertEqual(fip2_updated, fip2_shown)
        with ExpectedException(lib_exc.Conflict) as ctx:
            self.client.remove_router_interface_with_subnet_id(
                router1['id'], subnet2['id'])
        self.assertEqual('RouterInterfaceInUseAsGatewayByFloatingIP',
                         ctx.exception.resp_body['type'])
        with ExpectedException(lib_exc.Conflict) as ctx:
            self.client.remove_router_interface_with_subnet_id(
                router1['id'], subnet1['id'])
        self.assertEqual('RouterInterfaceInUseByFloatingIP',
                         ctx.exception.resp_body['type'])
        fip2_updated2 = self.client.update_floatingip(
            fip2['id'], port_id=None)['floatingip']
        expected = {
            'floating_network_id': net2['id'],
            'floating_ip_address': fip2_shown['floating_ip_address'],
            'port_id': None,
            'router_id': None,
        }
        for k, v in expected.items():
            self.assertIn(k, fip2_updated2)
            self.assertEqual(v, fip2_updated2[k])
        self.client.remove_router_interface_with_subnet_id(
            router1['id'], subnet2['id'])
        self.client.remove_router_interface_with_subnet_id(
            router1['id'], subnet1['id'])
