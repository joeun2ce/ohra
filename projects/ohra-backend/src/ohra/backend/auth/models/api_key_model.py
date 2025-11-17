from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from ohra.shared_kernel.infra.database.sqla.base import Base, TableNamePrefixMixin
from ohra.shared_kernel.infra.database.sqla.mixin import TimestampColumnMixin


class APIKeyModel(Base, TableNamePrefixMixin, TimestampColumnMixin):
    __tablename__ = "ohra_api_key"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("ohra_user.id", ondelete="CASCADE"), nullable=False, index=True)
    key_hash = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (Index("idx_api_key_user_active", "user_id", "is_active"),)
