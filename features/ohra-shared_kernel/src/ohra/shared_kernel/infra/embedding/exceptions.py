from ohra.shared_kernel.domain.exception import DomainException


class EmbeddingException(DomainException):
    pass


class EmbeddingDimensionMismatchException(EmbeddingException):
    pass
