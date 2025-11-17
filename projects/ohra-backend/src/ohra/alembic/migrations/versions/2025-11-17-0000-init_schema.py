"""init_schema

Revision ID: init_schema
Revises: 
Create Date: 2025-11-17 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from ohra.alembic.migrations.utils import get_existing_tables


# revision identifiers, used by Alembic.
revision: str = "init_schema"
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
            sa.Column("external_user_id", sa.String(), nullable=True),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
            sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_ohra_user_email", "ohra_user", ["email"], unique=True)
        op.create_index("ix_ohra_user_external_user_id", "ohra_user", ["external_user_id"], unique=True)

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

    # Create ohra_message table
    if "ohra_message" not in existing_tables:
        op.create_table(
            "ohra_message",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("conversation_id", sa.String(), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_ohra_message_conversation_id", "ohra_message", ["conversation_id"])

    # Create ohra_feedback table
    if "ohra_feedback" not in existing_tables:
        op.create_table(
            "ohra_feedback",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("message_id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("rating", sa.Integer(), nullable=False),
            sa.Column("comment", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_ohra_feedback_message_id", "ohra_feedback", ["message_id"])
        op.create_index("ix_ohra_feedback_user_id", "ohra_feedback", ["user_id"])


def downgrade() -> None:
    existing_tables = set(get_existing_tables())

    if "ohra_feedback" in existing_tables:
        op.drop_index("ix_ohra_feedback_user_id", table_name="ohra_feedback")
        op.drop_index("ix_ohra_feedback_message_id", table_name="ohra_feedback")
        op.drop_table("ohra_feedback")

    if "ohra_message" in existing_tables:
        op.drop_index("ix_ohra_message_conversation_id", table_name="ohra_message")
        op.drop_table("ohra_message")

    if "ohra_api_key" in existing_tables:
        op.drop_index("idx_api_key_user_active", table_name="ohra_api_key")
        op.drop_index("ix_ohra_api_key_key_hash", table_name="ohra_api_key")
        op.drop_index("ix_ohra_api_key_user_id", table_name="ohra_api_key")
        op.drop_table("ohra_api_key")

    if "ohra_user" in existing_tables:
        op.drop_index("ix_ohra_user_external_user_id", table_name="ohra_user")
        op.drop_index("ix_ohra_user_email", table_name="ohra_user")
        op.drop_table("ohra_user")

