# Copyright (c) 2017 Midokura SARL
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
from tempest.lib.common import ssh
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

from neutron_tempest_plugin import config
from neutron_tempest_plugin.scenario import base
from neutron_tempest_plugin.scenario import constants

try:
    from neutron_dynamic_routing.tests.tempest import bgp_client
except ImportError:
    bgp_client = None


CONF = config.CONF


class BgpClientMixin(object):
    @classmethod
    def resource_setup(cls):
        super(BgpClientMixin, cls).resource_setup()
        if bgp_client is None:
            msg = "No BGP service client is available"
            raise cls.skipException(msg)
        manager = cls.os_admin
        cls.bgp_client = bgp_client.BgpSpeakerClientJSON(
            manager.auth_provider,
            CONF.network.catalog_type,
            CONF.network.region or CONF.identity.region,
            endpoint_type=CONF.network.endpoint_type,
            build_interval=CONF.network.build_interval,
            build_timeout=CONF.network.build_timeout,
            **manager.default_params)

    def create_bgp_speaker(self, **kwargs):
        bgp_speaker = self.bgp_client.create_bgp_speaker(post_data={
            'bgp_speaker': kwargs,
        })['bgp_speaker']
        self.addCleanup(self.bgp_client.delete_bgp_speaker, bgp_speaker['id'])
        return bgp_speaker

    def create_bgp_peer(self, **kwargs):
        bgp_peer = self.bgp_client.create_bgp_peer(post_data={
            'bgp_peer': kwargs,
        })['bgp_peer']
        self.addCleanup(self.bgp_client.delete_bgp_peer, bgp_peer['id'])
        return bgp_peer

    def add_bgp_peer_with_id(self, bgp_speaker_id, bgp_peer_id):
        self.bgp_client.add_bgp_peer_with_id(bgp_speaker_id, bgp_peer_id)


class Bgp(BgpClientMixin, base.BaseTempestTestCase):
    """Test the following topology

          +-------------------+
          | public            |
          | network           |
          |                   |
          +-+---------------+-+
            |               |
            |               |
    +-------+-+           +-+-------+
    | LEFT    |           | RIGHT   |
    | router  | <--BGP--> | router  |
    |         |           |         |
    +----+----+           +----+----+
         |                     |
    +----+----+           +----+----+
    | LEFT    |           | RIGHT   |
    | network |           | network |
    |         |           |         |
    +---------+           +---------+
    """

    credentials = ['primary', 'admin']

    @classmethod
    @utils.requires_ext(extension="bgp-speaker-router-insertion",
                        service="network")
    def resource_setup(cls):
        super(Bgp, cls).resource_setup()

        # common
        cls.keypair = cls.create_keypair()
        cls.secgroup = cls.os_primary.network_client.create_security_group(
            name=data_utils.rand_name('secgroup-'))['security_group']
        cls.security_groups.append(cls.secgroup)
        cls.create_loginable_secgroup_rule(secgroup_id=cls.secgroup['id'])
        cls.create_pingable_secgroup_rule(secgroup_id=cls.secgroup['id'])

        # LEFT
        cls.router = cls.create_router(
            data_utils.rand_name('left-router'),
            admin_state_up=True,
            external_network_id=CONF.network.public_network_id)
        cls.network = cls.create_network(network_name='left-network')
        cls.subnet = cls.create_subnet(cls.network,
                                       name='left-subnet')
        cls.create_router_interface(cls.router['id'], cls.subnet['id'])

        # RIGHT
        cls._right_network, cls._right_subnet, cls._right_router = \
            cls._create_right_network()

    @classmethod
    def _create_right_network(cls):
        # NOTE(yamamoto): Disable SNAT to workaround a bug
        # https://midonet.atlassian.net/browse/MNA-1114
        router = cls.create_admin_router(
            data_utils.rand_name('right-router'),
            admin_state_up=True,
            external_network_id=CONF.network.public_network_id,
            enable_snat=False,
            project_id=cls.os_primary.network_client.tenant_id)
        network = cls.create_network(network_name='right-network')
        subnet = cls.create_subnet(
            network,
            cidr=netaddr.IPNetwork('10.10.0.0/24'),
            name='right-subnet')
        cls.create_router_interface(router['id'], subnet['id'])
        return network, subnet, router

    def _create_server(self, create_floating_ip=True, network=None):
        if network is None:
            network = self.network
        port = self.create_port(network, security_groups=[self.secgroup['id']])
        if create_floating_ip:
            fip = self.create_and_associate_floatingip(port['id'])
        else:
            fip = None
        server = self.create_server(
            flavor_ref=CONF.compute.flavor_ref,
            image_ref=CONF.compute.image_ref,
            key_name=self.keypair['name'],
            networks=[{'port': port['id']}])['server']
        waiters.wait_for_server_status(self.os_primary.servers_client,
                                       server['id'],
                                       constants.SERVER_STATUS_ACTIVE)
        return {'port': port, 'fip': fip, 'server': server}

    def _find_ipv4_subnet(self, network_id):
        subnets = self.os_admin.network_client.list_subnets(
            network_id=network_id)['subnets']
        for subnet in subnets:
            if subnet['ip_version'] == 4:
                return subnet['id']
        msg = "No suitable subnets on public network"
        raise self.skipException(msg)

    def _get_external_ip(self, router, subnet_id):
        for ip in router['external_gateway_info']['external_fixed_ips']:
            if ip['subnet_id'] == subnet_id:
                return ip['ip_address']

    def _setup_bgp(self):
        network_id = CONF.network.public_network_id
        subnet_id = self._find_ipv4_subnet(network_id)
        sites = [
            dict(name="left", network=self.network, subnet=self.subnet,
                 router=self.router, local_as=64512),
            dict(name="right", network=self._right_network,
                 subnet=self._right_subnet, router=self._right_router,
                 local_as=64513),
        ]
        psk = data_utils.rand_name('mysecret')
        for i in range(0, 2):
            site = sites[i]
            router = site['router']
            site['bgp_speaker'] = self.create_bgp_speaker(
                name=data_utils.rand_name('%s-bgp-speaker' % site['name']),
                local_as=site['local_as'],
                ip_version=4,
                logical_router=router['id'])
            site['external_v4_ip'] = self._get_external_ip(router, subnet_id)
        for i in range(0, 2):
            site = sites[i]
            bgp_speaker_id = site['bgp_speaker']['id']
            peer = sites[1 - i]
            peer_ip = peer['external_v4_ip']
            peer_as = peer['local_as']
            bgp_peer = self.create_bgp_peer(
                name=data_utils.rand_name('%s-bgp-peer' % site['name']),
                peer_ip=peer_ip,
                remote_as=peer_as,
                auth_type='md5',
                password=psk)
            self.add_bgp_peer_with_id(bgp_speaker_id, bgp_peer['id'])

    @decorators.idempotent_id('c1208ce2-c55f-4424-9035-25de83161d6f')
    def test_bgp(self):
        # RIGHT
        right_server = self._create_server(
            network=self._right_network,
            create_floating_ip=False)

        # LEFT
        left_server = self._create_server()
        ssh_client = ssh.Client(left_server['fip']['floating_ip_address'],
                                CONF.validation.image_ssh_user,
                                pkey=self.keypair['private_key'])

        # check LEFT -> RIGHT connectivity via BGP advertised routes
        self.check_remote_connectivity(
            ssh_client,
            right_server['port']['fixed_ips'][0]['ip_address'],
            should_succeed=False)
        self._setup_bgp()
        self.check_remote_connectivity(
            ssh_client,
            right_server['port']['fixed_ips'][0]['ip_address'])
