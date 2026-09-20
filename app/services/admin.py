from __future__ import annotations

from typing import Any

from app.config import get_settings


def is_admin(user_id: int | None) -> bool:
    if user_id is None:
        return False
    return user_id == get_settings().admin_id


def is_user_blocked(user: Any | None) -> bool:
    if user is None:
        return False
    try:
        return bool(getattr(user, "is_blocked", False))
    except (AttributeError, TypeError):
        return False


def can_access_bot(user: Any | None) -> bool:
    if user is None:
        return False
    return not is_user_blocked(user)


def require_admin(user_id: int | None) -> None:
    if not is_admin(user_id):
        raise PermissionError("Access denied: admin only")
