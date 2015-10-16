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
from midonet.neutron.ml2 import type_uplink
from midonet.neutron.tests.unit import test_midonet_type_driver as test_midonet


class UplinkTypeTest(test_midonet.MidonetTypeTest):

    network_type = const.TYPE_UPLINK
    driver = type_uplink.UplinkTypeDriver()
