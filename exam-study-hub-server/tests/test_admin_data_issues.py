from unittest import TestCase

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.catalog import AdmissionPlan, Institution, Major, Province, Question, QuestionTopic
from app.models.user import User


class AdminDataIssuesTest(TestCase):
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
        self.client = TestClient(app)
        with self.Session() as db:
            admin = User(username="admin", hashed_password="unused", role="admin")
            province = Province(code="henan", name="河南")
            major = Major(code="computer", name="计算机科学与技术", category="理工类")
            topic = QuestionTopic(subject="英语", name="词汇")
            db.add_all([admin, province, major, topic])
            db.flush()
            institution = Institution(code="001", name="测试大学", province_id=province.id)
            db.add(institution)
            db.flush()
            db.add_all([
                Question(topic_id=topic.id, stem="duplicate stem", options=["A", "B"], answer="A"),
                Question(topic_id=topic.id, stem="duplicate stem", options=["A", "B"], answer="A"),
                AdmissionPlan(
                    institution_id=institution.id,
                    year=2026,
                    major_code="unknown-major",
                    major_name="未收录专业",
                    level="专升本",
                    line_type="招生计划",
                ),
            ])
            db.commit()
            self.headers = {"Authorization": f"Bearer {create_access_token(admin.id, admin.password_version)}"}

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_admin_can_review_and_update_data_issue_status(self):
        response = self.client.get("/api/admin/data/issues", headers=self.headers)

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()["data"]
        self.assertEqual(payload["counts"]["open"], 2)
        duplicate = next(item for item in payload["items"] if item["issue_type"] == "duplicate_question")
        self.assertEqual(len(duplicate["related_records"]), 2)

        update = self.client.patch(
            f"/api/admin/data/issues/{duplicate['key']}",
            headers=self.headers,
            json={"status": "resolved"},
        )

        self.assertEqual(update.status_code, 200, update.text)
        self.assertEqual(update.json()["data"]["status"], "resolved")
        pending = self.client.get("/api/admin/data/issues", headers=self.headers)
        resolved = self.client.get("/api/admin/data/issues?status=resolved", headers=self.headers)
        self.assertEqual(pending.json()["data"]["counts"]["open"], 1)
        self.assertEqual(len(resolved.json()["data"]["items"]), 1)
        self.assertEqual(resolved.json()["data"]["items"][0]["status_updated_by"], "admin")

    def test_regular_user_cannot_access_data_issues(self):
        with self.Session() as db:
            user = User(username="student", hashed_password="unused", role="user")
            db.add(user)
            db.commit()
            headers = {"Authorization": f"Bearer {create_access_token(user.id, user.password_version)}"}

        response = self.client.get("/api/admin/data/issues", headers=headers)
        self.assertEqual(response.status_code, 403, response.text)
