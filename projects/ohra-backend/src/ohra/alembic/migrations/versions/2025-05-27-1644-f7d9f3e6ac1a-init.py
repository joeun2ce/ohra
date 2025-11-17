# projects/ohra-backend/src/ohra/alembic/migrations/versions/2025-05-27-1644-f7d9f3e6ac1a-init.py
"""init

Revision ID: f7d9f3e6ac1a
Revises:
Create Date: 2025-05-27 16:44:14.958849+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from ohra.alembic.migrations.utils import get_existing_tables

# revision identifiers, used by Alembic.
revision: str = "f7d9f3e6ac1a"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing_tables = set(get_existing_tables())

    # Create ohra_user table
    if "ohra_user" not in existing_tables:
        op.create_table(
            "ohra_user",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
            sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_ohra_user_email", "ohra_user", ["email"], unique=True)

    # Create ohra_api_key table
    if "ohra_api_key" not in existing_tables:
        op.create_table(
            "ohra_api_key",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("key_hash", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["user_id"], ["ohra_user.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_ohra_api_key_user_id", "ohra_api_key", ["user_id"])
        op.create_index("ix_ohra_api_key_key_hash", "ohra_api_key", ["key_hash"], unique=True)
        op.create_index("idx_api_key_user_active", "ohra_api_key", ["user_id", "is_active"])


def downgrade() -> None:
    existing_tables = set(get_existing_tables())

    if "ohra_api_key" in existing_tables:
        op.drop_table("ohra_api_key")

    if "ohra_user" in existing_tables:
        op.drop_table("ohra_user")
