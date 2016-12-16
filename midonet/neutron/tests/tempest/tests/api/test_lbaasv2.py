# Copyright 2016
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# TODO(Joe): move L4 version of tests to neutron-lbaas project

from neutron_lbaas.tests.tempest.v2.api import test_health_monitor_admin as hm_a  # noqa
from neutron_lbaas.tests.tempest.v2.api import test_health_monitors_non_admin as hm_na  # noqa
from neutron_lbaas.tests.tempest.v2.api import test_listeners_admin as l_a
from neutron_lbaas.tests.tempest.v2.api import test_listeners_non_admin as l_na
from neutron_lbaas.tests.tempest.v2.api import test_load_balancers_admin as lb_a  # noqa
from neutron_lbaas.tests.tempest.v2.api import test_load_balancers_non_admin as lb_na  # noqa
from neutron_lbaas.tests.tempest.v2.api import test_members_admin as m_a
from neutron_lbaas.tests.tempest.v2.api import test_members_non_admin as m_na
from neutron_lbaas.tests.tempest.v2.api import test_pools_admin as p_a
from neutron_lbaas.tests.tempest.v2.api import test_pools_non_admin as p_na
from tempest import test


class L4BaseMixin(object):
    @classmethod
    def _create_pool(cls, wait=True, **pool_kwargs):
        if pool_kwargs.get('protocol') == 'HTTP':
            pool_kwargs['protocol'] = 'TCP'
        return super(L4BaseMixin, cls)._create_pool(**pool_kwargs)

    @classmethod
    def _create_listener(cls, wait=True, **pool_kwargs):
        if pool_kwargs.get('protocol') == 'HTTP':
            pool_kwargs['protocol'] = 'TCP'
        return super(L4BaseMixin, cls)._create_listener(**pool_kwargs)


class TestL4HealthMonitorsAdmin(L4BaseMixin, hm_a.TestHealthMonitors):
    pass


class TestL4HealthMonitorsNonAdmin(L4BaseMixin, hm_na.TestHealthMonitors):
    pass


class TestL4ListenersAdmin(L4BaseMixin, l_a.ListenersTestJSON):
    pass


class TestL4ListenersNonAdmin(L4BaseMixin, l_na.ListenersTestJSON):
    pass


class TestL4LoadBalancersAdmin(L4BaseMixin, lb_a.LoadBalancersTestAdmin):
    pass


class TestL4LoadBalancersNonAdmin(L4BaseMixin, lb_na.LoadBalancersTestJSON):
    pass


class TestL4MembersAdmin(L4BaseMixin, m_a.MemberTestJSON):
    pass


class TestL4MembersNonAdmin(L4BaseMixin, m_na.MemberTestJSON):
    pass


class TestL4PoolsAdmin(L4BaseMixin, p_a.TestPools):

    @test.attr(type='smoke')
    def test_update_pool_sesssion_persistence_app_cookie(self):
        pass

    def test_update_pool_sesssion_persistence_app_to_http(self):
        pass


class TestL4PoolsNonAdmin(L4BaseMixin, p_na.TestPools):

    @test.attr(type='smoke')
    def test_create_pool_with_session_persistence_http_cookie(self):
        pass

    def test_create_pool_with_session_persistence_app_cookie(self):
        pass

    @test.attr(type='negative')
    def test_create_pool_with_session_persistence_redundant_cookie_name(self):
        pass

    @test.attr(type='negative')
    def test_create_pool_with_session_persistence_without_cookie_name(self):
        pass
