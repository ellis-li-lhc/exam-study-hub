from unittest import TestCase
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import EmailVerificationCode, User


class EmailRegistrationTest(TestCase):
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
            "app.routers.auth.send_verification_email",
            new=self.mail_mock,
        )
        self.turnstile_patch.start()
        self.mail_patch.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.mail_patch.stop()
        self.turnstile_patch.stop()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def send_code(self, email: str) -> str:
        response = self.client.post(
            "/api/auth/email-code",
            json={"email": email, "turnstile_token": "valid-token"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["data"]["resend_after"], 60)
        return self.mail_mock.await_args_list[-1].args[1]

    def test_verified_email_can_register_and_code_is_consumed(self):
        code = self.send_code("Student@QQ.com")
        response = self.client.post(
            "/api/auth/register",
            json={
                "username": "student",
                "password": "secure-pass",
                "email": "Student@QQ.com",
                "verification_code": code,
            },
        )

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["data"]["user"]["email"], "student@qq.com")
        with self.Session() as db:
            user = db.scalar(select(User).where(User.username == "student"))
            verification = db.scalar(select(EmailVerificationCode))
            self.assertIsNotNone(user.email_verified_at)
            self.assertIsNotNone(verification.consumed_at)

    def test_wrong_code_increments_attempts(self):
        self.send_code("wrong@qq.com")
        response = self.client.post(
            "/api/auth/register",
            json={
                "username": "wrong-code",
                "password": "secure-pass",
                "email": "wrong@qq.com",
                "verification_code": "000000",
            },
        )

        self.assertEqual(response.status_code, 400, response.text)
        with self.Session() as db:
            verification = db.scalar(select(EmailVerificationCode))
            self.assertEqual(verification.attempts, 1)

    def test_same_email_cannot_request_again_during_cooldown(self):
        self.send_code("cooldown@qq.com")
        response = self.client.post(
            "/api/auth/email-code",
            json={"email": "cooldown@qq.com", "turnstile_token": "valid-token"},
        )

        self.assertEqual(response.status_code, 429, response.text)
        self.assertIn("60", response.json()["message"])
