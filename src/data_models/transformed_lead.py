from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from src.utils.logger import logger

class TransformedLead(BaseModel):
    name: str = Field(..., description="Combined Name for Odoo")
    email: EmailStr = Field(..., description="Lead's Email Address")
    phone: Optional[str] = Field(None, description="Lead's Phone Number")
    partner_name: Optional[str] = Field(None, description="Company Name for Odoo Partner")
    description: Optional[str] = Field(None, description="Lead Description/Source Info")

    @validator("name")
    def check_name_length(cls, value):
        """Validate name length."""
        if len(value.strip()) < 2:
            raise ValueError("Name must be at least 2 characters long after stripping whitespace.")
        return value.strip()

    @validator("phone", pre=True, allow_reuse=True)
    def format_phone_number(cls, value):
        """Standardize phone number format."""
        if value:
            cleaned_phone = ''.join(filter(str.isdigit, value))
            if len(cleaned_phone) < 7:
                logger.warning(f"TransformedLead: Phone number '{value}' is too short after cleaning.")
                return None
            return cleaned_phone
        return cleaned_phone
