import uuid
import logging
from dataclasses import dataclass

from ohra.shared_kernel.infra.database.sqla.mixin import AsyncSqlaMixIn
from ohra.backend.rag.entities.feedback import Feedback
from ohra.backend.rag.models.feedback_model import FeedbackModel

logger = logging.getLogger(__name__)


@dataclass
class FeedbackUseCase(AsyncSqlaMixIn):
    def _feedback_to_model(self, feedback: Feedback) -> FeedbackModel:
        return FeedbackModel(
            id=feedback.id,
            message_id=feedback.message_id,
            user_id=feedback.user_id,
            rating=feedback.rating,
            comment=feedback.comment,
        )

    async def execute(self, user_id: str, message_id: str, rating: int, comment: str = "") -> None:
        feedback = Feedback(
            id=str(uuid.uuid4()),
            message_id=message_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
        )
        async with self.db.session() as session:
            feedback_model = self._feedback_to_model(feedback)
            session.add(feedback_model)
            await session.commit()
