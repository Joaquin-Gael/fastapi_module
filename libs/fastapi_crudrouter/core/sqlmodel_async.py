from typing import Any, Callable, Coroutine, List, Optional, Type, Union

from fastapi import Depends, HTTPException

from . import CRUDGenerator, NOT_FOUND, _utils
from ._types import DEPENDENCIES, PAGINATION, PYDANTIC_SCHEMA as SCHEMA

try:
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlmodel import SQLModel, select
except ImportError:
    AsyncSession = None  # type: ignore
    IntegrityError = None  # type: ignore
    SQLModel = None  # type: ignore
    select = None  # type: ignore
    sqlmodel_async_installed = False
else:
    sqlmodel_async_installed = True

Model = Type[SQLModel]
CALLABLE = Callable[..., Coroutine[Any, Any, SQLModel]]
CALLABLE_LIST = Callable[..., Coroutine[Any, Any, List[SQLModel]]]


class SQLModelAsyncCRUDRouter(CRUDGenerator[SCHEMA]):
    def __init__(
        self,
        schema: Type[SCHEMA],
        db_model: Model,
        db: Callable[..., AsyncSession],
        create_schema: Optional[Type[SCHEMA]] = None,
        update_schema: Optional[Type[SCHEMA]] = None,
        prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        paginate: Optional[int] = None,
        get_all_route: Union[bool, DEPENDENCIES] = True,
        get_one_route: Union[bool, DEPENDENCIES] = True,
        create_route: Union[bool, DEPENDENCIES] = True,
        update_route: Union[bool, DEPENDENCIES] = True,
        delete_one_route: Union[bool, DEPENDENCIES] = True,
        delete_all_route: Union[bool, DEPENDENCIES] = True,
        **kwargs: Any
    ) -> None:
        assert (
            sqlmodel_async_installed
        ), "SQLModel and SQLAlchemy async must be installed to use the SQLModelAsyncCRUDRouter."

        self.db_model = db_model
        self.db_func = db
        self._pk: str = db_model.__table__.primary_key.columns.keys()[0]
        self._pk_type: type = _utils.get_pk_type(schema, self._pk)

        super().__init__(
            schema=schema,
            create_schema=create_schema,
            update_schema=update_schema,
            prefix=prefix or db_model.__tablename__,
            tags=tags,
            paginate=paginate,
            get_all_route=get_all_route,
            get_one_route=get_one_route,
            create_route=create_route,
            update_route=update_route,
            delete_one_route=delete_one_route,
            delete_all_route=delete_all_route,
            **kwargs
        )

    def _get_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        async def route(
            db: AsyncSession = Depends(self.db_func),
            pagination: PAGINATION = self.pagination,
        ) -> List[SQLModel]:
            skip, limit = pagination.get("skip"), pagination.get("limit")
            statement = (
                select(self.db_model)
                .order_by(getattr(self.db_model, self._pk))
                .offset(skip)
            )

            if limit is not None:
                statement = statement.limit(limit)

            result = await db.execute(statement)
            return result.scalars().all()  # type: ignore

        return route

    def _get_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(
            item_id: self._pk_type,  # type: ignore
            db: AsyncSession = Depends(self.db_func),
        ) -> SQLModel:
            model = await db.get(self.db_model, item_id)

            if model:
                return model
            else:
                raise NOT_FOUND from None

        return route

    def _create(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(
            model: self.create_schema,  # type: ignore
            db: AsyncSession = Depends(self.db_func),
        ) -> SQLModel:
            try:
                db_model = self.db_model(**model.dict())
                db.add(db_model)
                await db.commit()
                await db.refresh(db_model)
                return db_model
            except IntegrityError:
                await db.rollback()
                raise HTTPException(422, "Key already exists") from None

        return route

    def _update(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(
            item_id: self._pk_type,  # type: ignore
            model: self.update_schema,  # type: ignore
            db: AsyncSession = Depends(self.db_func),
        ) -> SQLModel:
            try:
                db_model = await self._get_one()(item_id, db)

                for key, value in model.dict(exclude={self._pk}).items():
                    if hasattr(db_model, key):
                        setattr(db_model, key, value)

                db.add(db_model)
                await db.commit()
                await db.refresh(db_model)
                return db_model
            except IntegrityError as e:
                await db.rollback()
                self._raise(e)

        return route

    def _delete_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        async def route(db: AsyncSession = Depends(self.db_func)) -> List[SQLModel]:
            result = await db.execute(select(self.db_model))

            for db_model in result.scalars().all():
                await db.delete(db_model)

            await db.commit()
            return await self._get_all()(db=db, pagination={"skip": 0, "limit": None})

        return route

    def _delete_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(
            item_id: self._pk_type,  # type: ignore
            db: AsyncSession = Depends(self.db_func),
        ) -> SQLModel:
            db_model = await self._get_one()(item_id, db)
            await db.delete(db_model)
            await db.commit()

            return db_model

        return route
