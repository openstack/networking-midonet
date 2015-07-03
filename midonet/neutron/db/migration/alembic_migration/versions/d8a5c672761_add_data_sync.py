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

"""add data sync

Revision ID: d8a5c672761
Revises: 25aeae45d4ad
Create Date: 2015-03-16 06:04:40.695379

"""

# revision identifiers, used by Alembic.
revision = 'd8a5c672761'
down_revision = '25aeae45d4ad'

from alembic import op
import datetime
import sqlalchemy as sa


def upgrade():

    op.create_table('midonet_data_versions',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('sync_started_at', sa.DateTime()),
                    sa.Column('sync_finished_at', sa.DateTime()),
                    sa.Column('sync_status', sa.String(length=50)),
                    sa.Column('sync_tasks_status', sa.String(length=50)),
                    sa.Column('stale', sa.Boolean(), nullable=False))

    op.create_table('midonet_data_state',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('last_processed_task_id', sa.Integer()),
                    sa.Column('updated_at', sa.DateTime(),
                              default=datetime.datetime.utcnow,
                              nullable=False),
                    sa.Column('active_version', sa.Integer()),
                    sa.Column('readonly', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(
                        ['last_processed_task_id'], ['midonet_tasks.id']),
                    sa.ForeignKeyConstraint(
                        ['active_version'],
                        ['midonet_data_versions.id']))

    op.execute("INSERT INTO midonet_data_state (id, last_processed_task_id, "
               "updated_at, active_version, readonly) VALUES (1, NULL, '%s', "
               "NULL, false)" % (datetime.datetime.utcnow()))
