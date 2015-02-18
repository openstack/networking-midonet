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
"""add binding task

Revision ID: 3fe2bca71c72
Revises: 3404e2c31825
Create Date: 2015-02-16 05:24:01.270141

"""

PORT_BINDING_TABLE_NAME = 'midonet_port_binding'

# revision identifiers, used by Alembic.
revision = '3fe2bca71c72'
down_revision = '3404e2c31825'

from alembic import op
import sqlalchemy as sa


def add_port_binding_table():
    op.create_table(
        PORT_BINDING_TABLE_NAME,
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('port_id', sa.String(length=36), nullable=False),
        sa.Column('host_id', sa.String(length=36), nullable=False),
        sa.Column('interface_name', sa.String(length=16), nullable=False))


def add_binding_data_type():
    op.execute("INSERT INTO midonet_data_types "
               "(id, name) ""VALUES (12, 'port_binding')")


def drop_port_binding_table():
    op.drop_table(PORT_BINDING_TABLE_NAME)


def remove_binding_data_type():
    op.execute("DELETE FROM midonet_data_types WHERE name='port_binding'")


def upgrade():
    add_port_binding_table()
    add_binding_data_type()


def downgrade():
    remove_binding_data_type()
    drop_port_binding_table()
