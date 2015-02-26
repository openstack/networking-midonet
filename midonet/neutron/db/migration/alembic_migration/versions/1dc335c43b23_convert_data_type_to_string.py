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

"""convert data_type to string

Revision ID: 1dc335c43b23
Revises: 3fe2bca71c72
Create Date: 2015-02-24 08:13:42.045448

"""

# revision identifiers, used by Alembic.
revision = '1dc335c43b23'
down_revision = '3fe2bca71c72'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy import select


old_task = sa.Table('midonet_tasks', sa.MetaData(),
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('data_type_id', sa.Integer(),
                              sa.ForeignKey('midonet_data_types.id')),
                    sa.Column('data_type', sa.String(length=36)),
                    sa.Column('type_id', sa.Integer(),
                              sa.ForeignKey('midonet_task_types.id')),
                    sa.Column('type', sa.String(length=36)))

data_type = sa.Table('midonet_data_types', sa.MetaData(),
                    sa.Column('id', sa.Integer()),
                    sa.Column('name', sa.String(length=36)))

task_type = sa.Table('midonet_task_types', sa.MetaData(),
                    sa.Column('id', sa.Integer()),
                    sa.Column('name', sa.String(length=36)))


def upgrade():
    def add_col(name):
        op.add_column('midonet_tasks', sa.Column(name, sa.String(length=36)))

    def drop_table(name):
        fkey = {'type_id': 'midonet_tasks_ibfk_1',
                'data_type_id': 'midonet_tasks_ibfk_2'}
        table_name = {'type_id': 'midonet_task_types',
                      'data_type_id': 'midonet_data_types'}

        op.drop_constraint(fkey[name], 'midonet_tasks', type_='foreignkey')
        op.drop_column('midonet_tasks', name)
        op.drop_table(table_name[name])

    [add_col(name) for name in ['data_type', 'type']]

    type_sel = select([task_type.c.name]).\
        where(old_task.c.type_id == task_type.c.id).\
        as_scalar()
    op.execute(old_task.update().values(type=func.upper(type_sel)))

    dt_sel = select([data_type.c.name]).\
        where(old_task.c.data_type_id == data_type.c.id).\
        as_scalar()
    op.execute(old_task.update().values(data_type=func.upper(dt_sel)))

    [drop_table(name) for name in ['type_id', 'data_type_id']]


def downgrade():

    def add_name(table_name, name):
        op.execute("INSERT INTO %s (name) VALUES ('%s')" % (table_name, name))

    def add_task_type_name_table():
        table_name = 'midonet_task_types'
        op.create_table(
            table_name,
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('name', sa.String(50), nullable=False),)
        op_list = ['create', 'delete', 'update', 'flush']
        [add_name(table_name, operation) for operation in op_list]

    def add_data_type_name_table():
        table_name = 'midonet_data_types'
        op.create_table(
            table_name,
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('name', sa.String(50), nullable=False),)
        name_list = ['network', 'subnet', 'router', 'port', 'floating_ip',
                 'security_group', 'security_group_rule', 'pool', 'vip',
                 'health_monitor', 'member', 'port_binding']
        [add_name(table_name, name) for name in name_list]

    add_task_type_name_table()
    op.add_column('midonet_tasks',
                  sa.Column('type_id', sa.Integer(),
                            sa.ForeignKey('midonet_task_types.id')))

    add_data_type_name_table()
    op.add_column('midonet_tasks',
                  sa.Column('data_type_id', sa.Integer(),
                  sa.ForeignKey('midonet_data_types.id')))

    type_sel = select([task_type.c.id]).\
        where(old_task.c.type == func.upper(task_type.c.name)).\
        as_scalar()
    op.execute(old_task.update().values(type_id=type_sel))

    data_sel = select([data_type.c.id]).\
        where(old_task.c.data_type == func.upper(data_type.c.name)).\
        as_scalar()
    op.execute(old_task.update().values(data_type_id=data_sel))

    [op.drop_column('midonet_tasks', name) for name in ['type',
                                                        'data_type']]
