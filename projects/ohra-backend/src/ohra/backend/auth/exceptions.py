from ohra.shared_kernel.domain.exception import BaseMsgException


class AuthException(BaseMsgException):
    error: str = ""
    message: str = ""
    code: int = 500


class APIKeyNotFoundException(AuthException):
    error: str = "APIKeyNotFound"
    message: str = "API key not found."
    code: int = 404


class UnauthorizedException(AuthException):
    error: str = "Unauthorized"
    message: str = "Unauthorized to perform this action."
    code: int = 403
