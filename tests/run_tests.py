import sys
import unittest
from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.repositories.faculty_research_analytics_repository import FacultyResearchAnalyticsRepository
from app.services.faculty_research_analytics_service import FacultyResearchAnalyticsService


class TestBackendArchitecture(unittest.TestCase):
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
            Column("academic_year", String),
            Column("is_active", Boolean, default=True),
        )

        books = Table(
            "book_publications",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("book", String),
            Column("publisher", String),
            Column("isbn", String),
            Column("role", String),
            Column("publication_year", Integer),
            Column("score", Float),
            Column("vc_score", Float),
        )

        journal = Table(
            "journal_publications",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("journal_name", String),
            Column("indexing", String),
            Column("publication_year", Integer),
            Column("vc_score", Float),
            Column("self_score", Float),
            Column("director_score", Float),
            Column("dean_score", Float),
            Column("score", Float),
        )

        projects = Table(
            "research_projects",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("project_title", String),
            Column("project_status", String),
            Column("agency", String),
            Column("funding_agency", String),
            Column("amount", Float),
            Column("project_type", String),
            Column("academic_year", String),
            Column("score", Float),
            Column("vc_score", Float),
        )

        external_projects = Table(
            "external_research_projects",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("project_status", String),
            Column("agency", String),
            Column("amount", Float),
            Column("academic_year", String),
        )

        proposals = Table(
            "research_proposals",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("amount", Float),
            Column("academic_year", String),
        )

        guidance = Table(
            "research_guidance",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("student_name", String),
        )

        conferences = Table(
            "conferences",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
        )

        awards = Table(
            "awards",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
        )

        products = Table(
            "products_developed",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("details", String),
        )

        patents = Table(
            "patents",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("patent_title", String),
            Column("patent_status", String),
            Column("scope", String),
            Column("academic_year", String),
            Column("score", Float),
            Column("vc_score", Float),
        )

        metadata.create_all(cls.engine)

        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()

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
                    "academic_year": "2023-24",
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
                    "academic_year": "2023-24",
                    "is_active": True,
                },
            ],
        )

        cls.session.execute(
            journal.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Deep Learning Optimization",
                    "journal_name": "IEEE Transactions",
                    "indexing": "SCI",
                    "publication_year": 2024,
                    "vc_score": 10.0,
                    "score": 10.0,
                }
            ],
        )

        cls.session.execute(
            books.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Advanced Distributed Systems",
                    "book": "Handbook Vol 1",
                    "publisher": "Springer",
                    "isbn": "978-3-16-148410-0",
                    "role": "First Author",
                    "publication_year": 2024,
                    "score": 15.0,
                    "vc_score": 15.0,
                },
            ],
        )

        cls.session.execute(
            projects.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Quantum AI Systems",
                    "project_title": "Quantum AI Systems",
                    "project_status": "Ongoing",
                    "agency": "DST",
                    "funding_agency": "DST",
                    "amount": 750000.0,
                    "project_type": "External",
                    "academic_year": "2023-24",
                    "score": 15.0,
                    "vc_score": 15.0,
                }
            ],
        )

        cls.session.execute(
            patents.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "bob@university.edu",
                    "title": "Solar Energy Collector Grid",
                    "patent_title": "Solar Energy Collector Grid",
                    "patent_status": "Granted",
                    "scope": "National",
                    "academic_year": "2023-24",
                    "score": 20.0,
                    "vc_score": 20.0,
                }
            ],
        )

        cls.session.commit()
        cls.faculty_repo = FacultyResearchAnalyticsRepository(cls.session)
        cls.faculty_service = FacultyResearchAnalyticsService(cls.session)

    def test_dashboard_summary_structure(self):
        dash = self.faculty_repo.dashboard_summary({})
        self.assertIn("overview", dash)
        self.assertIn("kpis", dash)
        self.assertIn("trend", dash)
        self.assertIn("school_summary", dash)
        self.assertIn("department_summary", dash)
        self.assertIn("category_summary", dash)
        self.assertIn("funding_summary", dash)
        self.assertIn("patent_summary", dash)
        self.assertIn("insights", dash)
        self.assertIn("attention_alerts", dash)
        self.assertIn("filter_options", dash)
        self.assertIn("meta", dash)
        self.assertIn("warnings", dash)
        self.assertFalse(dash["meta"]["cached"])

    def test_dashboard_caching_and_refresh(self):
        # 1st call -> uncached
        res1 = self.faculty_repo.dashboard_summary({"school": "School of Engineering"})
        self.assertFalse(res1["meta"]["cached"])

        # 2nd call -> cached hit
        res2 = self.faculty_repo.dashboard_summary({"school": "School of Engineering"})
        self.assertTrue(res2["meta"]["cached"])

        # 3rd call with refresh=True -> bypass cache
        res3 = self.faculty_repo.dashboard_summary({"school": "School of Engineering"}, refresh=True)
        self.assertFalse(res3["meta"]["cached"])

    def test_health_check(self):
        health = self.faculty_service.repository.db.execute
        self.assertIsNotNone(health)

    def test_filtered_dashboard(self):
        dash = self.faculty_repo.dashboard_summary({"department": "Computer Science"}, refresh=True)
        self.assertEqual(dash["meta"]["filters_applied"]["department"], "Computer Science")


if __name__ == "__main__":
    unittest.main()
