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

"""add dynamic routing

Revision ID: 421564f630b1
Revises: 3fe2bca71c72
Create Date: 2015-03-31 04:40:24.533580

"""

# revision identifiers, used by Alembic.
revision = '421564f630b1'
down_revision = '3fe2bca71c72'

from alembic import op
import sqlalchemy as sa


def upgrade():

    op.create_table(
        'midonet_routing_instances',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('router_id', sa.String(length=36), nullable=False),
        sa.Column('local_as', sa.Integer(), nullable=False),
        sa.Column('protocol', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['router_id'], ['routers.id']))

    op.create_table(
        'midonet_routing_peers',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('routing_instance_id', sa.String(length=36),
                  nullable=False),
        sa.Column('port_id', sa.String(length=36), nullable=False),
        sa.Column('peer_as', sa.Integer(), nullable=False),
        sa.Column('peer_address', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['routing_instance_id'],
                                ['midonet_routing_instances.id']),
        sa.ForeignKeyConstraint(['port_id'], ['ports.id']))

    op.create_table(
        'midonet_advertise_route',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('routing_instance_id', sa.String(length=36),
                  nullable=False),
        sa.Column('destination', sa.String(length=36),
                  nullable=False),
        sa.ForeignKeyConstraint(['routing_instance_id'],
                                ['midonet_routing_instances.id']))
