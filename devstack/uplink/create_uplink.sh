#! /bin/bash

# Copyright 2016 Midokura SARL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Physical topology
#
#  +---------------+
#  | host tcp/ip   |
#  +----+----------+
#       |mn-uplink-host
#       |
#       |(veth pair)
#       |
#       |mn-uplink-virt
#  +----+----------+
#  | datapath      |
#  +---------------+

# Virtual topology
#
#  +---------------+
#  | mn-uplink-net |
#  +----+----------+
#       |mn-uplink-port
#       |
#       |(router interface, bound to mn-uplink-virt)
#     mn-edge
#       |(router interface)
#       |
#  +----+----------+
#  |    public     |
#  +----+----------+
#       |
#       |(router gateway port)
#     router1
#       |(router interface)
#       |
#  +----+----------+
#  |    private    |
#  +---------------+

# https://docs.midonet.org/docs/latest/quick-start-guide/ubuntu-1404_kilo/content/edge_router_setup.html

source $TOP_DIR/stackrc
source $TOP_DIR/functions

HOST_ID=${HOST_ID:-$(hostname)}
PUBLIC_SUBNET_NAME=${PUBLIC_SUBNET_NAME:-"public-subnet"}
EDGE_ROUTER_NAME=${EDGE_ROUTER_NAME:-"mn-edge"}

# Neutron net/subnet/port for uplink
UPLINK_NET_NAME=${UPLINK_NET_NAME:-"mn-uplink-net"}
UPLINK_SUBNET_NAME=${UPLINK_SUBNET_NAME:-"mn-uplink-subnet"}
UPLINK_SUBNET_NAME6=${UPLINK_SUBNET_NAME6:-"mn-uplink-subnet6"}
UPLINK_PORT_NAME=${UPLINK_PORT_NAME:-"mn-uplink-port"}
# Veth pair
UPLINK_VIRT_IFNAME=${UPLINK_VIRT_IFNAME:-"mn-uplink-virt"}
UPLINK_HOST_IFNAME=${UPLINK_HOST_IFNAME:-"mn-uplink-host"}
# NOTE(yamamoto): These addresses are taken from create_fake_uplink.sh
UPLINK_CIDR=${UPLINK_CIDR:-"172.19.0.0/30"}
UPLINK_PREFIX_LEN=${UPLINK_PREFIX_LEN:-"30"}
UPLINK_VIRT_IP=${UPLINK_VIRT_IP:-"172.19.0.1"}
UPLINK_HOST_IP=${UPLINK_HOST_IP:-"172.19.0.2"}
UPLINK_CIDR6=${UPLINK_CIDR6:-"fd1a:6fd3:0a22::/48"}
UPLINK_PREFIX_LEN6=${UPLINK_PREFIX_LEN6:-"48"}
UPLINK_VIRT_IP6=${UPLINK_VIRT_IP6:-"fd1a:6fd3:0a22::1"}
UPLINK_HOST_IP6=${UPLINK_HOST_IP6:-"fd1a:6fd3:0a22::2"}

sudo ip link add name ${UPLINK_HOST_IFNAME} type veth \
    peer name ${UPLINK_VIRT_IFNAME}
for name in ${UPLINK_HOST_IFNAME} ${UPLINK_VIRT_IFNAME}; do
    sudo ip addr flush ${name}
    sudo ip link set dev ${name} up
done

# NOTE(yamamoto): MidoNet fip64 implementation seems
# incompatible with the checksum "offloading"
install_package ethtool
sudo ethtool -K ${UPLINK_HOST_IFNAME} tx-checksum-ip-generic off

# Configure edge router and uplink network
openstack --os-project-name admin \
    router create \
    ${EDGE_ROUTER_NAME}
openstack --os-project-name admin \
    router add subnet \
    ${EDGE_ROUTER_NAME} ${PUBLIC_SUBNET_NAME}
openstack --os-project-name admin \
    network create \
    --provider-network-type uplink \
    ${UPLINK_NET_NAME}
openstack --os-project-name admin \
    subnet create \
    --no-dhcp \
    --network ${UPLINK_NET_NAME} \
    --subnet-range ${UPLINK_CIDR} \
    ${UPLINK_SUBNET_NAME}
openstack --os-project-name admin \
    subnet create \
    --ip-version 6 --no-dhcp \
    --network ${UPLINK_NET_NAME} \
    --subnet-range ${UPLINK_CIDR6} \
    ${UPLINK_SUBNET_NAME6}
openstack --os-project-name admin \
    port create \
    --network ${UPLINK_NET_NAME} \
    --host ${HOST_ID} \
    --binding-profile interface_name=${UPLINK_VIRT_IFNAME} \
    --fixed-ip ip-address=${UPLINK_VIRT_IP} \
    --fixed-ip ip-address=${UPLINK_VIRT_IP6} \
    ${UPLINK_PORT_NAME}
openstack --os-project-name admin \
    router add port \
    ${EDGE_ROUTER_NAME} ${UPLINK_PORT_NAME}
openstack --os-project-name admin \
    router set \
    --route destination=0.0.0.0/0,gateway=${UPLINK_HOST_IP} \
    ${EDGE_ROUTER_NAME}

# Configure host side
sudo ip addr add ${UPLINK_HOST_IP}/${UPLINK_PREFIX_LEN} \
    dev ${UPLINK_HOST_IFNAME}
sudo ip route replace ${FLOATING_RANGE} via ${UPLINK_VIRT_IP}
sudo ip route replace ${FIXED_RANGE} via ${UPLINK_VIRT_IP}

sudo ip addr add ${UPLINK_HOST_IP6}/${UPLINK_PREFIX_LEN6} \
    dev ${UPLINK_HOST_IFNAME}
sudo ip route replace ${IPV6_PUBLIC_RANGE} via ${UPLINK_VIRT_IP6}
