"""add external_user_id

Revision ID: 7fd464bd7af4
Revises: f7d9f3e6ac1a
Create Date: 2025-01-27 00:00:00.000000+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from ohra.alembic.migrations.utils import get_existing_tables

# revision identifiers, used by Alembic.
revision: str = "7fd464bd7af4"
down_revision: Union[str, None] = "f7d9f3e6ac1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing_tables = set(get_existing_tables())

    # Add external_user_id column to ohra_user table
    if "ohra_user" in existing_tables:
        op.add_column("ohra_user", sa.Column("external_user_id", sa.String(), nullable=True))
        # Create unique index on external_user_id
        op.create_index("ix_ohra_user_external_user_id", "ohra_user", ["external_user_id"], unique=True)


def downgrade() -> None:
    existing_tables = set(get_existing_tables())

    # Remove external_user_id column from ohra_user table
    if "ohra_user" in existing_tables:
        op.drop_index("ix_ohra_user_external_user_id", table_name="ohra_user")
        op.drop_column("ohra_user", "external_user_id")
