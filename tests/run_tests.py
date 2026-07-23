import sys
import unittest
from sqlalchemy import create_engine, Table, Column, Integer, String, Float, MetaData
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.repositories.research_analytics_repository import ResearchAnalyticsRepository
from app.services.research_analytics_service import ResearchAnalyticsService


class TestBackendArchitecture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        metadata = MetaData()

        faculty = Table(
            "faculty",
            metadata,
            Column("faculty_id", Integer, primary_key=True),
            Column("faculty_name", String),
            Column("employee_id", String),
            Column("email", String),
            Column("school", String),
            Column("department", String),
        )

        journal = Table(
            "journal_publications",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_id", Integer),
            Column("journal_name", String),
            Column("indexing", String),
            Column("publication_year", Integer),
            Column("vc_score", Float),
            Column("self_score", Float),
            Column("director_score", Float),
            Column("dean_score", Float),
        )

        projects = Table(
            "research_projects",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_id", Integer),
            Column("project_title", String),
            Column("status", String),
            Column("funding_agency", String),
            Column("amount", Float),
            Column("project_type", String),
            Column("vc_score", Float),
        )

        metadata.create_all(cls.engine)

        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()

        cls.session.execute(
            faculty.insert(),
            [
                {
                    "faculty_id": 1,
                    "faculty_name": "Dr. Alice Smith",
                    "employee_id": "EMP101",
                    "email": "alice@university.edu",
                    "school": "School of Engineering",
                    "department": "Computer Science",
                },
                {
                    "faculty_id": 2,
                    "faculty_name": "Dr. Bob Jones",
                    "employee_id": "EMP102",
                    "email": "bob@university.edu",
                    "school": "School of Sciences",
                    "department": "Physics",
                },
            ],
        )

        cls.session.execute(
            journal.insert(),
            [
                {
                    "id": 1,
                    "faculty_id": 1,
                    "journal_name": "IEEE Transactions on Software Engineering",
                    "indexing": "SCI",
                    "publication_year": 2024,
                    "vc_score": 10.0,
                    "self_score": 10.0,
                    "director_score": 10.0,
                    "dean_score": 10.0,
                },
                {
                    "id": 2,
                    "faculty_id": 1,
                    "journal_name": "ACM Computing Surveys",
                    "indexing": "Scopus",
                    "publication_year": 2023,
                    "vc_score": 8.0,
                    "self_score": 10.0,
                    "director_score": 8.0,
                    "dean_score": 8.0,
                },
            ],
        )

        cls.session.execute(
            projects.insert(),
            [
                {
                    "id": 1,
                    "faculty_id": 1,
                    "project_title": "Quantum AI Systems",
                    "status": "Ongoing",
                    "funding_agency": "DST",
                    "amount": 750000.0,
                    "project_type": "External",
                    "vc_score": 15.0,
                }
            ],
        )

        cls.session.commit()
        cls.repo = ResearchAnalyticsRepository(cls.session)
        cls.service = ResearchAnalyticsService(cls.session)

    def test_schema(self):
        schema = self.service.inspect_schema()
        self.assertIn("faculty_table", schema)
        self.assertIn("research_tables", schema)

    def test_overview(self):
        overview = self.service.overview()
        self.assertEqual(overview["total_faculty"], 2)
        self.assertEqual(overview["total_research_papers"], 2)
        self.assertEqual(overview["total_projects"], 1)
        self.assertEqual(overview["total_funding"], 750000.0)

    def test_indexing_distribution(self):
        indexing = self.service.indexing_distribution()
        self.assertGreaterEqual(len(indexing), 2)

    def test_faculty_summary(self):
        summary = self.service.faculty_summary(1, 10, {})
        self.assertEqual(summary["total"], 2)

    def test_faculty_detail(self):
        detail = self.service.faculty_detail(1)
        self.assertIn("faculty", detail)
        self.assertEqual(detail["faculty"]["faculty_id"], 1)

    def test_publication_trend(self):
        trend = self.service.publication_trend()
        self.assertGreaterEqual(len(trend), 2)

    def test_projects_summary(self):
        projects = self.service.projects_summary()
        self.assertIn("data", projects)
        self.assertGreater(len(projects["data"]), 0)

    def test_scores_comparison(self):
        scores = self.service.scores_comparison()
        self.assertGreater(scores["self_score"], 0)

    def test_filters(self):
        filters = self.service.filters()
        self.assertIn("School of Engineering", filters["schools"])
        self.assertIn("Computer Science", filters["departments"])

    def test_exports(self):
        rows = self.service.export_rows({})
        self.assertEqual(len(rows), 2)


if __name__ == "__main__":
    unittest.main()
