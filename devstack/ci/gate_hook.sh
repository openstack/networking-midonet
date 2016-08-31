#! /bin/bash

job=$1

case $job in;
    v1)
        # Note the actual url here is somewhat irrelevant because it
        # caches in nodepool, however make it a valid url for
        # documentation purposes.
        export DEVSTACK_LOCAL_CONFIG="enable_plugin networking-midonet git://git.openstack.org/openstack/networking-midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_PLUGIN=midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"TEMPEST_RUN_VALIDATION=True"

        # Enable MidoNet v1 architecture
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"MIDONET_PLUGIN=midonet.neutron.plugin_v1.MidonetPluginV2"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"MIDONET_CLIENT=midonet.neutron.client.api.MidonetApiClient"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"MIDONET_USE_ZOOM=False"
        # NOTE(yamamoto): v2015.06 is the latest stable releases
        # with v1 support.
        # REVISIT(yamamoto): Consider switching to stable/v2015.06.4
        # when available.
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"MIDONET_BRANCH=staging/v2015.06"
        ;;
    v2)
        # Note the actual url here is somewhat irrelevant because it
        # caches in nodepool, however make it a valid url for
        # documentation purposes.
        export DEVSTACK_LOCAL_CONFIG="enable_plugin networking-midonet git://git.openstack.org/openstack/networking-midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_PLUGIN=midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"TEMPEST_RUN_VALIDATION=True"

        # Enable MidoNet v2 architecture
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"MIDONET_PLUGIN=midonet.neutron.plugin_v2.MidonetPluginV2"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"MIDONET_CLIENT=midonet.neutron.client.api.MidonetApiClient"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_SERVICE_PLUGIN_CLASSES=midonet.neutron.services.l3.l3_midonet.MidonetL3ServicePlugin"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"MIDONET_USE_ZOOM=True"
        ;;
    ml2)
        # Note the actual url here is somewhat irrelevant because it
        # caches in nodepool, however make it a valid url for
        # documentation purposes.
        export DEVSTACK_LOCAL_CONFIG="enable_plugin networking-midonet git://git.openstack.org/openstack/networking-midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_PLUGIN=ml2"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"TEMPEST_RUN_VALIDATION=True"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_ML2_PLUGIN_MECHANISM_DRIVERS=midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_ML2_PLUGIN_TYPE_DRIVERS=midonet,uplink"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_ML2_TENANT_NETWORK_TYPE=midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"ML2_L3_PLUGIN=midonet.neutron.services.l3.l3_midonet.MidonetL3ServicePlugin"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"MIDONET_USE_ZOOM=True"
        ;;
    rally)
        # Note the actual url here is somewhat irrelevant because it
        # caches in nodepool, however make it a valid url for
        # documentation purposes.
        export DEVSTACK_LOCAL_CONFIG="enable_plugin networking-midonet git://git.openstack.org/openstack/networking-midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin rally git://git.openstack.org/openstack/rally"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_PLUGIN=midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"TEMPEST_RUN_VALIDATION=True"

        # Enable MidoNet v2 architecture
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"MIDONET_PLUGIN=midonet.neutron.plugin_v2.MidonetPluginV2"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"MIDONET_CLIENT=midonet.neutron.client.api.MidonetApiClient"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_SERVICE_PLUGIN_CLASSES=midonet.neutron.services.l3.l3_midonet.MidonetL3ServicePlugin"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"MIDONET_USE_ZOOM=True"
        ;;
esac

$BASE/new/devstack-gate/devstack-vm-gate.sh
