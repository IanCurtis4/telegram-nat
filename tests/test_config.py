import pytest
from sqlalchemy import BigInteger


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "token")
    monkeypatch.setenv("ADMIN_ID", "123")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")
    monkeypatch.setenv("DB_ECHO", "true")

    from app.config import Settings

    settings = Settings.from_env()

    assert settings.bot_token == "token"
    assert settings.admin_id == 123
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.db_echo is True


def test_settings_requires_admin_id(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "token")
    monkeypatch.setenv("ADMIN_ID", "0")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")

    from app.config import Settings

    try:
        Settings.from_env()
    except RuntimeError as exc:
        assert "ADMIN_ID" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for invalid ADMIN_ID")


def test_settings_requires_numeric_admin_id(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "token")
    monkeypatch.setenv("ADMIN_ID", "not-a-number")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")

    from app.config import Settings

    with pytest.raises(RuntimeError, match="ADMIN_ID"):
        Settings.from_env()


def test_admin_id_supports_64_bit_values(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "token")
    monkeypatch.setenv("ADMIN_ID", "6541436437")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")

    from app.config import Settings

    settings = Settings.from_env()

    assert settings.admin_id == 6541436437


def test_admin_user_access_guard():
    from app.services.admin import can_access_bot, is_user_blocked

    class DummyUser:
        def __init__(self, blocked: bool):
            self.is_blocked = blocked

    assert is_user_blocked(None) is False
    assert is_user_blocked(DummyUser(False)) is False
    assert is_user_blocked(DummyUser(True)) is True
    assert can_access_bot(None) is False
    assert can_access_bot(DummyUser(False)) is True
    assert can_access_bot(DummyUser(True)) is False


def test_telegram_user_id_model_uses_bigint(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "token")
    monkeypatch.setenv("ADMIN_ID", "123")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")

    from app.database.models import User

    assert isinstance(User.__table__.c.telegram_id.type, BigInteger)


def test_payload_round_trip(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "token")
    monkeypatch.setenv("ADMIN_ID", "123")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")

    from app.services.payments import build_payload, parse_payload

    user_id = 6541436437
    payload = build_payload(product_id=42, user_id=user_id)
    data = parse_payload(payload)

    assert data == {"product_id": 42, "user_id": user_id}
