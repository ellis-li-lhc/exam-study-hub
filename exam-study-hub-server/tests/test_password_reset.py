from unittest import TestCase
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import verify_password
from app.crud.user import create_user
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import PasswordResetCode, User


class PasswordResetTest(TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        def override_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_db
        self.turnstile_patch = patch(
            "app.routers.auth.verify_turnstile",
            new=AsyncMock(return_value=True),
        )
        self.mail_mock = AsyncMock(return_value=None)
        self.mail_patch = patch(
            "app.routers.auth.send_password_reset_email",
            new=self.mail_mock,
        )
        self.turnstile_patch.start()
        self.mail_patch.start()
        with self.Session() as db:
            create_user(db, "reset-student", "old-pass", "reset@qq.com")
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.mail_patch.stop()
        self.turnstile_patch.stop()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def send_code(self) -> str:
        response = self.client.post(
            "/api/auth/password-reset/code",
            json={"email": "RESET@qq.com", "turnstile_token": "valid-token"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["data"]["resend_after"], 60)
        return self.mail_mock.await_args_list[-1].args[1]

    def test_registered_email_can_reset_password_and_old_password_stops_working(self):
        old_session = self.client.post(
            "/api/auth/login",
            json={"username": "reset-student", "password": "old-pass"},
        )
        self.assertEqual(old_session.status_code, 200, old_session.text)
        old_token = old_session.json()["data"]["access_token"]

        code = self.send_code()
        response = self.client.post(
            "/api/auth/password-reset",
            json={
                "email": "reset@qq.com",
                "verification_code": code,
                "new_password": "new-secure-pass",
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["data"]["reset"])
        with self.Session() as db:
            user = db.scalar(select(User).where(User.username == "reset-student"))
            code_record = db.scalar(select(PasswordResetCode))
            self.assertTrue(verify_password("new-secure-pass", user.hashed_password))
            self.assertFalse(verify_password("old-pass", user.hashed_password))
            self.assertIsNotNone(code_record.consumed_at)

        old_login = self.client.post(
            "/api/auth/login",
            json={"username": "reset-student", "password": "old-pass"},
        )
        new_login = self.client.post(
            "/api/auth/login",
            json={"username": "reset-student", "password": "new-secure-pass"},
        )
        self.assertEqual(old_login.status_code, 401, old_login.text)
        self.assertEqual(new_login.status_code, 200, new_login.text)
        old_me = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {old_token}"},
        )
        self.assertEqual(old_me.status_code, 401, old_me.text)

    def test_unknown_email_returns_generic_success_without_sending_mail(self):
        response = self.client.post(
            "/api/auth/password-reset/code",
            json={"email": "unknown@qq.com", "turnstile_token": "valid-token"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["data"]["resend_after"], 60)
        self.mail_mock.assert_not_awaited()
        with self.Session() as db:
            self.assertIsNotNone(db.scalar(select(PasswordResetCode)))

        cooldown_response = self.client.post(
            "/api/auth/password-reset/code",
            json={"email": "unknown@qq.com", "turnstile_token": "valid-token"},
        )
        self.assertEqual(cooldown_response.status_code, 429, cooldown_response.text)
