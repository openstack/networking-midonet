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

"""add last-processed-task table

Revision ID: 7f435b33664
Revises: 19808c5df22a
Create Date: 2015-03-04 02:36:13.756101

"""

# revision identifiers, used by Alembic.
revision = '7f435b33664'
down_revision = '19808c5df22a'

from alembic import op
import datetime
import sqlalchemy as sa

TASK_STATE_TABLE = 'midonet_task_state'


def upgrade():
    op.create_table(TASK_STATE_TABLE,
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('last_processed_id', sa.Integer()),
                    sa.Column('updated_at', sa.DateTime(),
                              default=datetime.datetime.utcnow,
                              nullable=False),
                    sa.ForeignKeyConstraint(['last_processed_id'],
                                            ['midonet_tasks.id']))
    op.execute("INSERT INTO %s (id, last_processed_id, updated_at) VALUES"
               " (1, NULL, '%s')" % (TASK_STATE_TABLE,
                                     datetime.datetime.utcnow()))


def downgrade():
    op.drop_table(TASK_STATE_TABLE)
