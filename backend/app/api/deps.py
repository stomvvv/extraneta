from typing import Annotated
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.models.hotel import Hotel, HotelMember
from app.models.user import UserRole

DEMO_USER_EMAIL = "demo@extraneta.ru"


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    result = await db.execute(select(User).where(User.email == DEMO_USER_EMAIL))
    user = result.scalar_one_or_none()
    if not user:
        # Auto-create demo user if missing
        from app.core.security import hash_password
        user = User(
            email=DEMO_USER_EMAIL,
            hashed_password=hash_password("demo1234"),
            full_name="Demo User",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def get_hotel_membership(
    hotel_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HotelMember:
    result = await db.execute(
        select(HotelMember).where(
            HotelMember.hotel_id == hotel_id,
            HotelMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return member


def require_roles(*roles: UserRole):
    async def _check(
        member: Annotated[HotelMember, Depends(get_hotel_membership)],
    ) -> HotelMember:
        if member.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {member.role} cannot perform this action",
            )
        return member
    return _check


CurrentUser = Annotated[User, Depends(get_current_user)]
DB = Annotated[AsyncSession, Depends(get_db)]
