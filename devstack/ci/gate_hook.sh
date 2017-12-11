#! /bin/bash

# Copyright 2016 Midokura SARL
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

job=$1
pyversion=$2


_DEVSTACK_LOCAL_CONFIG_TAIL=

# Inject config from hook
function load_conf_hook {
    local hook="$1"
    local new="$2"
    local GATE_DEST=$BASE/$new
    local GATE_HOOKS=$GATE_DEST/networking-midonet/devstack/ci/hooks

    if [ "$new" = "old" -a ! -f $GATE_HOOKS/$hook ]; then
        # REVISIT(yamamoto): Revisit once
        # https://review.openstack.org/#/c/406749/ is merged
        echo "Skipping $GATE_HOOKS/$hook for old branch"
        return
    fi
    _DEVSTACK_LOCAL_CONFIG_TAIL+=$'\n'"$(cat $GATE_HOOKS/$hook)"
}

case $job in
    ml2)
        # Note the actual url here is somewhat irrelevant because it
        # caches in nodepool, however make it a valid url for
        # documentation purposes.
        export DEVSTACK_LOCAL_CONFIG="enable_plugin networking-midonet git://git.openstack.org/openstack/networking-midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"TEMPEST_RUN_VALIDATION=True"
        _ADV_SVC=False
        _LEGACY=False
        _QOS=False
        ;;
    ml2-full)
        # Note the actual url here is somewhat irrelevant because it
        # caches in nodepool, however make it a valid url for
        # documentation purposes.
        export DEVSTACK_LOCAL_CONFIG="enable_plugin networking-midonet git://git.openstack.org/openstack/networking-midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"TEMPEST_RUN_VALIDATION=True"
        _ADV_SVC=True
        _LEGACY=False
        _QOS=True
        ;;
    ml2-full-legacy)
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
        _ADV_SVC=True
        _QOS=True
        _LEGACY=True
        ;;
    grenade-v2)
        # NOTE(yamamoto): This job performs a migration from v2 to ML2
        # Note the actual url here is somewhat irrelevant because it
        # caches in nodepool, however make it a valid url for
        # documentation purposes.
        export DEVSTACK_LOCAL_CONFIG="enable_plugin networking-midonet git://git.openstack.org/openstack/networking-midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_PLUGIN=midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"TEMPEST_RUN_VALIDATION=True"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"MIDONET_PLUGIN=midonet.neutron.plugin_v2.MidonetPluginV2"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"MIDONET_CLIENT=midonet.neutron.client.api.MidonetApiClient"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_SERVICE_PLUGIN_CLASSES=midonet.neutron.services.l3.l3_midonet.MidonetL3ServicePlugin"
        _ADV_SVC=False
        _QOS=True
        _LEGACY=True
        load_conf_hook quotas old
        # REVISIT(yamamoto): A crude workaround for bug/1700487
        # A better fix: Iec45a33930a06b17be00e8602f2457ab6960073f
        ln -s \
            $BASE/new/networking-midonet/devstack/midonet/functions \
            $BASE/new/devstack/lib/neutron_plugins/midonet
        ;;
    grenade-ml2)
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
        _ADV_SVC=False
        _LEGACY=True
        _QOS=True
        load_conf_hook quotas old
        ;;
    rally-ml2)
        # Note the actual url here is somewhat irrelevant because it
        # caches in nodepool, however make it a valid url for
        # documentation purposes.
        export DEVSTACK_LOCAL_CONFIG="enable_plugin networking-midonet git://git.openstack.org/openstack/networking-midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin rally git://git.openstack.org/openstack/rally"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"TEMPEST_RUN_VALIDATION=True"
        _ADV_SVC=False
        _LEGACY=False
        _QOS=False
esac

if [ "$pyversion" == "-py35" ]; then
    export DEVSTACK_GATE_USE_PYTHON3=True
fi

# We are only interested on Neutron, so very few services are needed
# to deploy devstack and run the tests
s=""
s+="mysql,rabbit"
s+=",key"
s+=",neutron"
s+=",n-api,n-cond,n-cpu,n-crt,n-sch,placement-api,n-api-meta"
s+=",g-api,g-reg"
if [ "${_LEGACY}" = "True" ]; then
    s+=",q-svc"
else
    s+=",neutron-api"
fi
if [ -z "${RALLY_SCENARIO}" ] ; then
    # Only include tempest if this is not a rally job.
    s+=",tempest"
