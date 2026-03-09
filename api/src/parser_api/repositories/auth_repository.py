from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from parser_api.db.models import RefreshToken, User


class AuthRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        return await self.db.scalar(stmt)

    async def get_user_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return await self.db.scalar(stmt)

    async def create_user(self, email: str, password_hash: str, full_name: str | None) -> User:
        now = datetime.now(timezone.utc)
        user = User(
            email=email.lower(),
            password_hash=password_hash,
            full_name=full_name.strip() if full_name else None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def update_user_profile(self, user: User, full_name: str | None) -> User:
        user.full_name = full_name.strip() if full_name else None
        user.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return user

    async def add_refresh_token(
        self,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None,
        ip: str | None,
    ) -> RefreshToken:
        now = datetime.now(timezone.utc)
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked_at=None,
            created_at=now,
            user_agent=user_agent,
            ip=ip,
        )
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return await self.db.scalar(stmt)

    async def revoke_refresh_token(self, token: RefreshToken) -> None:
        if token.revoked_at is None:
            token.revoked_at = datetime.now(timezone.utc)
            await self.db.flush()
