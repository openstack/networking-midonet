# Copyright (C) 2012 Midokura Japan K.K.
# Copyright (C) 2013 Midokura PTE LTD
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

# Import all data models
from networking_l2gw.db.l2gateway import l2gateway_models  # noqa

from midonet.neutron.client import base as cli_base
# Import all data models
from midonet.neutron.common import config  # noqa
from midonet.neutron.db.migration.models import head  # noqa


TEST_MN_CLIENT = ('midonet.neutron.tests.unit.test_midonet_plugin.'
                  'NoopMidonetClient')


class NoopMidonetClient(cli_base.MidonetClientBase):
    """Dummy midonet client used for the unit tests"""
    pass
