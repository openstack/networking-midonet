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

"""add foreign key constraint on gateway device

Revision ID: 7234c9979bf2
Revises: 143b26cc5196
Create Date: 2016-04-12 10:32:00.698251

"""

from alembic import op

from neutron.db import migration


# revision identifiers, used by Alembic.
revision = '7234c9979bf2'
down_revision = '143b26cc5196'
depends_on = ('cfe0dea89aa',)

# milestone identifier, used by neutron-db-manage
neutron_milestone = [migration.MITAKA]


def upgrade():
    op.create_foreign_key(
        constraint_name=None,
        source_table='midonet_gateway_overlay_router_devices',
        referent_table='routers',
        local_cols=['resource_id'],
        remote_cols=['id'])
