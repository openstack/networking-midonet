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

"""create task table

Revision ID: 25aeae45d4ad
Revises: None
Create Date: 2014-10-27 13:26:15.053541

"""

# revision identifiers, used by Alembic.
revision = '25aeae45d4ad'
down_revision = None

from alembic import op
import sqlalchemy as sa


def add_name(table_name, name):
    op.execute("INSERT INTO %s (name) VALUES ('%s')" % (table_name, name))


def add_task_type_name():
    table_name = 'midonet_task_types'
    op.create_table(
        table_name,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),)
    op_list = ['create', 'delete', 'update']
    [add_name(table_name, operation) for operation in op_list]


def add_data_type_name():
    table_name = 'midonet_data_types'
    op.create_table(
        table_name,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),)
    name_list = ['network', 'subnet', 'router', 'port', 'floating_ip',
                 'security_group', 'security_group_rule']
    [add_name(table_name, name) for name in name_list]


def add_task_table():
    op.create_table(
        'midonet_tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('type_id', sa.Integer(), nullable=False),
        sa.Column('data_type_id', sa.Integer()),
        sa.Column('data', sa.Text(length = 2 ** 24)),
        sa.Column('resource_id', sa.String(length=36)),
        sa.Column('transaction_id', sa.String(length=40), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['type_id'], ['midonet_task_types.id'], ),
        sa.ForeignKeyConstraint(['data_type_id'],
                                ['midonet_data_types.id'], ),)


def upgrade():
    add_task_type_name()
    add_data_type_name()
    add_task_table()


def downgrade():
    [op.drop_table(table_name) for table_name in ['midonet_tasks',
                                                  'midonet_task_types',
                                                  'midonet_data_types']]
