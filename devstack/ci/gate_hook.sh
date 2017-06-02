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

LOCAL_CONF=/tmp/late-local.conf

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
    $DSCONF merge_lc $LOCAL_CONF $GATE_HOOKS/$hook
}

case $job in
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
        _ML2=False
        _ADV_SVC=False
        ;;
    v2-full)
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
        _ML2=False
        _ADV_SVC=True
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
        _ML2=True
        _ADV_SVC=False
        ;;
    ml2-full)
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
        _ML2=True
        _ADV_SVC=True
        ;;
    grenade|grenade-ml2)
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
        _ZOOM=True
        _ML2=True
        _ADV_SVC=False
        load_conf_hook quotas old
        ;;
    rally|rally-v2)
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
        _ML2=False
        _ADV_SVC=False
        ;;
    rally-ml2)
        # Note the actual url here is somewhat irrelevant because it
        # caches in nodepool, however make it a valid url for
        # documentation purposes.
        export DEVSTACK_LOCAL_CONFIG="enable_plugin networking-midonet git://git.openstack.org/openstack/networking-midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin rally git://git.openstack.org/openstack/rally"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_PLUGIN=ml2"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"TEMPEST_RUN_VALIDATION=True"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_ML2_PLUGIN_MECHANISM_DRIVERS=midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_ML2_PLUGIN_TYPE_DRIVERS=midonet,uplink"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_ML2_TENANT_NETWORK_TYPE=midonet"
        export DEVSTACK_LOCAL_CONFIG+=$'\n'"ML2_L3_PLUGIN=midonet.neutron.services.l3.l3_midonet.MidonetL3ServicePlugin"
        _ML2=True
        _ADV_SVC=False
esac

# We are only interested on Neutron, so very few services are needed
# to deploy devstack and run the tests
s=""
s+="mysql,rabbit"
s+=",key"
s+=",n-api,n-cond,n-cpu,n-crt,n-sch,placement-api"
s+=",g-api,g-reg"
s+=",q-svc,quantum"
if [ -z "${RALLY_SCENARIO}" ] ; then
    # Only include tempest if this is not a rally job.
    s+=",tempest"
fi
s+=",dstat"
# Use midonet metadata proxy
export DEVSTACK_LOCAL_CONFIG+=$'\n'"MIDONET_USE_METADATA=True"

# Tweak the chain for midonet metadata proxy.
# "metadata" interface is created by midolman for node-local use.
# OpenStack gate slaves have a rule which would reject packets
# forwarded to the metadata proxy:
#   https://github.com/openstack-infra/system-config/blob/master/modules/openstack_project/manifests/single_use_slave.pp
#   https://github.com/openstack-infra/puppet-iptables
sudo iptables -I openstack-INPUT 1 -i metadata -j ACCEPT || :

# Tweak the chain for midonet vpp downlink for fip64.
sudo iptables -I openstack-INPUT 1 -i tun-dl-+ -j ACCEPT || :

if [ "${_ADV_SVC}" = "True" ]; then
    # Enable FWaaS
    s+=",q-fwaas"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin neutron-fwaas https://github.com/openstack/neutron-fwaas"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"FWAAS_PLUGIN=midonet_firewall"

    # Enable VPNaaS
    s+=",neutron-vpnaas"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin neutron-vpnaas https://github.com/openstack/neutron-vpnaas"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"NEUTRON_VPNAAS_SERVICE_PROVIDER=\"VPN:Midonet:midonet.neutron.services.vpn.service_drivers.midonet_ipsec.MidonetIPsecVPNDriver:default\""

    # Enable QoS
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin neutron https://github.com/openstack/neutron"
    s+=",q-qos"

    # Enable LBaaSv2
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin neutron-lbaas https://git.openstack.org/openstack/neutron-lbaas"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_service q-lbaasv2"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"NEUTRON_LBAAS_SERVICE_PROVIDERV2=\"LOADBALANCERV2:Midonet:midonet.neutron.services.loadbalancer.v2_driver.MidonetLoadBalancerDriver:default\""

    # Enable Tap as a service
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin tap-as-a-service https://git.openstack.org/openstack/tap-as-a-service"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_service taas"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"TAAS_SERVICE_DRIVER=\"TAAS:Midonet:midonet.neutron.services.taas.service_drivers.taas_midonet.MidonetTaasDriver:default\""

    # Enable neutron-dynamic-routing
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin neutron-dynamic-routing https://git.openstack.org/openstack/neutron-dynamic-routing"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"DR_MODE=dr_plugin"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"BGP_PLUGIN=midonet_bgp"
fi

export OVERRIDE_ENABLED_SERVICES="$s"

# Begin list of exclusions.
r="^(?!.*"

# exclude the slow tag (part of the default for 'full')
r="$r(?:.*\[.*\bslow\b.*\])"

