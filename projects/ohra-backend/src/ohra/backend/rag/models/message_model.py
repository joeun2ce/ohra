from sqlalchemy import Column, String, Text
from ohra.shared_kernel.infra.database.sqla.base import Base, TableNamePrefixMixin
from ohra.shared_kernel.infra.database.sqla.mixin import TimestampColumnMixin


class MessageModel(Base, TableNamePrefixMixin, TimestampColumnMixin):
    __tablename__ = "ohra_message"

    id = Column(String, primary_key=True)
    conversation_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
