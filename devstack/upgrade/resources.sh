#! /usr/bin/env bash

set -x

source $GRENADE_DIR/grenaderc
source $GRENADE_DIR/functions

function verify() {
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
}

case $1 in
    "verify")
        verify $2
        ;;
esac
