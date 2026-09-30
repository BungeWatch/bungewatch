from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.services import users as user_service

router = APIRouter(prefix="/users", tags=["users"])


class CreateUserRequest(BaseModel):
    phone_number: str
    channel: str


class UpdateUserRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    preferred_language: str | None = None


@router.post("")
def create_user(payload: CreateUserRequest, db: Session = Depends(get_db)):
    user = user_service.get_or_create_user(db, payload.phone_number, payload.channel)
    return user


@router.patch("/{user_id}")
def update_user(user_id: UUID, payload: UpdateUserRequest, db: Session = Depends(get_db)):
    user = user_service.update_user_profile(
        db, user_id, payload.name, payload.email, payload.preferred_language
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}")
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = user_service.find_user_by_id(db, user_id)  # add this in service too
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user