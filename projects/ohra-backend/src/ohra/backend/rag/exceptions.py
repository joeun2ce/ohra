from ohra.shared_kernel.domain.exception import BaseMsgException


class RAGException(BaseMsgException):
    error: str = "RAGError"
    message: str = "RAG processing failed."
    code: int = 500


class EmptyResponseException(RAGException):
    error: str = "EmptyResponse"
    message: str = "LLM returned empty response."
    code: int = 500


class MessageNotFoundException(RAGException):
    error: str = "MessageNotFound"
    message: str = "Message not found."
    code: int = 404


class InvalidMessageRoleException(RAGException):
    error: str = "InvalidMessageRole"
    message: str = "Invalid message role."
    code: int = 400


class EmbeddingException(BaseMsgException):
    error: str = "EmbeddingError"
    message: str = "Embedding processing failed."
    code: int = 500
