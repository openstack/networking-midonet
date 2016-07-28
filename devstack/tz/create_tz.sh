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

# https://docs.midonet.org/docs/latest/quick-start-guide/ubuntu-1404_kilo/content/_midonet_host_registration.html

source $TOP_DIR/stackrc
source $TOP_DIR/functions

MIDONET_TZ_NAME=${MIDONET_TZ_NAME:-DEFAULT}
MIDOLMAN_IP=${MIDOLMAN_IP:-$HOST_IP}
HOST_ID=${HOST_ID:-$(hostname)}

TZ=$(midonet-cli -e tunnel-zone list | awk "\$4 == \"${MIDONET_TZ_NAME}\" {print \$2}")
if [ -z "${TZ}" ]; then
    TZ=$(midonet-cli -e tunnel-zone create name ${MIDONET_TZ_NAME} type vxlan)
fi

HOST=$(midonet-cli -e host list | awk "\$4 == \"${HOST_ID}\" {print \$2}")

MATCH=$(midonet-cli -e tunnel-zone ${TZ} member list | awk "\$4 == \"${HOST}\" {print \$2}")
if [ -z "${MATCH}" ]; then
    midonet-cli -e tunnel-zone ${TZ} add member host ${HOST} address ${MIDOLMAN_IP}
fi
