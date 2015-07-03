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

"""add agent membership

Revision ID: 19808c5df22a
Revises: d8a5c672761
Create Date: 2015-02-26 14:39:25.219125

"""

# revision identifiers, used by Alembic.
revision = '19808c5df22a'
down_revision = 'd8a5c672761'

from alembic import op
import sqlalchemy as sa


def upgrade():

    op.create_table(
        "midonet_agent_memberships",
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('ip_address', sa.String(64), nullable=False),)
