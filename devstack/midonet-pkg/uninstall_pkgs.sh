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

# While cassandra needs a jre during uninstall, it seems lacking
# proper dependencies.  Explicitly list it to ensure that it's
# removed before jre.
apt-get purge -y \
    zookeeperd \
    dsc22 \
    cassandra \
    midonet-tools \
    midonet-cluster \
    midolman \
    python-midonetclient

# Remove ca-certificates-java as well.
# Otherwise apt-get installs openjdk-7 as an alternative.
apt-get purge -y \
    openjdk-8-jre-headless \
    ca-certificates-java

apt-get autoremove -y --purge
