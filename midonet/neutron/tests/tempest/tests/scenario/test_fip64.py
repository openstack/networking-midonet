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

from tempest.common import utils
from tempest.common import waiters
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

from neutron_tempest_plugin import config
from neutron_tempest_plugin.scenario import base
from neutron_tempest_plugin.scenario import constants


CONF = config.CONF


class Fip64(base.BaseTempestTestCase):
    credentials = ['primary', 'admin']

    _fip_ip_version = 6

    @classmethod
    @utils.requires_ext(extension="fip64", service="network")
    def resource_setup(cls):
        super(Fip64, cls).resource_setup()
        cls.network = cls.create_network()
        cls.subnet = cls.create_subnet(cls.network)
        router = cls.create_router_by_client()
        cls.create_router_interface(router['id'], cls.subnet['id'])
        cls.keypair = cls.create_keypair()

        cls.secgroup = cls.os_primary.network_client.create_security_group(
            name=data_utils.rand_name('secgroup-'))['security_group']
        cls.security_groups.append(cls.secgroup)
        cls.create_loginable_secgroup_rule(secgroup_id=cls.secgroup['id'])

    def _find_ipv6_subnet(self, network_id):
        subnets = self.os_admin.network_client.list_subnets(
            network_id=network_id)['subnets']
        for subnet in subnets:
            if subnet['ip_version'] == self._fip_ip_version:
                return subnet['id']
        msg = "No suitable subnets on public network"
        raise self.skipException(msg)

    def _create_and_associate_floatingip64(self, port_id):
        network_id = CONF.network.public_network_id
        subnet_id = self._find_ipv6_subnet(network_id)
        fip = self.os_primary.network_client.create_floatingip(
            floating_network_id=network_id,
            subnet_id=subnet_id,
            port_id=port_id)['floatingip']
        self.floating_ips.append(fip)
        self.assertEqual(
            self._fip_ip_version,
            netaddr.IPAddress(fip['floating_ip_address']).version)
        return fip

    def _create_server_with_fip64(self):
        port = self.create_port(self.network, security_groups=[
            self.secgroup['id']])
        fip = self._create_and_associate_floatingip64(port['id'])
        server = self.create_server(
            flavor_ref=CONF.compute.flavor_ref,
            image_ref=CONF.compute.image_ref,
            key_name=self.keypair['name'],
            networks=[{'port': port['id']}])['server']
        waiters.wait_for_server_status(self.os_primary.servers_client,
                                       server['id'],
                                       constants.SERVER_STATUS_ACTIVE)
        return {'port': port, 'fip': fip, 'server': server}

    @decorators.idempotent_id('63f7da91-c7dd-449b-b50b-1c56853ce0ef')
    def test_fip64(self):
        server = self._create_server_with_fip64()
        self.check_connectivity(server['fip']['floating_ip_address'],
                                CONF.validation.image_ssh_user,
                                self.keypair['private_key'])
