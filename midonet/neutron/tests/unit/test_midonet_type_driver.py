# Copyright (c) 2015 Midokura SARL
# All Rights Reserved.
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

from midonet.neutron.common import constants as const
from midonet.neutron.ml2 import type_midonet

from neutron.common import exceptions as exc
from neutron.plugins.ml2 import driver_api as api
from neutron.tests import base


class MidonetTypeTest(base.BaseTestCase):

    network_type = const.TYPE_MIDONET
    driver = type_midonet.MidonetTypeDriver()

    def setUp(self):
        super(MidonetTypeTest, self).setUp()
        self.session = None

    def test_is_partial_segment(self):
        segment = {api.NETWORK_TYPE: self.network_type}
        self.assertFalse(self.driver.is_partial_segment(segment))

    def test_validate_provider_segment(self):
        segment = {api.NETWORK_TYPE: self.network_type}
        self.driver.validate_provider_segment(segment)

    def test_validate_provider_segment_with_unallowed_physical_network(self):
        segment = {api.NETWORK_TYPE: self.network_type,
                   api.PHYSICAL_NETWORK: 'phys_net'}
        self.assertRaises(exc.InvalidInput,
                          self.driver.validate_provider_segment,
                          segment)

    def test_validate_provider_segment_with_unallowed_segmentation_id(self):
        segment = {api.NETWORK_TYPE: self.network_type,
                   api.SEGMENTATION_ID: 2}
        self.assertRaises(exc.InvalidInput,
                          self.driver.validate_provider_segment,
                          segment)

    def test_reserve_provider_segment(self):
        segment = {api.NETWORK_TYPE: self.network_type}
        observed = self.driver.reserve_provider_segment(self.session, segment)
        self.assertEqual(segment, observed)

    def test_release_provider_segment(self):
        segment = {api.NETWORK_TYPE: self.network_type}
        observed = self.driver.reserve_provider_segment(self.session, segment)
        self.driver.release_segment(self.session, observed)

    def test_allocate_tenant_segment(self):
        expected = {api.NETWORK_TYPE: self.network_type}
        observed = self.driver.allocate_tenant_segment(self.session)
        self.assertEqual(expected, observed)
