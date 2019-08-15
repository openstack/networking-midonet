#! /bin/sh

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

# https://docs.midonet.org/docs/latest-en/quick-start-guide/ubuntu-1604_mitaka/content/_repository_configuration.html

MIDONET_DEB_URI=$1
MIDONET_DEB_SUITE=$2
MIDONET_DEB_COMPONENT=$3
MIDONET_USE_CASSANDRA=$4

# Configure DataStax repository

if [ "${MIDONET_USE_CASSANDRA}" = True ]; then
    cat > /etc/apt/sources.list.d/datastax.list <<EOL
# DataStax (Apache Cassandra)
deb http://debian.datastax.com/community 2.2 main
EOL

    curl -L https://debian.datastax.com/debian/repo_key | apt-key add -
fi

# Configure MidoNet repositories

cat > /etc/apt/sources.list.d/midonet.list <<EOL
# MidoNet
deb $MIDONET_DEB_URI $MIDONET_DEB_SUITE $MIDONET_DEB_COMPONENT

# MidoNet 3rd Party Tools and Libraries
deb http://builds.midonet.org/misc stable main
EOL

curl -L https://builds.midonet.org/midorepo.key | apt-key add -

apt-get update
