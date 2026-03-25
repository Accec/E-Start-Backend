import re
from typing import Optional

from pydantic import BaseModel
from sanic_ext.exceptions import ValidationError


ACCOUNT_PATTERN = re.compile(r"^[a-zA-Z0-9]+$")
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,15}$")


class PermissionRef(BaseModel):
    id: Optional[int] = None
    permission_title: Optional[str] = None


class RoleRef(BaseModel):
    id: Optional[int] = None
    role_name: Optional[str] = None


def validate_account_value(value: str):
    if not ACCOUNT_PATTERN.match(value):
        raise ValidationError(message="Account should only contain alphanumeric characters.")
    return value


def validate_password_value(value: str):
    if not PASSWORD_PATTERN.match(value):
        raise ValidationError(
            message="Password must be 8-15 characters long, include at least one uppercase letter, one lowercase letter, one number, and one special character."
        )
    return value
