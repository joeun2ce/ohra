"""seed_admin_user

Revision ID: seed_admin_user
Revises: init_schema
Create Date: 2025-11-17 00:00:01.000000+00:00

"""

from typing import Sequence, Union

from alembic import op
from ohra.alembic.migrations.utils import create_admin_user_if_not_exists


# revision identifiers, used by Alembic.
revision: str = "seed_admin_user"
down_revision: Union[str, None] = "init_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create admin user if it doesn't exist."""
    create_admin_user_if_not_exists()


def downgrade() -> None:
    """Remove admin user if needed.

    Note: This is intentionally left empty to avoid accidental data loss.
    If you need to remove the admin user, do it manually or implement
    a safe removal logic here.
    """
    pass
