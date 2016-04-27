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

"""add midonet gateway network vlan devices

Revision ID: 3df8cd6d2ada
Revises: cfe0dea89aa
Create Date: 2016-04-13 07:03:39.557871

"""

# revision identifiers, used by Alembic.
revision = '3df8cd6d2ada'
down_revision = 'cfe0dea89aa'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('midonet_gateway_network_vlan_devices',
                    sa.Column('device_id', sa.String(length=36),
                              nullable=False, primary_key=True),
                    sa.Column('resource_id', sa.String(length=36),
                              nullable=False),
                    sa.ForeignKeyConstraint(['device_id'],
                                            ['midonet_gateway_devices.id'],
                                            ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['resource_id'],
                                            ['networks.id']))
