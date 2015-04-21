# Copyright (C) 2015 Midokura SARL.
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

import neutron.common.exceptions as exc


class ClusterConnectionError(exc.ServiceUnavailable):
    message = _("Error connecting to cluster")


class MidonetApiException(exc.NeutronException):
    message = _("MidoNet API error: %(msg)s")


class InvalidMidonetDataState(exc.NeutronException):
    """
    Exception to signify a state in the midonet tables that is invalid,
    i.e. missing some table that should always be present
    """
    pass
