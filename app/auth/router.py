from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.auth.models import User
from app.auth.schemas import UserCreate, UserRead, UserLogin, Token
from app.auth.utils import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_active_user
)
from app.database import async_session_maker

router = APIRouter(prefix="/auth", tags=["Authorization"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    async with async_session_maker() as session:
        async with session.begin():
            # Быстрая «оптимистичная» проверка для нормального UX с понятным detail.
            # Реальная защита от гонки — IntegrityError ниже (unique-индексы).
            if await session.scalar(
                select(User).where(User.username == user_data.username)
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered",
                )
            if await session.scalar(
                select(User).where(User.email == user_data.email)
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )

            new_user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=get_password_hash(user_data.password),
            )
            session.add(new_user)
            try:
                # flush пушит INSERT в БД внутри открытой транзакции.
                # На уникальных индексах получим IntegrityError здесь, а не на commit,
                # и можем превратить её в нормальный 400.
                await session.flush()
            except IntegrityError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username or email already registered",
                )

        # session.begin() делает commit при выходе (если не было исключения).
        await session.refresh(new_user)
        return new_user


@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: UserLogin):
    async with async_session_maker() as session:
        user = await authenticate_user(form_data.username, form_data.password, session)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(data={"sub": str(user.id)})
        return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user