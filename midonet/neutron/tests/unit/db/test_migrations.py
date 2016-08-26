# Copyright (c) 2015 Cisco Systems, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_config import cfg

from neutron.db.migration.alembic_migrations import external
from neutron.db.migration import cli as migration
from neutron.tests.functional.db import test_migrations
from neutron.tests.unit import testlib_api

# NOTE(yamamoto): midonet_firewall_logs has a FK to firewalls.id
import neutron_fwaas.db.firewall.firewall_db  # noqa

from midonet.neutron.db.migration.models import head

# List of *aaS tables to exclude
# REVISIT(yamamoto): These *aaS repos should provide the lists by themselves,
# similarly to Neutron's external.TABLES.

LBAAS_TABLES = {
    # NOTE(yamamoto): We don't import these models
    'nsxv_edge_monitor_mappings',
    'nsxv_edge_pool_mappings',
    'nsxv_edge_vip_mappings',

    # LBaaS v2 tables
    'lbaas_healthmonitors',
    'lbaas_l7policies',
    'lbaas_l7rules',
    'lbaas_listeners',
    'lbaas_loadbalancer_statistics',
    'lbaas_loadbalanceragentbindings',
    'lbaas_loadbalancers',
    'lbaas_members',
    'lbaas_pools',
    'lbaas_sessionpersistences',
    'lbaas_sni',
}

FWAAS_TABLES = {
    # NOTE(yamamoto): We don't import these models
    'cisco_firewall_associations',
    'firewall_router_associations',
    # NOTE(yamamoto): We don't support FWaaS v2
    'firewall_rules_v2',
    'firewall_groups_v2',
    'firewall_group_port_associations_v2',
    'firewall_policy_rule_associations_v2',
    'firewall_policies_v2',
}

VPNAAS_TABLES = {
    # NOTE(yamamoto): We don't import these models
    'vpn_endpoint_groups',
    'vpn_endpoints',
}

L2GW_TABLES = {
    # NOTE(yamamoto): We don't import these models
    'l2gw_alembic_version',
    'physical_locators',
    'physical_switches',
    'physical_ports',
    'logical_switches',
    'ucast_macs_locals',
    'ucast_macs_remotes',
    'vlan_bindings',
    'l2gatewayconnections',
    'l2gatewayinterfaces',
    'l2gatewaydevices',
    'l2gateways',
    'pending_ucast_macs_remotes'
}

TAAS_TABLES = {
    'tap_services',
    'tap_flows',
    'tap_id_associations',
}

# EXTERNAL_TABLES should contain all names of tables that are not related to
# current repo.
EXTERNAL_TABLES = (set(external.TABLES) | LBAAS_TABLES | FWAAS_TABLES |
                   VPNAAS_TABLES | L2GW_TABLES | TAAS_TABLES)
# FIXME(yamamoto): Fix this after branching stable/mitaka
EXTERNAL_TABLES |= {'bgp_speaker_router_associations'}
VERSION_TABLE = 'alembic_version_midonet'


class _TestModelsMigrationsMidonet(test_migrations._TestModelsMigrations):

    def db_sync(self, engine):
        cfg.CONF.set_override('connection', engine.url, group='database')
        for conf in migration.get_alembic_configs():
            self.alembic_config = conf
            self.alembic_config.neutron_config = cfg.CONF
            migration.do_alembic_command(conf, 'upgrade', 'heads')

    def get_metadata(self):
        return head.get_metadata()

    def include_object(self, object_, name, type_, reflected, compare_to):
        if type_ == 'table' and (name.startswith('alembic') or
                                 name == VERSION_TABLE or
                                 name in EXTERNAL_TABLES):
            return False
        if type_ == 'index' and reflected and name.startswith("idx_autoinc_"):
            return False
        return True


class TestModelsMigrationsMysql(testlib_api.MySQLTestCaseMixin,
                                _TestModelsMigrationsMidonet,
                                testlib_api.SqlTestCaseLight):
    pass


class TestModelsMigrationsPostgresql(testlib_api.PostgreSQLTestCaseMixin,
                                     _TestModelsMigrationsMidonet,
                                     testlib_api.SqlTestCaseLight):
    pass
