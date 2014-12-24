# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright (C) 2014 Midokura SARL.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Add router service insertion tables

Revision ID: 4105f6d52b82
Revises: 4cedd30aadf6
Create Date: 2014-12-24 19:25:38.042068

"""

# revision identifiers, used by Alembic.
revision = '4105f6d52b82'
down_revision = '4cedd30aadf6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'midonet_servicerouterbindings',
        sa.Column('resource_id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=36), nullable=False),
        sa.Column('router_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['router_id'], [u'routers.id'],
                                name='midonet_servicerouterbindings_ibfk_1'),
        sa.PrimaryKeyConstraint('resource_id', 'resource_type'))
    op.create_table(
        'midonet_routerservicetypebindings',
        sa.Column('router_id', sa.String(length=36), nullable=False),
        sa.Column('service_type_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ['router_id'], ['routers.id'],
            name='midonet_routerservicetypebindings_ibfk_1'),
        sa.PrimaryKeyConstraint(u'router_id'))


def downgrade():
    op.drop_table(u'midonet_routerservicetypebindings')
    op.drop_table(u'midonet_servicerouterbindings')
