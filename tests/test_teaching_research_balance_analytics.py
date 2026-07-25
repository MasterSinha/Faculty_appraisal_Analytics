import unittest
from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from app.services.teaching_research_balance_analytics_service import TeachingResearchBalanceAnalyticsService


class TestTeachingResearchBalanceAnalyticsModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        metadata = MetaData()

        faculty = Table(
            "faculty_profiles",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("full_name", String),
            Column("employee_id", String),
            Column("email", String),
            Column("school", String),
            Column("department", String),
            Column("designation", String),
            Column("is_active", Boolean, default=True),
        )

        teaching_process = Table(
            "teaching_process",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("score", Float),
            Column("academic_year", String),
        )

        student_feedback = Table(
            "student_feedback",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("score", Float),
            Column("academic_year", String),
        )

        journals = Table(
            "journal_publications",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("score", Float),
            Column("academic_year", String),
        )

        projects = Table(
            "research_projects",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("score", Float),
            Column("academic_year", String),
        )

        innovative_teaching = Table(
            "innovative_teaching",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("score", Float),
            Column("academic_year", String),
        )

        metadata.create_all(cls.engine)

        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()

        # Insert faculty profiles (1 balanced leader, 1 teaching focused)
        cls.session.execute(
            faculty.insert(),
            [
                {
                    "id": 1,
                    "full_name": "Dr. Alice Smith",
                    "employee_id": "EMP101",
                    "email": "alice@university.edu",
                    "school": "School of Engineering",
                    "department": "Computer Science",
                    "designation": "Professor",
                    "is_active": True,
                },
                {
                    "id": 2,
                    "full_name": "Dr. Bob Jones",
                    "employee_id": "EMP102",
                    "email": "bob@university.edu",
                    "school": "School of Sciences",
                    "department": "Physics",
                    "designation": "Associate Professor",
                    "is_active": True,
                },
            ],
        )

        # Insert teaching activities
        cls.session.execute(
            teaching_process.insert(),
            [
                {"id": 1, "faculty_email": "alice@university.edu", "score": 25.0, "academic_year": "2023-24"},
                {"id": 2, "faculty_email": "bob@university.edu", "score": 25.0, "academic_year": "2023-24"},
            ],
        )

        cls.session.execute(
            student_feedback.insert(),
            [
                {"id": 1, "faculty_email": "alice@university.edu", "score": 25.0, "academic_year": "2023-24"},
                {"id": 2, "faculty_email": "bob@university.edu", "score": 25.0, "academic_year": "2023-24"},
            ],
        )

        cls.session.execute(
            innovative_teaching.insert(),
            [
                {"id": 1, "faculty_email": "alice@university.edu", "score": 15.0, "academic_year": "2023-24"},
                {"id": 2, "faculty_email": "bob@university.edu", "score": 10.0, "academic_year": "2023-24"},
            ],
        )



        # Insert research activities for Alice only (making Bob Teaching Focused)
        cls.session.execute(
            journals.insert(),
            [
                {"id": 1, "faculty_email": "alice@university.edu", "title": "AI Frontier Journal", "score": 50.0, "academic_year": "2023-24"},
            ],
        )

        cls.session.execute(
            projects.insert(),
            [
                {"id": 1, "faculty_email": "alice@university.edu", "title": "AI Research Grant", "score": 20.0, "academic_year": "2023-24"},
            ],
        )



        cls.session.commit()
        cls.service = TeachingResearchBalanceAnalyticsService(cls.session)

    def test_get_analytics_structure(self):
        res = self.service.get_analytics(1, 500, {})
        self.assertIn("items", res)
        self.assertIn("summary", res)
        self.assertIn("quadrants", res)
        self.assertIn("department_balance", res)
        self.assertIn("teaching_components", res)
        self.assertIn("research_components", res)
        self.assertEqual(res["total"], 2)

    def test_quadrant_classification(self):
        res = self.service.get_analytics(1, 500, {})
        items = res["items"]
        alice = next(item for item in items if item["faculty_email"] == "alice@university.edu")
        bob = next(item for item in items if item["faculty_email"] == "bob@university.edu")

        self.assertGreaterEqual(alice["teaching_score_percentage"], 50.0)
        self.assertGreaterEqual(alice["research_score_percentage"], 60.0)
        self.assertEqual(alice["quadrant"], "Balanced Leaders")

        self.assertEqual(bob["quadrant"], "Teaching Focused")

    def test_disclaimer_presence(self):
        res = self.service.get_analytics(1, 500, {})
        summary = res["summary"]
        self.assertIn("associations within recorded appraisal data", summary["disclaimer"])


if __name__ == "__main__":
    unittest.main()
