from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

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
        existing_user = await session.execute(
            User.__table__.select().where(User.username == user_data.username)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        existing_email = await session.execute(
            User.__table__.select().where(User.email == user_data.email)
        )
        if existing_email.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(new_user)
        await session.commit()
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