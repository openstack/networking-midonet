#! /usr/bin/env bash

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

# NOTE(yamamoto): This script is intended to consume the same set of
# environment variables as devmido/mido.sh so that it can be used as
# a drop-in replacement.

set -x
set -e

source $TOP_DIR/functions

## defaults

# IP address/hostname to use for the services
SERVICE_HOST=${SERVICE_HOST:-127.0.0.1}

# ZK Hosts (comma delimited)
ZOOKEEPER_HOSTS=${ZOOKEEPER_HOSTS:-${SERVICE_HOST}:2181}

# Cassandra Host
CASSANDRA_HOST=${CASSANDRA_HOST:-${SERVICE_HOST}}

# MidoNet API port and URI
API_PORT=${API_PORT:-8181}
API_URI=http://$SERVICE_HOST:$API_PORT/midonet-api

# Time (in sec) to wait for the API to start
API_TIMEOUT=${API_TIMEOUT:-120}

# DB connection string for the tasks importer
ENABLE_TASKS_IMPORTER=${ENABLE_TASKS_IMPORTER:-False}
MIDO_DB_USER=${MIDO_DB_USER:-root}
MIDO_DB_PASSWORD=${MIDO_DB_PASSWORD:-$MIDO_PASSWORD}
TASKS_DB_CONN=${TASKS_DB_CONN:-jdbc:mysql://localhost:3306/neutron?user=$MIDO_DB_USER&password=$MIDO_DB_PASSWORD}
TASKS_DB_DRIVER_CLASS=${TASKS_DB_DRIVER_CLASS:-org.mariadb.jdbc.Driver}

# Auth variables. They are exported so that you could source this file and
# run midonet-cli using these credentials
export MIDO_API_URL=$API_URI
export MIDO_USER=${MIDO_USER:-admin}
export MIDO_PROJECT_ID=${MIDO_PROJECT_ID:-admin}
export MIDO_PASSWORD=${MIDO_PASSWORD:-midonet}

## Stop services

for x in midolman midonet-cluster zookeeper cassandra; do
    stop_service $x || :
done

## Zookeeper

sudo rm -rf /var/lib/zookeeper/*
restart_service zookeeper

## Cassandra

if [ "${MIDONET_USE_CASSANDRA}" = True ]; then
    sudo chown cassandra:cassandra /var/lib/cassandra
    sudo rm -rf /var/lib/cassandra/data/system/LocationInfo
    CASSANDRA_FILE='/etc/cassandra/cassandra.yaml'
    sudo sed -i -e "s/^cluster_name:.*$/cluster_name: \'midonet\'/g" $CASSANDRA_FILE
    CASSANDRA_ENV_FILE='/etc/cassandra/cassandra-env.sh'
    sudo sed -i 's/\(MAX_HEAP_SIZE=\).*$/\1128M/' $CASSANDRA_ENV_FILE
    sudo sed -i 's/\(HEAP_NEWSIZE=\).*$/\164M/' $CASSANDRA_ENV_FILE
    # Cassandra seems to need at least 228k stack working with Java 7.
    # Related bug: https://issues.apache.org/jira/browse/CASSANDRA-5895
    sudo sed -i -e "s/-Xss180k/-Xss228k/g" $CASSANDRA_ENV_FILE
    sudo rm -rf /var/lib/cassandra/*
    restart_service cassandra
fi

## MidoNet

# Wrapper for mn-conf command
# Uses globals ``ZOOKEEPER_HOSTS``
function configure_mn {
    local value="$2"

    # quote with "" only when necessary.  we don't always quote because
    # mn-conf complains for quoted booleans.  eg. "false"
    if [[ "${value}" =~ ":" || "${value}" = "" ]]; then
        value="\"${value}\""
    fi

    # In some commands, mn-conf creates a local file, which requires root
    # access.  For simplicity, always call mn-conf with root for now.
    echo $1 : "${value}" | MIDO_ZOOKEEPER_HOSTS="$ZOOKEEPER_HOSTS" sudo -E mn-conf set
}

# midonet-cluster

configure_mn "cluster.loggers.root" "DEBUG"
configure_mn "cluster.rest_api.http_port" $API_PORT
configure_mn "cluster.state_proxy.server.address" $SERVICE_HOST
configure_mn "cluster.endpoint.enabled" "true"
configure_mn "cluster.endpoint.service.host" $SERVICE_HOST
configure_mn "cluster.endpoint.auth.ssl.enabled" "false"
# NOTE(yamamoto): The following configurations are commented out
# because we don't have users of the topology api right now.
# (The "agent" extension is the only user.  but it's incomplete.)
# configure_mn "cluster.topology_api.enabled" "true"
# configure_mn "cluster.topology_api.port" $TOPOLOGY_API_PORT
# configure_mn "cluster.topology_api.socket_enabled" "true"

if [[ "$ENABLE_TASKS_IMPORTER" = "True" ]]; then
    configure_mn "cluster.neutron_importer.enabled" "true"
    configure_mn "cluster.neutron_importer.connection_string" "\"$TASKS_DB_CONN\""
    configure_mn "cluster.neutron_importer.jdbc_driver_class" "\"$TASKS_DB_DRIVER_CLASS\""
fi
if [ "$MIDONET_USE_KEYSTONE" = "True" ]; then
    configure_mn "cluster.auth.keystone.admin_token" ""
    configure_mn "cluster.auth.keystone.url" "$KEYSTONE_AUTH_URI_V3"
    configure_mn "cluster.auth.keystone.domain_name" "default"
    configure_mn "cluster.auth.keystone.tenant_name" "$SERVICE_PROJECT_NAME"
    configure_mn "cluster.auth.keystone.user_name" "midonet"
    configure_mn "cluster.auth.keystone.user_password" "$SERVICE_PASSWORD"
    configure_mn "cluster.auth.keystone.version" "3"
    configure_mn "cluster.auth.admin_role" "midonet-admin"
    configure_mn "cluster.auth.provider_class" "org.midonet.cluster.auth.keystone.KeystoneService"
fi

MIDOENT_CLUSTER_ENV_FILE='/etc/midonet-cluster/midonet-cluster-env.sh'
sudo sed -i 's/\(MAX_HEAP_SIZE=\).*$/\1256M/' $MIDOENT_CLUSTER_ENV_FILE
sudo sed -i 's/\(HEAP_NEWSIZE=\).*$/\1128M/' $MIDOENT_CLUSTER_ENV_FILE

restart_service midonet-cluster

if ! timeout $API_TIMEOUT sh -c 'while ! midonet-cli -e host list; do sleep 1; done'; then
    die $LINENO "API server didn't start in $API_TIMEOUT seconds"
fi

# midolman

sudo mkdir -p /etc/midolman
sudo tee /etc/midolman/midolman.conf <<EOF
[zookeeper]
zookeeper_hosts = ${ZOOKEEPER_HOSTS}
EOF

if [[ "$USE_METADATA" = "True" ]]; then
    configure_mn "agent.openstack.metadata.enabled" "true"
    configure_mn "agent.openstack.metadata.nova_metadata_url" \
        "$NOVA_METADATA_URL"
    configure_mn "agent.openstack.metadata.shared_secret" \
        "$METADATA_SHARED_SECRET"
fi

configure_mn "agent.loggers.root" "DEBUG"
configure_mn "agent.midolman.lock_memory" "false"
configure_mn "cassandra.servers" "${CASSANDRA_HOST}"

MIDOLMAN_ENV_FILE='/etc/midolman/midolman-env.sh'
sudo sed -i 's/\(MAX_HEAP_SIZE=\).*$/\1256M/' $MIDOLMAN_ENV_FILE
MINIONS_ENV_FILE='/etc/midolman/minions-env.sh'
sudo sed -i 's/\(MAX_HEAP_SIZE=\).*$/\1128M/' $MINIONS_ENV_FILE

restart_service midolman

HOST_ID=${HOST_ID:-$(hostname)}
export HOST_ID
if ! timeout 60 sh -c 'while test -z "$(midonet-cli -e host list | awk \$4\ \=\=\ \"${HOST_ID}\")"; do sleep 1; done'; then
    die $LINENO "HostService didn't register the host"
fi
