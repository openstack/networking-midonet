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

# lib/neutron vs lib/neutron-legacy compat
Q_PLUGIN=${Q_PLUGIN:-$NEUTRON_CORE_PLUGIN}
Q_PLUGIN_CONF_FILE=${Q_PLUGIN_CONF_FILE:-$NEUTRON_CORE_PLUGIN_CONF}
Q_ADMIN_USERNAME=${Q_ADMIN_USERNAME:-neutron}
Q_DHCP_CONF_FILE=${Q_DHCP_CONF_FILE:-$NEUTRON_DHCP_CONF}
Q_META_DATA_IP=${Q_META_DATA_IP:-$SERVICE_HOST}

if [[ "$1" == "stack" ]]; then

    if [[ "$2" == "pre-install" ]]; then

        source $ABSOLUTE_PATH/functions
        source $ABSOLUTE_PATH/$Q_PLUGIN/functions

        # Install MidoNet packages.
        # NOTE(yamamoto): Do this even if MIDONET_USE_PACKAGE=False, to pull
        # runtime dependencies like libreswan.
        # REVISIT(yamamoto): Consider to have a separate set of scripts
        # for dependencies.
        if [[ "$OFFLINE" != "True" ]]; then
            sudo $ABSOLUTE_PATH/midonet-pkg/configure_repo.sh \
                $MIDONET_DEB_URI $MIDONET_DEB_SUITE $MIDONET_DEB_COMPONENT \
                $MIDONET_USE_CASSANDRA
            sudo $ABSOLUTE_PATH/midonet-pkg/install_pkgs.sh \
                $MIDONET_USE_CASSANDRA
        fi

        if [ "$MIDONET_USE_PACKAGE" != "True" ]; then
            # Clone MidoNet source
            if [[ "$OFFLINE" != "True" ]]; then
                if [[ ! -d $MIDONET_DIR ]]; then
                    local orig_dir=$(pwd)

                    git clone $MIDONET_REPO $MIDONET_DIR
                    cd $MIDONET_DIR
                    git checkout $MIDONET_BRANCH
                    cd ${orig_dir}
                fi
            fi

            # Build and install MidoNet packages
            local orig_dir=$(pwd)
            cd $MIDONET_DIR
            find . -type f -name "*.deb" -print0 | xargs -0 -r rm
            ./gradlew nsdb:clean  # workaround for errors after proto changes
            install_package ruby-dev
            install_package ruby-ronn
            sudo gem install fpm
            # Also, we need JDK to build MidoNet (vs JRE)
            install_package openjdk-8-jdk-headless
            ./gradlew debian
            find . -type f -name "*.deb" -print0 | xargs -0 sudo dpkg -i
            cd ${orig_dir}
        fi

    elif [[ "$2" == "install" ]]; then

        # Build neutron midonet plugin
        pip_install --no-deps --editable $NETWORKING_MIDONET_DIR
        # Configure midonet-cli
        configure_midonet_cli

        install_neutron_midonet

    elif [[ "$2" == "extra" ]]; then

        tweak_neutron_initial_network_for_midonet

        if [ "$MIDONET_CREATE_FAKE_UPLINK" == "True" ]; then
            . $ABSOLUTE_PATH/uplink/create_uplink.sh
            if [ "$MIDONET_USE_UPLINK_NAT" == "True" ]; then
                . $ABSOLUTE_PATH/uplink/create_nat.sh
            fi
            . $ABSOLUTE_PATH/tz/create_tz.sh
        fi

    elif [[ "$2" == "post-config" ]]; then

        configure_neutron_midonet
        create_nova_conf_midonet

        get_or_create_role midonet-admin
        get_or_add_user_project_role \
            midonet-admin "$Q_ADMIN_USERNAME" "$SERVICE_PROJECT_NAME"
        get_or_add_user_project_role midonet-admin admin admin
        create_service_user "midonet"

        export SERVICE_HOST=${MIDONET_SERVICE_HOST:?Error \$MIDONET_SERVICE_HOST is not set}
        export API_PORT=$MIDONET_SERVICE_API_PORT
        export API_TIMEOUT=${MIDONET_API_TIMEOUT}

        export MIDONET_USE_KEYSTONE
        export KEYSTONE_AUTH_URI_V3
        export SERVICE_PROJECT_NAME
        export SERVICE_PASSWORD
        export TOPOLOGY_API_PORT

        export TIMESTAMP_FORMAT
        export LOGFILE
        export USE_SCREEN
        export SCREEN_LOGDIR
        export LOGDIR
        export MIDO_PASSWORD=$ADMIN_PASSWORD
        export MIDO_DB_USER=$DATABASE_USER
        export MIDO_DB_PASSWORD=$DATABASE_PASSWORD
        export CONFIGURE_LOGGING
        export USE_METADATA=$MIDONET_USE_METADATA
        export NOVA_METADATA_URL=$MIDONET_NOVA_METADATA_URL
        export METADATA_SHARED_SECRET=$MIDONET_METADATA_SHARED_SECRET
        if [ $MIDONET_CLIENT = "midonet.neutron.client.cluster.MidonetClusterClient" ]; then
            export ENABLE_TASKS_IMPORTER=True
        fi

        # Run the command
        # Create symbolic links for logs so that they will be
        # gathered on gate.
        ln -sf /var/log/midolman/midolman.log ${LOGDIR}
        ln -sf /var/log/midolman/minions.log ${LOGDIR}
        ln -sf /var/log/midolman/minions-stderr.log ${LOGDIR}
        ln -sf /var/log/midolman/vpp.log ${LOGDIR}
        ln -sf /var/log/midolman/vpp-stderr.log ${LOGDIR}
        ln -sf /var/log/midolman/upstart-stderr.log ${LOGDIR}
        ln -sf /var/log/midonet-cluster/midonet-cluster.log ${LOGDIR}
        ln -sf /var/log/midonet-cluster/upstart-stderr.log ${LOGDIR}
        $ABSOLUTE_PATH/midonet-pkg/configure_and_start_midonet.sh

        # copy needed neutron config (eg rootwrap filters)
        sudo cp $NETWORKING_MIDONET_DIR/etc/midonet_rootwrap.filters /etc/neutron/rootwrap.d/

        neutron-db-manage --subproject networking-midonet upgrade head

        if is_service_enabled nova; then
            sudo cp $NETWORKING_MIDONET_DIR/etc/midonet_rootwrap.filters /etc/nova/rootwrap.d/

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
    elif [[ "$2" == "test-config" ]]; then
        # MidoNet LBaaS doesn't support HTTP.
        iniset $TEMPEST_CONFIG lbaas default_listener_protocol TCP
        iniset $TEMPEST_CONFIG lbaas default_pool_protocol TCP
    fi

elif [[ "$1" == "unstack" ]]; then

    source $ABSOLUTE_PATH/functions
    source $ABSOLUTE_PATH/$Q_PLUGIN/functions

    if [ "$MIDONET_CREATE_FAKE_UPLINK" == "True" ]; then
        . $ABSOLUTE_PATH/tz/delete_tz.sh
        if [ "$MIDONET_USE_UPLINK_NAT" == "True" ]; then
            . $ABSOLUTE_PATH/uplink/delete_nat.sh
        fi
        . $ABSOLUTE_PATH/uplink/delete_uplink.sh
    fi
    $ABSOLUTE_PATH/midonet-pkg/stop_midonet.sh
fi