# https://bugs.launchpad.net/tempest/+bug/1509590
r="$r|(?:tempest\.api\.network\.admin\.test_dhcp_agent_scheduler\.DHCPAgentSchedulersTestJSON\.test_add_remove_network_from_dhcp_agent.*)"
r="$r|(?:tempest\.api\.network\.admin\.test_dhcp_agent_scheduler\.DHCPAgentSchedulersTestJSON\.test_list_networks_hosted_by_one_dhcp.*)"
r="$r|(?:tempest\.api\.network\.admin\.test_agent_management\.AgentManagementTestJSON.*)"
r="$r|(?:^neutron\.tests\.tempest\.api\.admin\.test_dhcp_agent_scheduler\.DHCPAgentSchedulersTestJSON\..*)"
r="$r|(?:^neutron\.tests\.tempest\.api\.admin\.test_agent_management\.AgentManagementTestJSON\.*)"

if [ "${_ML2}" = "True" ]; then
    # bug 1507453 1608796
    r="$r|(?:^neutron\.tests\.tempest\.api\.test_routers\.RoutersTest\.test_router_interface_status)"
fi

# MidoNet doesn't support a gateway port without IP. (MNP-167)
# "Bad router request: No IPs assigned to the gateway port for router"
r="$r|(?:^neutron\.tests\.tempest\.api\.admin\.test_external_network_extension\.ExternalNetworksRBACTestJSON\.test_regular_client_shares_with_another)"
r="$r|(?:^neutron\.tests\.tempest\.api\.admin\.test_external_network_extension\.ExternalNetworksRBACTestJSON\.test_external_update_policy_from_wildcard_to_specific_tenant)"

# MidoNet doesn't support HTTP_COOKIE/APP_COOKIE
r="$r|(?:^neutron_lbaas\.tests\.tempest\.v2\.api\.test_pools_admin\.TestPools\.test_update_pool_sesssion_persistence_app_cookie)"
r="$r|(?:^neutron_lbaas\.tests\.tempest\.v2\.api\.test_pools_admin\.TestPools\.test_update_pool_sesssion_persistence_app_to_http)"
r="$r|(?:^neutron_lbaas\.tests\.tempest\.v2\.api\.test_pools_non_admin\.TestPools\.test_create_pool_with_session_persistence_http_cookie)"
r="$r|(?:^neutron_lbaas\.tests\.tempest\.v2\.api\.test_pools_non_admin\.TestPools\.test_create_pool_with_session_persistence_app_cookie)"
r="$r|(?:^neutron_lbaas\.tests\.tempest\.v2\.api\.test_pools_non_admin\.TestPools\.test_create_pool_with_session_persistence_redundant_cookie_name)"
r="$r|(?:^neutron_lbaas\.tests\.tempest\.v2\.api\.test_pools_non_admin\.TestPools\.test_create_pool_with_session_persistence_without_cookie_name)"

# bug 1693103
r="$r|(?:^neutron_lbaas\.tests\.tempest\.v2\.scenario\.test_session_persistence\.TestSessionPersistence\.test_session_persistence)"

# DDT tests have protocol=HTTP hardcoded.  MidoNet doesn't support it.
# Also, they often exceed the quota of loadbalancer
r="$r|(?:^neutron_lbaas\.tests\.tempest\.v2\.ddt\..*)"

# Skip non-networking api tests to save testing time
r="$r|(?:tempest\.api\.compute\..*)"
r="$r|(?:tempest\.api\.identity\..*)"
r="$r|(?:tempest\.api\.image\..*)"

# End list of exclusions.
r="$r)"

r="$r^(tempest\.(api|scenario)|neutron_fwaas|neutron_lbaas|neutron_vpnaas|neutron_taas|neutron|midonet)\..*$"

export DEVSTACK_GATE_TEMPEST_REGEX="$r"
export DEVSTACK_GATE_TEMPEST_ALL_PLUGINS=1
# NOTE(yamamoto): Tempest "all-plugin" uses OS_TEST_TIMEOUT=1200 by default.
# As we exclude slow tests by the above regex, 500, which is the default
# for "full", should be enough.
export TEMPEST_OS_TEST_TIMEOUT=500

# Explicitly set LOGDIR to align with the SCREEN_LOGDIR setting
# from devstack-gate.  Otherwise, devstack infers it from LOGFILE,
# which is not appropriate for our gate jobs.
export DEVSTACK_LOCAL_CONFIG+=$'\n'"LOGDIR=$BASE/new/screen-logs"

# Use fernet tokens
export DEVSTACK_LOCAL_CONFIG+=$'\n'"KEYSTONE_TOKEN_FORMAT=fernet"

load_conf_hook quotas new

# NOTE(yamamoto): devstack-gate merges DEVSTACK_LOCALCONF
# after DEVSTACK_LOCAL_CONFIG
export DEVSTACK_LOCALCONF=$(cat $LOCAL_CONF)
$BASE/new/devstack-gate/devstack-vm-gate.sh
