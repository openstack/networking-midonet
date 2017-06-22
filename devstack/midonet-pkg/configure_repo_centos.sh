#! /bin/sh

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

# https://docs.midonet.org/docs/latest-en/quick-start-guide/rhel-7_newton-rdo/content/_repository_configuration.html

MIDONET_YUM_URI=$1
MIDONET_USE_CASSANDRA=$2

# Configure DataStax repository

if [ "${MIDONET_USE_CASSANDRA}" = True ]; then
    cat > /etc/yum.repos.d/datastax.repo  <<EOL
# DataStax (Apache Cassandra)
[datastax]
name = DataStax Repo for Apache Cassandra
baseurl = http://rpm.datastax.com/community
enabled = 1
gpgcheck = 1
gpgkey = https://rpm.datastax.com/rpm/repo_key
EOL
fi

# Configure MidoNet repositories

cat > /etc/yum.repos.d/midonet.repo <<EOL
[midonet]
name=MidoNet
baseurl=${MIDONET_YUM_URI}
enabled=1
gpgcheck=1
gpgkey=https://builds.midonet.org/midorepo.key

[midonet-misc]
name=MidoNet 3rd Party Tools and Libraries
baseurl=http://builds.midonet.org/misc/stable/el7/
enabled=1
gpgcheck=1
gpgkey=https://builds.midonet.org/midorepo.key
EOL
