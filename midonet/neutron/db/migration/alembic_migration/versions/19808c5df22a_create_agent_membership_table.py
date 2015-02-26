# Copyright 2015 Midokura SARL
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

"""create agent membership table

Revision ID: 19808c5df22a
Revises: 1dc335c43b23
Create Date: 2015-02-26 14:39:25.219125

"""

# revision identifiers, used by Alembic.
revision = '19808c5df22a'
down_revision = '1dc335c43b23'

from alembic import op
import sqlalchemy as sa

AGENT_MEMBERSHIP_TABLE = 'midonet_agent_membership'


def upgrade():
    table_name = AGENT_MEMBERSHIP_TABLE
    op.create_table(
        table_name,
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('ip_address', sa.String(64), nullable=False),)


def downgrade():
    op.drop_table(AGENT_MEMBERSHIP_TABLE)
