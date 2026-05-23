from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from app.models.user import UserRole


class HotelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    room_count: Optional[int] = Field(None, gt=0)
    expected_commission_rates: dict[str, float] = Field(default_factory=dict)
    currency: str = Field("RUB", max_length=3)
    timezone: str = Field("Europe/Moscow", max_length=50)


class HotelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    room_count: Optional[int] = Field(None, gt=0)
    expected_commission_rates: Optional[dict[str, float]] = None
    currency: Optional[str] = Field(None, max_length=3)
    timezone: Optional[str] = Field(None, max_length=50)


class HotelOut(BaseModel):
    id: UUID
    name: str
    room_count: Optional[int]
    expected_commission_rates: dict
    currency: str
    timezone: str

    model_config = {"from_attributes": True}


class HotelMemberOut(BaseModel):
    id: UUID
    user_id: UUID
    hotel_id: UUID
    role: UserRole
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None

    model_config = {"from_attributes": True}


class InviteRequest(BaseModel):
    email: str
    role: UserRole = UserRole.manager


class AcceptInviteRequest(BaseModel):
    token: str
    full_name: Optional[str] = None
    password: Optional[str] = None
