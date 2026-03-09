from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from parser_api.core.config import Settings
from parser_api.db.models import User
from parser_api.repositories.auth_repository import AuthRepository


class AuthError(RuntimeError):
    pass


class AuthenticationFailed(AuthError):
    pass


class ConflictError(AuthError):
    pass


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthService:
    def __init__(self, repository: AuthRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings
        # Use argon2 for new passwords (no bcrypt 72-byte limit),
        # while preserving support for existing bcrypt hashes.
        self.password_ctx = CryptContext(
            schemes=["argon2", "bcrypt_sha256", "bcrypt"],
            deprecated="auto",
        )

    async def register(
        self,
        email: str,
        password: str,
        full_name: str | None,
        user_agent: str | None,
        ip: str | None,
    ) -> tuple[User, AuthTokens]:
        existing = await self.repository.get_user_by_email(email)
        if existing is not None:
            raise ConflictError("User with this email already exists")

        password_hash = self.password_ctx.hash(password)
        user = await self.repository.create_user(email=email, password_hash=password_hash, full_name=full_name)
        tokens = await self._issue_tokens(user=user, user_agent=user_agent, ip=ip)
        await self.repository.db.commit()
        return user, tokens

    async def login(
        self,
        email: str,
        password: str,
        user_agent: str | None,
        ip: str | None,
    ) -> tuple[User, AuthTokens]:
        user = await self.repository.get_user_by_email(email)
        if user is None or not self.password_ctx.verify(password, user.password_hash):
            raise AuthenticationFailed("Invalid email or password")
        if not user.is_active:
            raise AuthenticationFailed("User is deactivated")

        tokens = await self._issue_tokens(user=user, user_agent=user_agent, ip=ip)
        await self.repository.db.commit()
        return user, tokens

    async def refresh(
        self,
        refresh_token: str,
        user_agent: str | None,
        ip: str | None,
    ) -> tuple[User, AuthTokens]:
        token_hash = self.hash_refresh_token(refresh_token)
        stored_token = await self.repository.get_refresh_token(token_hash=token_hash)
        now = datetime.now(timezone.utc)
        if stored_token is None or stored_token.revoked_at is not None or stored_token.expires_at <= now:
            raise AuthenticationFailed("Refresh token is invalid or expired")

        user = await self.repository.get_user_by_id(stored_token.user_id)
        if user is None or not user.is_active:
            raise AuthenticationFailed("User is unavailable")

        await self.repository.revoke_refresh_token(stored_token)
        tokens = await self._issue_tokens(user=user, user_agent=user_agent, ip=ip)
        await self.repository.db.commit()
        return user, tokens

    async def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return

        token_hash = self.hash_refresh_token(refresh_token)
        stored_token = await self.repository.get_refresh_token(token_hash=token_hash)
        if stored_token is not None:
            await self.repository.revoke_refresh_token(stored_token)
            await self.repository.db.commit()

    async def get_user_by_access_token(self, access_token: str) -> User:
        try:
            payload = jwt.decode(
                access_token,
                self.settings.jwt_secret,
                algorithms=[self.settings.jwt_algorithm],
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationFailed("Invalid access token") from exc

        subject = payload.get("sub")
        if not subject:
            raise AuthenticationFailed("Invalid token payload")

        user = await self.repository.get_user_by_id(int(subject))
        if user is None or not user.is_active:
            raise AuthenticationFailed("User not found")
        return user

    async def update_profile(self, user: User, full_name: str | None) -> User:
        updated_user = await self.repository.update_user_profile(user=user, full_name=full_name)
        await self.repository.db.commit()
        return updated_user

    def create_access_token(self, user: User) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self.settings.access_token_ttl_minutes)).timestamp()),
            "type": "access",
        }
        return jwt.encode(payload, self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm)

    def generate_refresh_token(self) -> str:
        return secrets.token_urlsafe(48)

    @staticmethod
    def hash_refresh_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    async def _issue_tokens(
        self,
        user: User,
        user_agent: str | None,
        ip: str | None,
    ) -> AuthTokens:
        access_token = self.create_access_token(user)
        refresh_token = self.generate_refresh_token()
        refresh_hash = self.hash_refresh_token(refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.settings.refresh_token_ttl_days)
        await self.repository.add_refresh_token(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip=ip,
        )
        return AuthTokens(access_token=access_token, refresh_token=refresh_token)
