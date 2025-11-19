import os
import uuid
from alembic import op
from sqlalchemy import Inspector
import sqlalchemy as sa


def get_existing_tables() -> list[str]:
    con = op.get_bind()
    inspector = Inspector.from_engine(con)
    response = []
    response.extend(inspector.get_table_names())
    response.extend(get_existing_mv())
    return response


def get_existing_mv() -> list[str]:
    con = op.get_bind()
    inspector = Inspector.from_engine(con)
    response = []
    # response.extend(inspector.get_materialized_view_names())
    response.extend(inspector.get_view_names())
    return response


def get_revision_id():
    return str(uuid.uuid4()).replace("-", "")[:12]


def create_admin_user_if_not_exists(
    admin_email: str | None = None,
    admin_name: str | None = None,
    admin_external_id: str | None = None,
) -> None:
    """Create admin user if it doesn't exist, or update external_id if exists.

    Args:
        admin_email: Admin user email. If None, reads from OHRA_ADMIN_EMAIL env var.
        admin_name: Admin user name. If None, reads from OHRA_ADMIN_NAME env var.
        admin_external_id: Admin user external_id. If None, reads from OHRA_ADMIN_EXTERNAL_ID env var.
    """
    connection = op.get_bind()

    admin_email = admin_email or os.getenv("OHRA_ADMIN_EMAIL", "admin@ohra.local")
    admin_name = admin_name or os.getenv("OHRA_ADMIN_NAME", "Admin")
    admin_external_id = admin_external_id or os.getenv("OHRA_ADMIN_EXTERNAL_ID")

    # Check if admin user already exists
    result = connection.execute(
        sa.text("SELECT id, external_user_id FROM ohra_user WHERE email = :email"), {"email": admin_email}
    ).fetchone()

    if result is None:
        # Create new admin user
        admin_id = str(uuid.uuid4())
        connection.execute(
            sa.text("""
                INSERT INTO ohra_user (id, email, name, is_admin, external_user_id)
                VALUES (:id, :email, :name, :is_admin, :external_user_id)
            """),
            {
                "id": admin_id,
                "email": admin_email,
                "name": admin_name,
                "is_admin": True,
                "external_user_id": admin_external_id,
            },
        )
        connection.commit()
    elif admin_external_id and result[1] != admin_external_id:
        # Update external_id if provided and different
        connection.execute(
            sa.text("""
                UPDATE ohra_user 
                SET external_user_id = :external_user_id
                WHERE id = :id
            """),
            {
                "id": result[0],
                "external_user_id": admin_external_id,
            },
        )
        connection.commit()


def run():
    print("********** Running migrations... **********")
    try:
        from alembic import command
        from alembic.config import Config

        print(os.getcwd())
        alembic_cfg = Config("alembic.ini")

        # Set the script location dynamically
        # migrations_path = "src/migration"
        # alembic_cfg.set_main_option("script_location", str(migrations_path))
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("********** migrations complete **********")
