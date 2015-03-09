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

import logging
from midonet.neutron.common import exceptions as mexc
from midonetclient import topology  # noqa
from midonetclient.topology import hosts


import socket
import uuid


LOG = logging.getLogger(__name__)


MIDO_AGENT_NAME = 'Midonet Agent'
MIDO_BINARY = 'midolman'


def midonet_host_to_neutron_agent(host):
    return {'admin_state_up': True,
            'agent_type': MIDO_AGENT_NAME,
            'alive': True,
            'binary': MIDO_BINARY,
            'configurations': {},
            'host': None,
            'id': host.get('id')}


def invoke_cluster_rpc(cluster_ip, cluster_port, call):
    try:
        sock = socket.create_connection((cluster_ip, cluster_port))
        req_uuid = uuid.uuid4()
        topology.handshake(sock, uuid.uuid4(), req_uuid)
        ret = list(call(sock))
        topology.bye(sock, req_uuid)
        return ret
    except socket.error:
        raise mexc.ClusterConnectionError()


def get_all_midonet_hosts(cluster_ip, cluster_port):
    return invoke_cluster_rpc(cluster_ip, cluster_port, hosts.get_all_dict)