fi
s+=",dstat"
# Use midonet metadata proxy
export DEVSTACK_LOCAL_CONFIG+=$'\n'"MIDONET_USE_METADATA=True"
export DEVSTACK_LOCAL_CONFIG+=$'\n'"MIDONET_METADATA_OPENSTACK_CI_TWEAK=True"

# Explicitly set LOGDIR to align with the SCREEN_LOGDIR setting
# from devstack-gate.  Otherwise, devstack infers it from LOGFILE,
# which is not appropriate for our gate jobs.
export DEVSTACK_LOCAL_CONFIG+=$'\n'"LOGDIR=$BASE/new/screen-logs"

# migration config
if [[ "$DEVSTACK_GATE_TOPOLOGY" != "aio" ]]; then
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"NOVA_ALLOW_MOVE_TO_SAME_HOST=False"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"LIVE_MIGRATION_AVAILABLE=True"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"USE_BLOCK_MIGRATION_FOR_LIVE_MIGRATION=True"
fi

# subnode config
export DEVSTACK_SUBNODE_CONFIG="$DEVSTACK_LOCAL_CONFIG"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"DATABASE_TYPE=mysql"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"DATABASE_HOST=\$SERVICE_HOST"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"RABBIT_HOST=\$SERVICE_HOST"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"disable_service mysql"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"disable_service rabbit"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"disable_service key"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"disable_service placement-api"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"disable_service n-api"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"disable_service n-api-meta"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"disable_service n-cond"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"disable_service n-crt"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"disable_service n-sch"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"disable_service g-api"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"disable_service g-reg"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"disable_service neutron-api"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"disable_service tempest"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"enable_service placement-client"
export DEVSTACK_SUBNODE_CONFIG+=$'\n'"MIDONET_CREATE_FAKE_UPLINK=False"

if [ "${_ADV_SVC}" = "True" ]; then
    # Enable FWaaS
    if [ "${_LEGACY}" = "True" ]; then
        s+=",q-fwaas"
    else
        s+=",neutron-fwaas-v1"
    fi
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin neutron-fwaas https://github.com/openstack/neutron-fwaas"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"FWAAS_PLUGIN=midonet_firewall"

    # Enable VPNaaS
    # NOTE(yamamoto): neutron-vpnaas devstack plugin doesn't have q- name
    s+=",neutron-vpnaas"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin neutron-vpnaas https://github.com/openstack/neutron-vpnaas"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"NEUTRON_VPNAAS_SERVICE_PROVIDER=\"VPN:Midonet:midonet.neutron.services.vpn.service_drivers.midonet_ipsec.MidonetIPsecVPNDriver:default\""

    # Enable LBaaSv2
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin neutron-lbaas https://git.openstack.org/openstack/neutron-lbaas"
    if [ "${_LEGACY}" = "True" ]; then
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_service q-lbaasv2"
    else
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_service neutron-lbaasv2"
    fi
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"NEUTRON_LBAAS_SERVICE_PROVIDERV2=\"LOADBALANCERV2:Midonet:midonet.neutron.services.loadbalancer.v2_driver.MidonetLoadBalancerDriver:default\""

    # Enable Tap as a service
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin tap-as-a-service https://git.openstack.org/openstack/tap-as-a-service"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_service taas"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"TAAS_SERVICE_DRIVER=\"TAAS:Midonet:midonet.neutron.services.taas.service_drivers.taas_midonet.MidonetTaasDriver:default\""

    # Enable neutron-dynamic-routing
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin neutron-dynamic-routing https://git.openstack.org/openstack/neutron-dynamic-routing"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"DR_MODE=dr_plugin"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"BGP_PLUGIN=midonet_bgp"
    # See REVISIT comment in devstack/settings
    if [ "${_LEGACY}" = "True" ]; then
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_service q-dr"
    else
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_service neutron-dr"
    fi
fi

if [ "${_QOS}" = "True" ]; then
    # Enable QoS
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin neutron https://github.com/openstack/neutron"
    if [ "${_LEGACY}" = "True" ]; then
        s+=",q-qos"
    else
        s+=",neutron-qos"
    fi

fi

export OVERRIDE_ENABLED_SERVICES="$s"

# Begin list of exclusions.
r="^(?!.*"

r="$r(?:.*\[.*\bDUMMY\b.*\])"

if ! lsb_release -i 2>/dev/null | grep -iq "ubuntu"; then
    # bug 1719771
    # The centos-7 image on gate uses libreswan-3.20-3.el7.x86_64,
    # which doesn't seem to be compatible with MidoNet.
    r="$r|(?:neutron_vpnaas)"
