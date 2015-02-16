# Copyright 2014 Midokura SARL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Need to import all data models, as the 'neutron/tests/unit/testlib_api.py'
# does.
#
# For now, we are going to load here. If we have to create a new base lib from
# where all the MidoNet tests must extends, it may be a good idea to move it
# there.
import os

from oslo_config import cfg

from midonet.neutron.db import routedserviceinsertion_db  # noqa
from midonet.neutron.db import task  # noqa
from neutron.db.migration.models import head  # noqa
from neutron_lbaas.db.loadbalancer import loadbalancer_db as lb_db  # noqa

MIDONET_TEST_ROOTDIR = os.path.dirname(os.path.abspath(__file__))
MIDONET_TEST_ETCDIR = os.path.join(MIDONET_TEST_ROOTDIR, 'etc')
POLICY_JSON_TEST_FILE = "%s/policy.json.test" % MIDONET_TEST_ETCDIR
cfg.CONF.set_override('policy_file', POLICY_JSON_TEST_FILE)
