import uuid
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import sqlalchemy as sa

from ohra.shared_kernel.infra.database.sqla.mixin import AsyncSqlaMixIn
from ohra.backend.auth.entities.user import User
from ohra.backend.auth.models.user_model import UserModel
from ohra.backend.auth.models.api_key_model import APIKeyModel
from ohra.backend.auth.dtos.request import APIKeyCreateRequest, WebhookRequest
from ohra.backend.auth import exceptions


@dataclass
class AuthUseCase(AsyncSqlaMixIn):
    async def create_api_key(self, user_id: str, request: APIKeyCreateRequest) -> APIKeyModel:
        api_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        expires_at = datetime.now() + timedelta(days=request.expires_in_days) if request.expires_in_days else None

        async with self.db.session() as session:
            api_key_model = APIKeyModel(
                id=str(uuid.uuid4()),
                user_id=user_id,
                key_hash=key_hash,
                name=request.name,
                expires_at=expires_at,
                is_active=True,
            )
            session.add(api_key_model)
            await session.commit()
            await session.refresh(api_key_model)

        api_key_model.key = api_key
        return api_key_model

    async def validate_api_key(self, api_key: str) -> Optional[User]:
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        async with self.db.session() as session:
            stmt = sa.select(APIKeyModel).where(APIKeyModel.key_hash == key_hash)
            api_key_model = (await session.execute(stmt)).scalar_one_or_none()
            if not api_key_model or not api_key_model.is_active:
                return None
            if api_key_model.expires_at and datetime.now() > api_key_model.expires_at:
                return None

            stmt = sa.select(UserModel).where(UserModel.id == api_key_model.user_id)
            user_model = (await session.execute(stmt)).scalar_one_or_none()
            if not user_model:
                return None

            return self._model_to_user(user_model)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        async with self.db.session() as session:
            stmt = sa.select(UserModel).where(UserModel.email == email)
            user_model = (await session.execute(stmt)).scalar_one_or_none()
            if not user_model:
                return None
            return self._model_to_user(user_model)

    async def get_or_create_user(self, email: str, name: Optional[str] = None) -> User:
        async with self.db.session() as session:
            stmt = sa.select(UserModel).where(UserModel.email == email)
            user_model = (await session.execute(stmt)).scalar_one_or_none()

            if user_model:
                return self._model_to_user(user_model)

            user_model = UserModel(
                id=str(uuid.uuid4()),
                email=email,
                name=name or "unknown",
            )
            session.add(user_model)
            await session.commit()
            await session.refresh(user_model)

            return self._model_to_user(user_model)

    async def revoke_api_key(self, api_key_id: str, user_id: str) -> None:
        async with self.db.session() as session:
            api_key = await session.get(APIKeyModel, api_key_id)
            if not api_key:
                raise exceptions.APIKeyNotFoundException(f"API key with id {api_key_id} not found.")
            if api_key.user_id != user_id:
                raise exceptions.UnauthorizedException("Unauthorized to revoke this API key.")
            api_key.is_active = False
            await session.commit()

    async def get_user_by_external_id(self, external_user_id: str) -> Optional[User]:
        async with self.db.session() as session:
            stmt = sa.select(UserModel).where(UserModel.external_user_id == external_user_id)
            user_model = (await session.execute(stmt)).scalar_one_or_none()
            if not user_model:
                return None
            return self._model_to_user(user_model)

    async def handle_webhook(self, request: WebhookRequest) -> User:
        user_data = request.get_user_data()

        if user_data.id:
            existing = await self.get_user_by_external_id(user_data.id)
            if existing:
                return existing

        async with self.db.session() as session:
            user_model = UserModel(
                id=str(uuid.uuid4()),
                external_user_id=user_data.id,
                email=user_data.email,
                name=user_data.name or user_data.nickname or "unknown",
                is_admin=user_data.role == "admin",
            )
            session.add(user_model)
            await session.commit()
            await session.refresh(user_model)

            return self._model_to_user(user_model)

    async def update_user_last_active(self, external_user_id: str, last_active_at: datetime) -> None:
        async with self.db.session() as session:
            stmt = sa.select(UserModel).where(UserModel.external_user_id == external_user_id)
            user_model = (await session.execute(stmt)).scalar_one_or_none()
            if user_model:
                user_model.updated_at = last_active_at
                await session.commit()

    def _model_to_user(self, user_model: UserModel) -> User:
        return User(
            id=user_model.id,
            external_user_id=user_model.external_user_id,
            email=user_model.email,
            name=user_model.name,
            is_active=user_model.is_active,
            is_admin=user_model.is_admin,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
        )
