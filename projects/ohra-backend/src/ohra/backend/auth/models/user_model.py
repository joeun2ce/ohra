from sqlalchemy import Column, String, Boolean
from ohra.shared_kernel.infra.database.sqla.base import Base, TableNamePrefixMixin
from ohra.shared_kernel.infra.database.sqla.mixin import TimestampColumnMixin


class UserModel(Base, TableNamePrefixMixin, TimestampColumnMixin):
    __tablename__ = "ohra_user"

    id = Column(String, primary_key=True)
    external_user_id = Column(String, nullable=True, unique=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
