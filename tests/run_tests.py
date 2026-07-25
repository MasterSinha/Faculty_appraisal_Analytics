import sys
import unittest
from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.repositories.books_analytics_repository import BooksAnalyticsRepository
from app.repositories.research_analytics_repository import ResearchAnalyticsRepository
from app.services.books_analytics_service import BooksAnalyticsService
from app.services.research_analytics_service import ResearchAnalyticsService


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
            Column("journal_name", String),
            Column("indexing", String),
            Column("publication_year", Integer),
            Column("vc_score", Float),
            Column("self_score", Float),
            Column("director_score", Float),
            Column("dean_score", Float),
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
                    "is_active": True,
                },
                {
                    "id": 2,
                    "full_name": "Dr. Bob Jones",
                    "employee_id": "EMP102",
                    "email": "bob@university.edu",
                    "school": "School of Sciences",
                    "department": "Physics",
                    "is_active": True,
                },
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

        cls.session.commit()
        cls.service = ResearchAnalyticsService(cls.session)
        cls.books_service = BooksAnalyticsService(cls.session)

    def test_overview(self):
        overview = self.service.overview()
        self.assertEqual(overview["total_faculty"], 2)

    def test_books_overview(self):
        ov = self.books_service.overview({})
        self.assertEqual(ov["total_book_publication_records"], 1)
        self.assertEqual(ov["faculty_publishing_books"], 1)

    def test_books_departments(self):
        deps = self.books_service.departments(1, 10, {})
        self.assertEqual(deps["total"], 2)

    def test_books_publishers(self):
        pubs = self.books_service.publishers({})
        self.assertEqual(len(pubs), 1)

    def test_books_records(self):
        recs = self.books_service.records(1, 10, {})
        self.assertEqual(recs["total"], 1)


if __name__ == "__main__":
    unittest.main()
