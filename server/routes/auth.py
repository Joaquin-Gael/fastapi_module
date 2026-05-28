from fastapi import APIRouter, Depends, HTTPException, status

from core import SessionDep
from core.models.base.user import User
from core.spi.base.users import SPIBaseUsers
from core.models.base.user import hasher
from core.auth.keep_secret import get_token, read_token
from core.auth.dependencies import get_current_user, AuthUser

from server.schemas.base.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    CurrentUser,
)

router = APIRouter(prefix="/auth", tags=["Auth"])
spi_users = SPIBaseUsers()


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(request: RegisterRequest, session: SessionDep):
    """Registrar un nuevo usuario"""
    try:
        # Verificar si el usuario ya existe
        existing = await spi_users.get_user_by_email(request.email, session)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado",
            )

        new_user = User(
            name=request.name,
            email=request.email,
            password=request.password,
            active=True,
        )

        created_user = await spi_users.create_user(new_user, session)

        token = await get_token(
            {
                "uid": str(created_user.id),
                "email": created_user.email,
                "name": created_user.name,
            }
        )

        return TokenResponse(access_token=token, token_type="bearer")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar usuario: {str(e)}",
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, session: SessionDep):
    """Iniciar sesión y obtener token"""
    try:
        # Buscar usuario por email
        user = await spi_users.get_user_by_email(request.email, session)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )

        # Verificar password
        try:
            hasher.verify(user.password, request.password)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )

        if not user.active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo"
            )

        # Generar token
        token = await get_token(
            {"uid": str(user.id), "email": user.email, "name": user.name}
        )

        return TokenResponse(access_token=token, token_type="bearer")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar sesión: {str(e)}",
        )


@router.get("/me", response_model=CurrentUser)
async def get_me(current_user: CurrentUser = Depends(get_current_user)):
    """Obtener información del usuario actual"""
    return current_user
