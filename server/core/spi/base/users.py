from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from ...models.base import User


class SPIBaseUsers:
    def __init__(self, user_class: type(User) = User):
        self.user_class = user_class

    async def get_user_by_email(self, email: str, session: AsyncSession):
        try:
            statement = select(self.user_class).where(
                getattr(self.user_class, "email") == email
            )
            result = await session.execute(statement)
            return result.scalars().first()
        except Exception as e:
            raise e

    async def get_user_by_username(self, username: str, session: AsyncSession):
        try:
            statement = select(self.user_class).where(
                getattr(self.user_class, "name") == username
            )
            result = await session.execute(statement)
            return result.scalars().first()
        except Exception as e:
            raise e

    async def get_user_by_id(self, user_id: UUID, session: AsyncSession):
        try:
            statement = select(self.user_class).where(
                getattr(self.user_class, "id") == user_id
            )
            result = await session.execute(statement)
            return result.scalars().first()
        except Exception as e:
            raise e

    async def get_users(
        self,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        active: Optional[bool] = None,
    ) -> list[User]:
        """
        Lista usuarios con paginación y filtro opcional por estado.
        """
        try:
            statement = select(self.user_class)

            # Filtrar por estado active si se especifica
            if active is not None:
                statement = statement.where(self.user_class.active == active)

            statement = statement.offset(offset).limit(limit)
            result = await session.execute(statement)
            return list(result.scalars().all())
        except Exception as e:
            raise e

    async def count_users(
        self, session: AsyncSession, active: Optional[bool] = None
    ) -> int:
        """
        Cuenta el total de usuarios, opcionalmente filtrado por estado.
        """
        try:
            statement = select(func.count(self.user_class.id))

            if active is not None:
                statement = statement.where(self.user_class.active == active)

            result = await session.execute(statement)
            return result.scalar() or 0
        except Exception as e:
            raise e

    async def create_user(self, user: User, session: AsyncSession):
        try:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
        except Exception as e:
            raise e

    async def update_user(self, user: User, session: AsyncSession):
        try:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
        except Exception as e:
            raise e

    async def delete_user(self, user_id: UUID, session: AsyncSession):
        try:
            statement = select(self.user_class).where(
                getattr(self.user_class, "id") == user_id
            )
            result = await session.execute(statement)
            user = result.scalars().first()
            if not user:
                raise ValueError("User not found")
            await session.delete(user)
            await session.commit()
            return True
        except Exception as e:
            raise e
