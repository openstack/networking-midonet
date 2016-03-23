#!/bin/bash

# Copyright 2015 Midokura SARL
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

# This script is meant to be sourced from devstack.  It is a wrapper of
# devmido scripts that allows proper exporting of environment variables.

ABSOLUTE_PATH=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)

if [[ "$1" == "stack" ]]; then

    if [[ "$2" == "pre-install" ]]; then

        source $ABSOLUTE_PATH/functions
        source $ABSOLUTE_PATH/$Q_PLUGIN/functions

        # Clone and build midonet service
        if [[ "$OFFLINE" != "True" ]]; then
            if [[ ! -d $MIDONET_DIR ]]; then
                local orig_dir=$(pwd)

                git clone $MIDONET_REPO $MIDONET_DIR
                cd $MIDONET_DIR
                git checkout $MIDONET_BRANCH
                cd ${orig_dir}
            fi
        fi

        # Clone and build neutron midonet plugin
        PLUGIN_PATH=$ABSOLUTE_PATH/..

    elif [[ "$2" == "install" ]]; then

        # Build neutron midonet plugin
        pip_install --no-deps --editable $PLUGIN_PATH
        # Ensure that we can do "tox -e genconfig" in the later phase
        safe_chown -R $STACK_USER $PLUGIN_PATH/*.egg-info

        # Build midonet client
        pip_install --editable $MIDONET_DIR/python-midonetclient

    elif [[ "$2" == "extra" ]]; then

        if [ "$MIDONET_CREATE_FAKE_UPLINK" == "True" ]; then
            if [[ "$MIDONET_USE_ZOOM" == "True" ]]; then
                if [ "$MIDONET_USE_UPLINK" == "True" ]; then
                    . $ABSOLUTE_PATH/uplink/create_uplink.sh
                else
                    $MIDONET_DIR/tools/devmido/create_fake_uplink_l2.sh \
                        $EXT_NET_ID $FLOATING_RANGE $PUBLIC_NETWORK_GATEWAY
                    local ROUTER_GW_IP
                    ROUTER_GW_IP=`neutron port-list -c fixed_ips -c device_owner | grep router_gateway | awk -F'ip_address'  '{ print $2 }' | cut -f3 -d\" | tr '\n' ' '`
                    sudo ip route replace ${FIXED_RANGE} via ${ROUTER_GW_IP}
                fi
            else
                $MIDONET_DIR/tools/devmido/create_fake_uplink.sh \
                    $FLOATING_RANGE
            fi
        fi

        # Set log level to DEBUG.
        # REVISIT(yamamoto): Revisit when MNA-1025 is fixed on
        # all relevant bracnches.
        echo agent.loggers.root: DEBUG|mn-conf set

    elif [[ "$2" == "post-config" ]]; then

        configure_neutron_midonet
        if is_service_enabled l2gw-plugin; then
            l2gw_configure_midonet
        fi
        create_nova_conf_midonet

        export SERVICE_HOST=${MIDONET_SERVICE_HOST:?Error \$MIDONET_SERVICE_HOST is not set}
        export API_PORT=$MIDONET_SERVICE_API_PORT
        export API_TIMEOUT=${MIDONET_API_TIMEOUT}

        export TIMESTAMP_FORMAT
        export LOGFILE
        export USE_SCREEN
        export SCREEN_LOGDIR
        export LOGDIR
        export MIDO_PASSWORD=$SERVICE_PASSWORD
        export MIDO_DB_USER=$DATABASE_USER
        export MIDO_DB_PASSWORD=$DATABASE_PASSWORD
        export CONFIGURE_LOGGING
        export USE_METADATA=$MIDONET_USE_METADATA
        export NOVA_METADATA_URL=$MIDONET_NOVA_METADATA_URL
        export METADATA_SHARED_SECRET=$MIDONET_METADATA_SHARED_SECRET

        # Run the command
        $MIDONET_DIR/tools/devmido/mido.sh

        # Set rootwrap.d to installed mm-ctl filters
        sudo cp $ABSOLUTE_PATH/midonet_rootwrap.filters /etc/neutron/rootwrap.d/

        neutron-db-manage --subproject networking-midonet upgrade head

        if is_service_enabled nova; then
            sudo cp $ABSOLUTE_PATH/midonet_rootwrap.filters /etc/nova/rootwrap.d/

            # Hack libvirt qemu conf to allow ethernet mode to run
            export LIBVIRT_QEMU_CONF='/etc/libvirt/qemu.conf'
            if [ ! $(sudo grep -q '^cgroup_device_acl' $LIBVIRT_QEMU_CONF) ]; then
                sudo bash -c "cat <<EOF >> $LIBVIRT_QEMU_CONF
cgroup_device_acl = [
    '/dev/null', '/dev/full', '/dev/zero',
    '/dev/random', '/dev/urandom',
    '/dev/ptmx', '/dev/kvm', '/dev/kqemu',
    '/dev/rtc', '/dev/hpet', '/dev/net/tun',
]
EOF"
                sudo service libvirt-bin restart
            fi
        fi
    fi

elif [[ "$1" == "unstack" ]]; then

    source $ABSOLUTE_PATH/functions
    source $ABSOLUTE_PATH/$Q_PLUGIN/functions

    if [ "$MIDONET_CREATE_FAKE_UPLINK" == "True" ]; then
        if [[ "$MIDONET_USE_ZOOM" == "True" ]]; then
            if [ "$MIDONET_USE_UPLINK" == "True" ]; then
                . $ABSOLUTE_PATH/uplink/delete_uplink.sh
            else
                $MIDONET_DIR/tools/devmido/delete_fake_uplink_l2.sh
            fi
        else
            $MIDONET_DIR/tools/devmido/delete_fake_uplink.sh
        fi
    fi
    $MIDONET_DIR/tools/devmido/unmido.sh
fi
