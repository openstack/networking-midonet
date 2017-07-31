#! /usr/bin/env bash

set -x

source $GRENADE_DIR/grenaderc
source $GRENADE_DIR/functions

PROJECT=networking-midonet

function create_resources {
    # NOTE(yamamoto): openrc can alter $DEST
    source $TOP_DIR/openrc admin admin

    ID=$(openstack network create -f value -c id net-midonet)
    resource_save ${PROJECT} net_midonet ${ID}
    ID=$(openstack network create -f value -c id --provider-network-type uplink net-uplink)
    resource_save ${PROJECT} net_uplink ${ID}
}

function verify_resources {
    # NOTE(yamamoto): openrc can alter $DEST
    source $TOP_DIR/openrc admin admin

    local ID
    local net_type

    ID=$(resource_get ${PROJECT} net_midonet)
    net_type=$(openstack network show -f value -c provider:network_type ${ID})
    test ${net_type} = midonet

    ID=$(resource_get ${PROJECT} net_uplink)
    net_type=$(openstack network show -f value -c provider:network_type ${ID})
    test ${net_type} = uplink
}

function verify {
    case $1 in
        "post-upgrade")
            # NOTE(yamamoto): Upgrade tempest config.  This doesn't really
            # belong to resources.sh.  But we need to do this after
            # upgrade-tempest, which copies the base config to the target.
            # See bug/1692388 bug/1687544
            # A relevant change: I2575a516244b848e5ed461e7f488c59edc41068d
            # REVISIT(yamamoto): Probably this belongs to either devstack or
            # grenade, not here.
            source $TARGET_DEVSTACK_DIR/stackrc
            source $TARGET_DEVSTACK_DIR/lib/tempest
            iniset $TEMPEST_CONFIG identity-feature-enabled api_v2_admin False
        ;;
    esac
    verify_resources
}

case $1 in
    "create")
        create_resources
        ;;
    "verify")
        verify $2
        ;;
esac
