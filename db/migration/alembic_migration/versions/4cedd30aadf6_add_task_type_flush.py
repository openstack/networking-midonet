"""add task type FLUSH

Revision ID: 4cedd30aadf6
Revises: 25aeae45d4ad
Create Date: 2014-10-29 11:50:24.064368

"""

# revision identifiers, used by Alembic.
revision = '4cedd30aadf6'
down_revision = '25aeae45d4ad'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("INSERT INTO midonet_task_types (id, name) VALUES (4, 'flush')")


def downgrade():
    op.execute("DELETE FROM midonet_task_types WHERE name='flush'")
    pass
