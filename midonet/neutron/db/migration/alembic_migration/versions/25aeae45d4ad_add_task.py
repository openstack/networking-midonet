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

"""add task

Revision ID: 25aeae45d4ad
Revises: None
Create Date: 2014-10-27 13:26:15.053541

"""

# revision identifiers, used by Alembic.
revision = '25aeae45d4ad'
down_revision = 'start_neutron_midonet'

from alembic import op
import sqlalchemy as sa


def upgrade():

    if op.get_bind().engine.dialect.name == 'mysql':
        # NOTE(yamamoto): Specify a length long enough to make
        # the dialict to choose LONGTEXT
        data_type = sa.Text(length=2 ** 24)
    else:
        data_type = sa.Text()

    op.create_table(
        'midonet_tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('type', sa.String(length=36)),
        sa.Column('data_type', sa.String(length=36)),
        sa.Column('data', data_type),
        sa.Column('resource_id', sa.String(length=36)),
        sa.Column('tenant_id', sa.String(length=255)),
        sa.Column('transaction_id', sa.String(length=40), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),)
