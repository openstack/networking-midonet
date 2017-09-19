# Copyright 2016 Midokura SARL
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

"""Remove agent membership

Revision ID: 1612b5389e6e
Revises: 27e6e3451f22
Create Date: 2016-12-09 00:27:26.878502

"""

from alembic import op

from neutron.db import migration


# revision identifiers, used by Alembic.
revision = '1612b5389e6e'
down_revision = '27e6e3451f22'

# milestone identifier, used by neutron-db-manage
neutron_milestone = [migration.OCATA, migration.PIKE]


def upgrade():
    op.drop_table('midonet_agent_memberships')
