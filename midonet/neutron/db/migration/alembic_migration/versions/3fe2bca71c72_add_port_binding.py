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

"""add port binding

Revision ID: 3fe2bca71c72
Revises: 19808c5df22a
Create Date: 2015-02-16 05:24:01.270141

"""

# revision identifiers, used by Alembic.
revision = '3fe2bca71c72'
down_revision = '19808c5df22a'

from alembic import op
import sqlalchemy as sa


def upgrade():

    op.create_table(
        'midonet_port_bindings',
        sa.Column('port_id', sa.String(length=36), sa.ForeignKey('ports.id'),
                  nullable=False, primary_key=True),
        sa.Column('interface_name', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['port_id'], ['portbindingports.port_id'],
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('port_id'))
