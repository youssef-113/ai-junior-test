from langchain.tools import StructuredTool
from typing import List
from datetime import datetime , date
from pydantic import BaseModel, Field, validator
from enum import Enum


class BranchName(str, Enum):
    """Available NovaBite branches"""
    NACR_CITY = "nacrCity"
    SHROUQ_CITY = "ShroukCity"


class LoyaltyTier(str, Enum):
    """Loyalty program tiers"""
    BASE = "base"
    PRO = "pro"
    PREMIUM = "premium"

class SpecialEventType(str, Enum):
    """Special event types"""
    BIRTHDAY = "birthday"
    ANNIVERSARY = "anniversary"
    HOLIDAY = "holiday"
    EID_DAY = "EidDay"


class TableSize(str, Enum):
    """Available table sizes"""
    TWO_TOP = "2-top"
    FOUR_TOP = "4-top"
    SIX_TOP = "6-top"

    
class Branch(BaseModel):
    """Restaurant branch information"""
    name: BranchName
    display_name: str
    city: str
    phone: Optional[str] = None
    address: Optional[str] = None

    class Config:
        use_enum_values = False


class SpecialDish(BaseModel):
    """Special dish for a branch"""
    startWith: str = Field(..., alias="startwith")
    endWith: str = Field(..., alias="endwith")
    additional: str

    class Config:
        populate_by_name = True

class MenuItem(BaseModel):
    """Menu item with details"""
    name: str
    description: str
    price: float
    ingredients: List[str] = []
    allergens: List[str] = []
    isVegan: bool = False
    branch: Optional[BranchName] = None


class Plan(BaseModel):
    """Loyalty plan details"""
    tier: LoyaltyTier
    description: str
    discount_percent: int = 0
    benefits: List[str] = []

    class Config:
        use_enum_values = False


class SpecialEvent(BaseModel):
    """Special event offer"""
    event_type: SpecialEventType
    title: str
    description: str
    benefits: List[str] = []

    class Config:
        use_enum_values = False


class LoyaltyUser(BaseModel):
    """User loyalty information"""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    loyaltyPoints: int = 0
    tier: LoyaltyTier = LoyaltyTier.BASE
    totalBookings: int = 0
    joinDate: Optional[date] = None

    class Config:
        use_enum_values = False


class Booking(BaseModel):
    """Table booking record"""
    confirmationID: Optional[str] = None
    userID: str
    guestName: str
    branch: BranchName
    date: str  # Format: yyyy-mm-dd
    time: str  # Format: hh:mm
    partySize: int
    tableSize: Optional[TableSize] = None
    specialOccasion: Optional[SpecialEventType] = None
    notes: Optional[str] = None
    createdAt: Optional[datetime] = None
    status: Literal["confirmed", "cancelled", "completed"] = "confirmed"


    @validator("date")
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in yyyy-mm-dd format")

    @validator("time")
    def validate_time_format(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
            return v
        except ValueError:
            raise ValueError("Time must be in hh:mm format")

    @validator("party_size")
    def validate_party_size(cls, v):
        if v < 1 or v > 12:
            raise ValueError("Party size must be between 1 and 12")
        return v

    class Config:
        use_enum_values = False



class CheckAvailabilityInput(BaseModel):
    """Input schema for check_table_availability tool"""
    date: str = Field(..., description="Date in yyyy-mm-dd format")
    time: str = Field(..., description="Time in hh:mm format (24-hour)")
    branch: BranchName = Field(..., description="Branch name")

    @validator("date")
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in yyyy-mm-dd format")

    @validator("time")
    def validate_time_format(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
            return v
        except ValueError:
            raise ValueError("Time must be in hh:mm format (24-hour)")

    class Config:
        use_enum_values = True

class BookTableInput(BaseModel):
    """Input schema for book_table tool"""
    guestName: str = Field(..., description="Guest name for the reservation")
    userID: str = Field(..., description="Unique user identifier")
    date: str = Field(..., description="Reservation date in yyyy-mm-dd format")
    time: str = Field(..., description="Reservation time in hh:mm format (24-hour)")
    branch: BranchName = Field(..., description="Branch name")
    partySize: int = Field(..., description="Number of guests", ge=1, le=12)
    specialOccasion: Optional[SpecialEventType] = Field(
        None, description="Special occasion type if applicable"
    )
    notes: Optional[str] = Field(None, description="Special requests or notes")

    @validator("date")
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in yyyy-mm-dd format")

    @validator("time")
    def validate_time_format(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
            return v
        except ValueError:
            raise ValueError("Time must be in hh:mm format (24-hour)")

    class Config:
        use_enum_values = True

