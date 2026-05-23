import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DB, get_hotel_membership, require_roles
from app.models.hotel import Hotel, HotelMember, Invitation
from app.models.user import User, UserRole
from app.schemas.hotel import HotelCreate, HotelUpdate, HotelOut, HotelMemberOut, InviteRequest, AcceptInviteRequest
from app.core.config import settings
from app.core.security import hash_password

router = APIRouter(prefix="/hotels", tags=["hotels"])


@router.post("", response_model=HotelOut, status_code=201)
async def create_hotel(payload: HotelCreate, current_user: CurrentUser, db: DB):
    hotel = Hotel(**payload.model_dump())
    db.add(hotel)
    await db.flush()

    member = HotelMember(hotel_id=hotel.id, user_id=current_user.id, role=UserRole.owner)
    db.add(member)
    await db.commit()
    await db.refresh(hotel)
    return hotel


@router.get("", response_model=list[HotelOut])
async def list_hotels(current_user: CurrentUser, db: DB):
    result = await db.execute(
        select(Hotel)
        .join(HotelMember, HotelMember.hotel_id == Hotel.id)
        .where(HotelMember.user_id == current_user.id)
        .order_by(Hotel.name)
    )
    return result.scalars().all()


@router.get("/{hotel_id}", response_model=HotelOut)
async def get_hotel(hotel_id: UUID, current_user: CurrentUser, db: DB):
    await get_hotel_membership(hotel_id, current_user, db)
    result = await db.execute(select(Hotel).where(Hotel.id == hotel_id))
    hotel = result.scalar_one_or_none()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return hotel


@router.patch("/{hotel_id}", response_model=HotelOut)
async def update_hotel(hotel_id: UUID, payload: HotelUpdate, current_user: CurrentUser, db: DB):
    member = await get_hotel_membership(hotel_id, current_user, db)
    if member.role not in (UserRole.owner, UserRole.manager):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    result = await db.execute(select(Hotel).where(Hotel.id == hotel_id))
    hotel = result.scalar_one_or_none()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(hotel, field, value)
    await db.commit()
    await db.refresh(hotel)
    return hotel


@router.delete("/{hotel_id}", status_code=204)
async def delete_hotel(hotel_id: UUID, current_user: CurrentUser, db: DB):
    member = await get_hotel_membership(hotel_id, current_user, db)
    if member.role != UserRole.owner:
        raise HTTPException(status_code=403, detail="Only owners can delete hotels")

    result = await db.execute(select(Hotel).where(Hotel.id == hotel_id))
    hotel = result.scalar_one_or_none()
    if hotel:
        await db.delete(hotel)
        await db.commit()


@router.get("/{hotel_id}/members", response_model=list[HotelMemberOut])
async def list_members(hotel_id: UUID, current_user: CurrentUser, db: DB):
    await get_hotel_membership(hotel_id, current_user, db)
    result = await db.execute(
        select(HotelMember, User.email, User.full_name)
        .join(User, User.id == HotelMember.user_id)
        .where(HotelMember.hotel_id == hotel_id)
    )
    rows = result.all()
    return [
        HotelMemberOut(
            id=m.id,
            user_id=m.user_id,
            hotel_id=m.hotel_id,
            role=m.role,
            user_email=email,
            user_full_name=full_name,
        )
        for m, email, full_name in rows
    ]


@router.post("/{hotel_id}/invite", status_code=201)
async def invite_member(hotel_id: UUID, payload: InviteRequest, current_user: CurrentUser, db: DB):
    member = await get_hotel_membership(hotel_id, current_user, db)
    if member.role != UserRole.owner:
        raise HTTPException(status_code=403, detail="Only owners can invite members")

    token = secrets.token_urlsafe(32)
    invitation = Invitation(
        hotel_id=hotel_id,
        email=payload.email,
        role=payload.role,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invitation)
    await db.commit()

    invite_url = f"{settings.FRONTEND_URL}/invite/{token}"
    return {"detail": "Invitation created", "invite_url": invite_url, "token": token}


@router.post("/accept-invite")
async def accept_invite(payload: AcceptInviteRequest, db: DB):
    """Public endpoint — no auth required. Accepts an invitation token."""
    result = await db.execute(
        select(Invitation).where(
            Invitation.token == payload.token,
            Invitation.accepted == False,
        )
    )
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found or already used")
    if invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invitation expired")

    # Find or create user from invitation email
    existing = await db.execute(select(User).where(User.email == invitation.email))
    user = existing.scalar_one_or_none()
    if not user:
        if not payload.full_name or not payload.password:
            raise HTTPException(status_code=400, detail="full_name and password required for new users")
        user = User(
            email=invitation.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        await db.flush()

    # Check not already a member
    existing_member = await db.execute(
        select(HotelMember).where(
            HotelMember.hotel_id == invitation.hotel_id,
            HotelMember.user_id == user.id,
        )
    )
    if not existing_member.scalar_one_or_none():
        new_member = HotelMember(hotel_id=invitation.hotel_id, user_id=user.id, role=invitation.role)
        db.add(new_member)

    invitation.accepted = True
    await db.commit()
    return {"detail": "Invitation accepted", "hotel_id": str(invitation.hotel_id)}
