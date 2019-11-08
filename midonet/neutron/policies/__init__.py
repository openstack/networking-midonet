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

import itertools

from midonet.neutron.policies import bgp_speaker_router_insertion
from midonet.neutron.policies import gateway_device


def list_rules():
    return itertools.chain(
        bgp_speaker_router_insertion.list_rules(),
        gateway_device.list_rules(),
    )
