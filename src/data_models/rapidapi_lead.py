from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from src.utils.logger import logger

class RapidAPILead(BaseModel):
    lead_id: str = Field(..., description="Unique ID from RapidAPI")
    first_name: str = Field(..., description="Lead's First Name")
    last_name: str = Field(..., description="Lead's Last Name")
    email: EmailStr = Field(..., description="Lead's Email Address")
    phone: Optional[str] = Field(None, description="Lead's Phone Number")
    company: Optional[str] = Field(None, description="Lead's Company Name")
    source: str = Field(..., description="Source of the lead from RapidAPI")

    class Config:
        extra = "ignore"

    @validator("phone", pre=True, allow_reuse=True)
    def format_phone_number(cls, value):
        """Standardize phone number format."""
        if value:
            cleaned_phone = ''.join(filter(str.isdigit, value))
            if len(cleaned_phone) < 7:
                logger.warning(f"RapidAPI: Phone number '{value}' is too short after cleaning.")
                return None
            return cleaned_phone
        return None
