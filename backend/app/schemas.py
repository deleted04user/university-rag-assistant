from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class FormationBase(BaseModel):
    code: str
    title: str
    description: str = ""
    duration_semesters: int = 6


class FormationCreate(FormationBase):
    pass


class FormationUpdate(BaseModel):
    code: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    duration_semesters: Optional[int] = None


class FormationOut(FormationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HoraireBase(BaseModel):
    module_code: str
    module_name: str
    day_of_week: str
    start_time: time
    end_time: time
    room: str = ""
    teacher: str = ""
    formation_id: Optional[int] = None


class HoraireCreate(HoraireBase):
    pass


class HoraireUpdate(BaseModel):
    module_code: Optional[str] = None
    module_name: Optional[str] = None
    day_of_week: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    room: Optional[str] = None
    teacher: Optional[str] = None
    formation_id: Optional[int] = None


class HoraireOut(HoraireBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UniversityInfoBase(BaseModel):
    category: str
    title: str
    content: str


class UniversityInfoCreate(UniversityInfoBase):
    pass


class UniversityInfoUpdate(BaseModel):
    category: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None


class UniversityInfoOut(UniversityInfoBase):
    id: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatAsk(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatReply(BaseModel):
    answer: str
    intent: str
    recommendations: list[str] = []
    sources: list[str] = []


class AdminUserUpdate(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class StatsSummary(BaseModel):
    total_messages: int
    by_intent: dict[str, int]
    last_7_days: int
