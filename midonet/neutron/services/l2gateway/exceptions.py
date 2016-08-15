# Copyright (C) 2016 Midokura SARL
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from neutron_lib import exceptions as nexception

from midonet.neutron._i18n import _


class MidonetL2GatewayUnavailable(nexception.ServiceUnavailable):
    message = _("Midonet L2 Gateway Service is unavailable "
                "because Gateway Device Management Service is disabled.")


class MidonetL2GatewayConnectionExists(nexception.InUse):
    message = _("L2 Gateway Connection related to "
                "specified L2 Gateway %(l2_gateway_id)s already exists")
