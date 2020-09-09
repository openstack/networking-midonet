# Copyright 2019 Midokura SARL
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

from alembic import op


"""Drop FWaaS v1 and logging_resource

Revision ID: f5dfd5cefbc7
Revises: 1612b5389e6e
Create Date: 2019-02-05 15:51:24.345127

"""

# revision identifiers, used by Alembic.
revision = 'f5dfd5cefbc7'
down_revision = '1612b5389e6e'


def upgrade():
    op.drop_table('midonet_firewall_logs')
    op.drop_table('midonet_logging_resources')
