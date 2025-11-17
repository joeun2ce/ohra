from sqlalchemy import Column, String, Integer, Text, ForeignKey
from ohra.shared_kernel.infra.database.sqla.base import Base, TableNamePrefixMixin
from ohra.shared_kernel.infra.database.sqla.mixin import TimestampColumnMixin


class FeedbackModel(Base, TableNamePrefixMixin, TimestampColumnMixin):
    __tablename__ = "ohra_feedback"

    id = Column(String, primary_key=True)
    message_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=False, default="")
