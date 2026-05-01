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
