from uuid import UUID
from sqlalchemy.orm import Session
from app.models.user import User

def find_user_by_phone(db: Session, phone_number: str) -> User | None:
    return db.query(User).filter(User.phone_number == phone_number).first()

def create_user(db: Session, phone_number: str, preferred_channel: str) -> User:
    user = User(phone_number=phone_number, preferred_channel=preferred_channel)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def find_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

def update_user_fields(db: Session, user_id: UUID, fields: dict) -> User:
    user = find_user_by_id(db, user_id)
    if not user:
        return None
    for key, value in fields.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: UUID) -> None:
    user = find_user_by_id(db, user_id)
    if user:
        db.delete(user)
        db.commit()