fi

# https://bugs.launchpad.net/tempest/+bug/1509590
r="$r|(?:tempest\.api\.network\.admin\.test_dhcp_agent_scheduler\.DHCPAgentSchedulersTestJSON\.test_add_remove_network_from_dhcp_agent.*)"
r="$r|(?:tempest\.api\.network\.admin\.test_dhcp_agent_scheduler\.DHCPAgentSchedulersTestJSON\.test_list_networks_hosted_by_one_dhcp.*)"
r="$r|(?:tempest\.api\.network\.admin\.test_agent_management\.AgentManagementTestJSON.*)"
r="$r|(?:^neutron_tempest_plugin\.api\.admin\.test_dhcp_agent_scheduler\.DHCPAgentSchedulersTestJSON\..*)"
r="$r|(?:^neutron_tempest_plugin\.api\.admin\.test_agent_management\.AgentManagementTestJSON\.*)"

# bug 1507453 1608796
r="$r|(?:^neutron_tempest_plugin\.api\.test_routers\.RoutersTest\.test_router_interface_status)"

# MidoNet doesn't support a gateway port without IP. (MNP-167)
# "Bad router request: No IPs assigned to the gateway port for router"
r="$r|(?:^neutron_tempest_plugin\.api\.admin\.test_external_network_extension\.ExternalNetworksRBACTestJSON\.test_regular_client_shares_with_another)"
r="$r|(?:^neutron_tempest_plugin\.api\.admin\.test_external_network_extension\.ExternalNetworksRBACTestJSON\.test_external_update_policy_from_wildcard_to_specific_tenant)"

# MidoNet doesn't support HTTP_COOKIE/APP_COOKIE
r="$r|(?:^neutron_lbaas\.tests\.tempest\.v2\.api\.test_pools_admin\.TestPools\.test_update_pool_sesssion_persistence_app_cookie)"
r="$r|(?:^neutron_lbaas\.tests\.tempest\.v2\.api\.test_pools_admin\.TestPools\.test_update_pool_sesssion_persistence_app_to_http)"
r="$r|(?:^neutron_lbaas\.tests\.tempest\.v2\.api\.test_pools_non_admin\.TestPools\.test_create_pool_with_session_persistence_http_cookie)"
r="$r|(?:^neutron_lbaas\.tests\.tempest\.v2\.api\.test_pools_non_admin\.TestPools\.test_create_pool_with_session_persistence_app_cookie)"
r="$r|(?:^neutron_lbaas\.tests\.tempest\.v2\.api\.test_pools_non_admin\.TestPools\.test_create_pool_with_session_persistence_redundant_cookie_name)"
r="$r|(?:^neutron_lbaas\.tests\.tempest\.v2\.api\.test_pools_non_admin\.TestPools\.test_create_pool_with_session_persistence_without_cookie_name)"

# DDT tests have protocol=HTTP hardcoded.  MidoNet doesn't support it.
# Also, they often exceed the quota of loadbalancer
r="$r|(?:^neutron_lbaas\.tests\.tempest\.v2\.ddt\..*)"

# Skip non-networking api tests to save testing time
r="$r|(?:tempest\.api\.compute\.(?!.*migration))"
r="$r|(?:tempest\.api\.identity\..*)"
r="$r|(?:tempest\.api\.image\..*)"

# End list of exclusions.
r="$r)"

r="$r^(tempest\.(api|scenario)|neutron_fwaas|neutron_lbaas|neutron_vpnaas|neutron_taas|neutron_tempest_plugin|midonet)\..*$"

export DEVSTACK_GATE_TEMPEST_REGEX="$r"
export DEVSTACK_GATE_TEMPEST_ALL_PLUGINS=0
# NOTE(yamamoto): Tempest "all" uses OS_TEST_TIMEOUT=1200 by default.
# As we exclude slow tests by the above regex, 500, which is the default
# for "full", should be enough.
export TEMPEST_OS_TEST_TIMEOUT=500
load_conf_hook tempest_plugins_base new
if [ "${_ADV_SVC}" = "True" ]; then
    load_conf_hook tempest_plugins_advsvc new
fi

# Use fernet tokens
export DEVSTACK_LOCAL_CONFIG+=$'\n'"KEYSTONE_TOKEN_FORMAT=fernet"

load_conf_hook quotas new

export DEVSTACK_LOCAL_CONFIG+=$'\n'"$_DEVSTACK_LOCAL_CONFIG_TAIL"

$BASE/new/devstack-gate/devstack-vm-gate.sh
