# Copyright 2014 Midokura SARL
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

"""add task type FLUSH

Revision ID: 4cedd30aadf6
Revises: 25aeae45d4ad
Create Date: 2014-10-29 11:50:24.064368

"""

# revision identifiers, used by Alembic.
revision = '4cedd30aadf6'
down_revision = '25aeae45d4ad'

from alembic import op


def upgrade():
    op.execute("INSERT INTO midonet_task_types (id, name) VALUES (4, 'flush')")


def downgrade():
    op.execute("DELETE FROM midonet_task_types WHERE name='flush'")
    pass
