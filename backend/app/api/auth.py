from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from ..schemas.user import UserCreate, UserRead
from ..models.user import User
from ..core.security import hash_password, verify_password, create_access_token
from ..deps import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=UserRead, status_code=201)
async def signup(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    if await db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(400, "Email already registered")

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login")
async def login(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email == payload.email))
    user: User | None = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Bad credentials")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
