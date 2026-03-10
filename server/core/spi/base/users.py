from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.base import User


class SPIBaseUsers:
    def __init__(self, user_class: User = User):
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

    async def get_user_by_id(self, user_id: int, session: AsyncSession):
        try:
            statement = select(self.user_class).where(
                getattr(self.user_class, "id") == user_id
            )
            result = await session.execute(statement)
            return result.scalars().first()
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

    async def delete_user(self, user_id: int, session: AsyncSession):
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
