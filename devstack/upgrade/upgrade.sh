#! /usr/bin/env bash

source $GRENADE_DIR/grenaderc
source $GRENADE_DIR/functions
source $TARGET_DEVSTACK_DIR/stackrc

setup_develop $TARGET_RELEASE_DIR/networking-midonet

set -x

# Migrate from the monolithic plugin to ML2
# https://docs.openstack.org/developer/networking-midonet/ml2_migration.html
if [ ${Q_PLUGIN} != ml2 ]; then
    # REVISIT(yamamoto): It's better to avoid hardcoding these paths
    # but it's complicated to get these devstack variables here.
    # (See grenade/projects/50_neutron/upgrade.sh)
    _NEUTRON_CONF=/etc/neutron/neutron.conf
    _Q_PLUGIN_CONF_FILE=etc/neutron/plugins/midonet/midonet.ini

    iniset $_NEUTRON_CONF DEFAULT core_plugin ml2
    iniset /$_Q_PLUGIN_CONF_FILE ml2 mechanism_drivers midonet
    iniset /$_Q_PLUGIN_CONF_FILE ml2 type_drivers midonet,uplink
    iniset /$_Q_PLUGIN_CONF_FILE ml2 tenant_network_types midonet
    iniset /$_Q_PLUGIN_CONF_FILE ml2 external_network_type midonet
    iniset /$_Q_PLUGIN_CONF_FILE ml2 extension_drivers port_security,qos
fi
