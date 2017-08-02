#! /usr/bin/env bash

set -x
set -e

source $GRENADE_DIR/grenaderc
source $GRENADE_DIR/functions

PROJECT=networking-midonet

function create_resources {
    # NOTE(yamamoto): openrc can alter $DEST
    source $TOP_DIR/openrc admin admin

    local POLICY1
    local POLICY2
    local NET1
    local NET2
    local SUBNET1
    local PORT1

    POLICY1=$(openstack network qos policy create -f value -c id policy1)
    resource_save ${PROJECT} policy1 ${POLICY1}

    POLICY2=$(openstack network qos policy create -f value -c id policy2)
    resource_save ${PROJECT} policy2 ${POLICY2}

    NET1=$(openstack network create -f value -c id --qos-policy ${POLICY1} net-midonet)
    resource_save ${PROJECT} net_midonet ${NET1}

    SUBNET1=$(openstack subnet create -f value -c id --ip-version 4 --subnet-range 192.2.0.0/24 --network ${NET1} subnet1)
    resource_save ${PROJECT} subnet1 ${SUBNET1}

    # NOTE(yamamoto): port qos policy is not supported by this version of osc
    # local PORT1=$(openstack port create -f value -c id --network ${NET1} --qos-policy ${POLICY2} port1)
    PORT1=$(neutron port-create -f value -c id --name port1 --qos-policy ${POLICY2} ${NET1})
    resource_save ${PROJECT} port1 ${PORT1}

    NET2=$(openstack network create -f value -c id --provider-network-type uplink net-uplink)
    resource_save ${PROJECT} net_uplink ${NET2}
}

function verify_resources {
    # NOTE(yamamoto): openrc can alter $DEST
    source $TOP_DIR/openrc admin admin

    local net_type
    local POLICY
    local POLICY1
    local POLICY2
    local NET1
    local NET2
    local PORT1

    POLICY1=$(resource_get ${PROJECT} policy1)
    POLICY2=$(resource_get ${PROJECT} policy2)

    NET1=$(resource_get ${PROJECT} net_midonet)
    net_type=$(openstack network show -f value -c provider:network_type ${NET1})
    test "${net_type}" = midonet

    POLICY=$(openstack network show -f value -c qos_policy_id ${NET1})
    test "${POLICY}" = ${POLICY1}

    NET2=$(resource_get ${PROJECT} net_uplink)
    net_type=$(openstack network show -f value -c provider:network_type ${NET2})
    test "${net_type}" = uplink

    POLICY=$(openstack network show -f value -c qos_policy_id ${NET2})
    test "${POLICY}" = None

    PORT1=$(resource_get ${PROJECT} port1)
    POLICY=$(openstack port show -f value -c qos_policy_id ${PORT1})
    test "${POLICY}" = ${POLICY2}
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
