from dependency_injector import containers, providers

from ohra.backend.settings import Settings

from ..use_case import AuthUseCase


class AuthContainer(containers.DeclarativeContainer):
    settings = providers.Resource(Settings)

    auth_use_case = providers.Singleton(AuthUseCase)
