from unittest.mock import MagicMock
from uuid import uuid4
from app.services import users as user_service


def test_get_or_create_returns_existing():
    db = MagicMock()
    existing = MagicMock(id=uuid4())
    user_service.repo.find_user_by_phone = MagicMock(return_value=existing)

    result = user_service.get_or_create_user(db, "123", "sms")
    assert result is existing
    user_service.repo.create_user.assert_not_called()


def test_get_or_create_creates_when_missing():
    db = MagicMock()
    user_service.repo.find_user_by_phone = MagicMock(return_value=None)
    new_user = MagicMock()
    user_service.repo.create_user = MagicMock(return_value=new_user)

    result = user_service.get_or_create_user(db, "123", "sms")
    assert result is new_user
    user_service.repo.create_user.assert_called_once_with(db, "123", "sms")


def test_update_user_profile_only_passes_provided_fields():
    db = MagicMock()
    user_service.repo.update_user_fields = MagicMock(return_value=MagicMock())

    user_service.update_user_profile(db, uuid4(), name="Ali", email=None, preferred_language="en")

    called_fields = user_service.repo.update_user_fields.call_args[0][2]
    assert called_fields == {"name": "Ali", "preferred_language": "en"}