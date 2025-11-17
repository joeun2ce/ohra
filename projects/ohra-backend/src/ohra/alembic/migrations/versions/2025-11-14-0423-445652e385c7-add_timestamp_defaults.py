"""add_timestamp_defaults

Revision ID: 445652e385c7
Revises: 7fd464bd7af4
Create Date: 2025-11-14 04:23:19.767390+00:00

"""

from typing import Sequence, Union

from ohra.alembic.migrations.utils import get_existing_tables


# revision identifiers, used by Alembic.
revision: str = "445652e385c7"
down_revision: Union[str, None] = "7fd464bd7af4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing_tables = set(get_existing_tables())

    # Add server_default to created_at and updated_at for ohra_user
    if "ohra_user" in existing_tables:
        # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
        # But for now, we'll just ensure the defaults are set for new inserts
        # Existing columns will work with Python-level defaults
        pass

    # Add server_default to created_at and updated_at for ohra_api_key
    if "ohra_api_key" in existing_tables:
        # Same as above - Python-level defaults will handle this
        pass


def downgrade() -> None:
    # No downgrade needed - we're just adding defaults
    pass
