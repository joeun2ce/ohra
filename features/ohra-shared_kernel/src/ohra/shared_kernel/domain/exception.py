class DomainException(Exception):
    """Base domain exception"""

    pass


class ValueObjectEnumError(DomainException):
    """Value Object got invalid value"""

    def __str__(self):
        return "Value Object got invalid value."


class EntityNotFoundException(DomainException):
    """Entity not found"""

    pass


class ValidationException(DomainException):
    """Validation failed"""

    pass


class AuthorizationException(DomainException):
    """Authorization failed"""

    pass


class BaseMsgException(Exception):
    """Base message exception (for backward compatibility)"""

    error: str = ""
    message: str = ""
    code: int = 500

    def __str__(self):
        return self.message

    @classmethod
    def create(cls, e: Exception) -> "BaseMsgException":
        model = cls()
        model.error = str(e)
        model.message = getattr(e, "message", "")
        model.code = getattr(e, "code", 500)
        return model
