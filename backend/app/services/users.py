from uuid import UUID
from sqlalchemy.orm import Session
from app.repository import users_repository as repo
from app.models.user import User

def get_or_create_user(db: Session, phone_number: str, channel: str) -> User:
    user = repo.find_user_by_phone(db, phone_number)
    if user:
        return user
    return repo.create_user(db, phone_number, channel)

def update_user_profile(
    db: Session,
    user_id: UUID,
    name: str | None = None,
    email: str | None = None,
    preferred_language: str | None = None,
) -> User:
    fields = {}
    if name is not None:
        fields["name"] = name
    if email is not None:
        fields["email"] = email
    if preferred_language is not None:
        fields["preferred_language"] = preferred_language

    return repo.update_user_fields(db, user_id, fields)