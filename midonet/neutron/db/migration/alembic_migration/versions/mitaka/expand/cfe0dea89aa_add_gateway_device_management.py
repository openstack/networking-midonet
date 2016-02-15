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
"""add gateway device management

Revision ID: cfe0dea89aa
Revises: 4f3b347ea1c2
Create Date: 2015-12-21 11:06:46.155138

"""

# revision identifiers, used by Alembic.
revision = 'cfe0dea89aa'
down_revision = '4f3b347ea1c2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('midonet_gateway_devices',
                    sa.Column('id', sa.String(length=36), primary_key=True),
                    sa.Column('name', sa.String(length=255), nullable=True),
                    sa.Column('type', sa.String(length=255), nullable=False),
                    sa.Column('tenant_id', sa.String(length=255),
                              nullable=True))

    op.create_table('midonet_gateway_hw_vtep_devices',
                    sa.Column('device_id', sa.String(length=36),
                              nullable=False),
                    sa.Column('management_ip', sa.String(length=64),
                              nullable=False, unique=True),
                    sa.Column('management_port', sa.Integer(),
                              nullable=False),
                    sa.Column('management_protocol', sa.String(length=255),
                              nullable=False),
                    sa.ForeignKeyConstraint(['device_id'],
                                            ['midonet_gateway_devices.id'],
                                            ondelete='CASCADE'))

    op.create_table('midonet_gateway_overlay_router_devices',
                    sa.Column('device_id', sa.String(length=36),
                              nullable=False),
                    sa.Column('resource_id', sa.String(length=36),
                              nullable=False),
                    sa.ForeignKeyConstraint(['device_id'],
                                            ['midonet_gateway_devices.id'],
                                            ondelete='CASCADE'))

    op.create_table('midonet_gateway_tunnel_ips',
                    sa.Column('device_id', sa.String(length=36),
                              nullable=False),
                    sa.Column('tunnel_ip', sa.String(length=64),
                              nullable=False, unique=True),
                    sa.ForeignKeyConstraint(['device_id'],
                                            ['midonet_gateway_devices.id'],
                                            ondelete='CASCADE'))

    op.create_table('midonet_gateway_remote_mac_tables',
                    sa.Column('id', sa.String(length=36),
                              primary_key=True),
                    sa.Column('device_id', sa.String(length=36),
                              nullable=False),
                    sa.Column('mac_address', sa.String(length=32),
                              nullable=False, unique=True),
                    sa.Column('vtep_address', sa.String(length=64),
                              nullable=False),
                    sa.Column('segmentation_id', sa.Integer(),
                              nullable=True),
                    sa.ForeignKeyConstraint(['device_id'],
                                            ['midonet_gateway_devices.id'],
                                            ondelete='CASCADE'))
