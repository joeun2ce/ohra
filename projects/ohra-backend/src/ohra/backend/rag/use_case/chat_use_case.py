import uuid
import logging
from dataclasses import dataclass

from ohra.shared_kernel.infra.database.sqla.mixin import AsyncSqlaMixIn
from ohra.backend.rag.service.v1.pipeline import LangchainRAGAnalyzer
from ohra.backend.rag.dtos.request import ChatCompletionRequest
from ohra.backend.rag.dtos.response import ChatCompletionResponse
from ohra.backend.rag.entities.message import Message
from ohra.backend.rag.models.message_model import MessageModel
from ohra.backend.rag import exceptions

logger = logging.getLogger(__name__)


@dataclass
class ChatCompletionUseCase(AsyncSqlaMixIn):
    analyzer: LangchainRAGAnalyzer

    def _message_to_model(self, message: Message) -> MessageModel:
        return MessageModel(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
        )

    async def execute(self, user_id: str, request: ChatCompletionRequest) -> ChatCompletionResponse:
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            raise exceptions.InvalidMessageRoleException("No user message found in request")

        response = await self.analyzer.ainvoke(request)

        if response.choices:
            response_text = response.choices[0].message.content

            if response_text:
                conversation_id = request.user or str(uuid.uuid4())
                assistant_message = Message(
                    id=f"msg_{uuid.uuid4()}",
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response_text,
                )

                async with self.db.session() as session:
                    message_model = self._message_to_model(assistant_message)
                    session.add(message_model)
                    await session.commit()

        return response
