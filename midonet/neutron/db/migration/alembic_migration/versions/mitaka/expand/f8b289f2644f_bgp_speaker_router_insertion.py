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

"""bgp speaker router insertion

Revision ID: f8b289f2644f
Revises: 3df8cd6d2ada
Create Date: 2016-05-13 10:14:14.939657

"""

# revision identifiers, used by Alembic.
revision = 'f8b289f2644f'
down_revision = '3df8cd6d2ada'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'bgp_speaker_router_associations',
        sa.Column('bgp_speaker_id', sa.String(length=36), nullable=False),
        sa.Column('router_id', sa.String(length=36), nullable=False,
                  unique=True),
        sa.ForeignKeyConstraint(
            ['bgp_speaker_id'], ['bgp_speakers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['router_id'], ['routers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('bgp_speaker_id'))
