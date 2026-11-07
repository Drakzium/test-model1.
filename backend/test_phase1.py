"""Quick authentication and hosted chat checks. Run from the backend folder."""

import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import User

client = TestClient(app)


def main() -> None:
    health = client.get("/api/health")
    assert health.status_code == 200, health.text

    email = f"phase1-{uuid.uuid4().hex[:8]}@example.com"
    password = "strongpass1"
    register = client.post(
        "/api/auth/register",
        json={"email": email, "display_name": "Fakhir", "password": password},
    )
    assert register.status_code == 200, register.text
    recovery = register.json()["recovery_code"]
    assert recovery

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["display_name"] == "Fakhir"

    status = client.get("/api/system/status")
    assert status.status_code == 200
    assert status.json()["phase"] == 2
    model_status = client.get("/api/chat/model")
    assert model_status.status_code == 200
    assert model_status.json()["provider"] == "OpenAI-compatible hosted API"

    with patch("app.routers.chat.generate_reply", return_value="A helpful test response.") as generate:
        chat = client.post("/api/chat/messages", json={"content": "Help me plan my week."})
    assert chat.status_code == 200, chat.text
    chat_turn = chat.json()
    conversation_id = chat_turn["conversation"]["id"]
    assert len(chat_turn["messages"]) == 2
    assert chat_turn["messages"][0]["role"] == "user"
    assert chat_turn["messages"][1]["content"] == "A helpful test response."
    assert generate.call_args.args[0][-1] == {
        "role": "user",
        "content": "Help me plan my week.",
    }

    history = client.get(f"/api/chat/conversations/{conversation_id}/messages")
    assert history.status_code == 200
    assert len(history.json()) == 2
    assert client.get("/api/chat/conversations").json()[0]["id"] == conversation_id

    other_user = TestClient(app)
    other_email = f"phase1-{uuid.uuid4().hex[:8]}@example.com"
    other_register = other_user.post(
        "/api/auth/register",
        json={"email": other_email, "display_name": "Other", "password": password},
    )
    assert other_register.status_code == 200, other_register.text
    assert other_user.get(f"/api/chat/conversations/{conversation_id}/messages").status_code == 404
    assert other_user.get("/api/chat/conversations").json() == []

    deleted = client.delete(f"/api/chat/conversations/{conversation_id}")
    assert deleted.status_code == 204, deleted.text
    assert client.get(f"/api/chat/conversations/{conversation_id}/messages").status_code == 404

    profile = client.patch("/api/users/me", json={"display_name": "Owner"})
    assert profile.status_code == 200
    assert profile.json()["display_name"] == "Owner"

    logs = client.get("/api/logs")
    assert logs.status_code == 200
    assert len(logs.json()) >= 1

    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/chat/conversations").status_code == 401

    reset = client.post(
        "/api/auth/forgot-password",
        json={"email": email, "recovery_code": recovery.lower(), "new_password": "newpass123"},
    )
    assert reset.status_code == 200, reset.text

    login = client.post("/api/auth/login", json={"email": email, "password": "newpass123"})
    assert login.status_code == 200, login.text

    password_change = client.post(
        "/api/auth/change-password",
        json={"current_password": "newpass123", "new_password": "finalpass456", "confirm_password": "finalpass456"},
    )
    assert password_change.status_code == 200, password_change.text

    re_login = client.post("/api/auth/login", json={"email": email, "password": "finalpass456"})
    assert re_login.status_code == 200, re_login.text

    with SessionLocal() as db:
        for test_user in db.query(User).filter(User.email.in_([email, other_email])).all():
            db.delete(test_user)
        db.commit()

    print("Backend authentication and chat checks passed.")


if __name__ == "__main__":
    main()
