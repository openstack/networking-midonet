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

# https://docs.midonet.org/docs/latest-en/quick-start-guide/rhel-7_newton-rdo/content/_midolman_installation.html

MIDONET_USE_CASSANDRA=$1
PYTHON_PREFIX=$2

# Remove possible reminders from the previous devmido runs
rm -rf \
    /usr/local/bin/mn-conf \
    /usr/local/bin/mm-ctl \
    /usr/local/bin/mm-dpctl \
    /usr/local/bin/mm-meter \
    /usr/local/bin/mm-trace

yum -y install java-1.8.0-openjdk-headless

if [ "${MIDONET_USE_CASSANDRA}" = True ]; then
    CASSANDRA_PKG=dsc22
else
    CASSANDRA_PKG=
fi

yum -y install \
    zookeeper \
    ${CASSANDRA_PKG} \
    midonet-tools \
    midonet-cluster \
    midolman \
    ${PYTHON_PREFIX}midonetclient
