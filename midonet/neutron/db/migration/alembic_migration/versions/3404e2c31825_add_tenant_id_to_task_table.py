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

"""add tenant id to task table

Revision ID: 3404e2c31825
Revises: 4105f6d52b82
Create Date: 2015-01-20 11:37:02.198076

"""

# revision identifiers, used by Alembic.
revision = '3404e2c31825'
down_revision = '4105f6d52b82'

from alembic import op
import sqlalchemy

TASK_TABLE_NAME = 'midonet_tasks'
TENANT_COL_NAME = 'tenant_id'


def upgrade():
    op.add_column(TASK_TABLE_NAME,
                  sqlalchemy.Column(TENANT_COL_NAME, sqlalchemy.String(255)))
    pass


def downgrade():
    op.drop_column(TASK_TABLE_NAME, TENANT_COL_NAME)
    pass
