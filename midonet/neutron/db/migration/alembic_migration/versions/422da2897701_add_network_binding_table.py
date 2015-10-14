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
"""add network binding table

Revision ID: 422da2897701
Revises: 421564f630b1
Create Date: 2015-06-05 03:23:00.000000

"""

from alembic import op
import sqlalchemy as sa

from neutron.db import migration

# revision identifiers, used by Alembic.
revision = '422da2897701'
down_revision = '421564f630b1'

# milestone identifier, used by neutron-db-manage
neutron_milestone = [migration.LIBERTY]


def upgrade():
    op.create_table(
        'midonet_network_bindings',
        sa.Column('network_id', sa.String(length=36),
                  sa.ForeignKey('networks.id'), nullable=False,
                  primary_key=True),
        sa.Column('network_type', sa.String(length=255), nullable=False))
