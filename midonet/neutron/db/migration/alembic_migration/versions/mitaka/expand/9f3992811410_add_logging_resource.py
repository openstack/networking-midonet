# Copyright 2016 Midokura SARL
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

"""add logging resource

Revision ID: 9f3992811410
Revises: f8b289f2644f
Create Date: 2016-06-06 09:39:35.381427

"""

from alembic import op
import sqlalchemy as sa

from neutron.db import migration


# revision identifiers, used by Alembic.
revision = '9f3992811410'
down_revision = 'f8b289f2644f'

# milestone identifier, used by neutron-db-manage
neutron_milestone = [
    migration.MITAKA, migration.NEWTON, migration.OCATA,
    migration.PIKE
]


def upgrade():
    op.create_table('midonet_logging_resources',
                    sa.Column('id', sa.String(length=36), primary_key=True),
                    sa.Column('name', sa.String(length=255), nullable=True),
                    sa.Column('description', sa.String(length=1024),
                              nullable=True),
                    sa.Column('tenant_id', sa.String(length=255),
                              nullable=True),
                    sa.Column('enabled', sa.Boolean(), nullable=False))

    op.create_table('midonet_firewall_logs',
                    sa.Column('id', sa.String(length=36), primary_key=True),
                    sa.Column('logging_resource_id', sa.String(length=36),
                              nullable=False),
                    sa.Column('tenant_id', sa.String(length=255),
                              nullable=True),
                    sa.Column('description', sa.String(length=1024),
                              nullable=True),
                    sa.Column('fw_event', sa.String(length=255),
                              nullable=False),
                    sa.Column('firewall_id', sa.String(length=36),
                              nullable=False),
                    sa.ForeignKeyConstraint(['logging_resource_id'],
                                            ['midonet_logging_resources.id'],
                                            ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['firewall_id'],
                                            ['firewalls.id'],
                                            ondelete='CASCADE'))
