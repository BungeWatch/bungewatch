import uuid

from pydantic import BaseModel, ConfigDict

from app.models.user import Language, PreferredChannel


class CreateUserRequest(BaseModel):
    phone_number: str
    channel: PreferredChannel


class UpdateUserRequest(BaseModel):

    name: str | None = None
    email: str | None = None
    preferred_language: Language | None = None


class UserResponse(BaseModel):
    
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phone_number: str
    preferred_channel: PreferredChannel | None
    preferred_language: Language
    name: str | None
    email: str | None
    whatsapp_optin: bool
    is_verified: bool