#! /usr/bin/env bash

source $GRENADE_DIR/grenaderc
source $GRENADE_DIR/functions
source $TARGET_DEVSTACK_DIR/stackrc

setup_develop $TARGET_RELEASE_DIR/networking-midonet
