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

source $TOP_DIR/stackrc
source $TOP_DIR/functions

HOST_ID=${HOST_ID:-$(hostname)}
PUBLIC_SUBNET_NAME=${PUBLIC_SUBNET_NAME:-"public-subnet"}
EDGE_ROUTER_NAME=${EDGE_ROUTER_NAME:-"mn-edge"}

# Neutron net/subnet/port for uplink
UPLINK_NET_NAME=${UPLINK_NET_NAME:-"mn-uplink-net"}
UPLINK_SUBNET_NAME=${UPLINK_SUBNET_NAME:-"mn-uplink-subnet"}
UPLINK_PORT_NAME=${UPLINK_PORT_NAME:-"mn-uplink-port"}
# Veth pair
UPLINK_VIRT_IFNAME=${UPLINK_VIRT_IFNAME:-"mn-uplink-virt"}
UPLINK_HOST_IFNAME=${UPLINK_HOST_IFNAME:-"mn-uplink-host"}

openstack --os-project-name admin \
    router remove port \
    ${EDGE_ROUTER_NAME} ${UPLINK_PORT_NAME}
openstack --os-project-name admin \
    network delete \
    ${UPLINK_NET_NAME}
openstack --os-project-name admin \
    router remove port \
    ${EDGE_ROUTER_NAME} ${PUBLIC_SUBNET_NAME}
openstack --os-project-name admin \
    router delete \
    ${EDGE_ROUTER_NAME}

sudo ip link delete ${UPLINK_HOST_IFNAME}
