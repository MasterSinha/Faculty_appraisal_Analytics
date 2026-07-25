import unittest
from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from app.services.books_analytics_service import BooksAnalyticsService


class TestBooksAnalyticsModule(unittest.TestCase):
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
            Column("first_author", String),
            Column("coauthor", String),
            Column("publication_year", Integer),
            Column("score", Float),
            Column("hod_score", Float),
            Column("director_score", Float),
            Column("dean_score", Float),
            Column("vc_score", Float),
        )

        journal = Table(
            "journal_publications",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("journal_name", String),
            Column("publication_year", Integer),
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

        cls.session.execute(
            books.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Advanced Distributed Systems",
                    "book": "Distributed Systems Handbook",
                    "publisher": "Springer",
                    "isbn": "978-3-16-148410-0",
                    "role": "First Author",
                    "first_author": "Dr. Alice Smith",
                    "coauthor": None,
                    "publication_year": 2024,
                    "score": 15.0,
                    "hod_score": 15.0,
                    "director_score": 15.0,
                    "dean_score": 15.0,
                    "vc_score": 15.0,
                },
                {
                    "id": 2,
                    "faculty_email": "alice@university.edu",
                    "title": "Cloud Computing Handbook",
                    "book": "Cloud Architecture Volume 1",
                    "publisher": "Springer",
                    "isbn": "978-3-16-148410-0",  # Duplicate ISBN for testing
                    "role": "Co-Author",
                    "first_author": None,
                    "coauthor": "Dr. Alice Smith",
                    "publication_year": 2023,
                    "score": 10.0,
                    "hod_score": 10.0,
                    "director_score": 10.0,
                    "dean_score": 10.0,
                    "vc_score": 10.0,
                },
            ],
        )

        cls.session.execute(
            journal.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "journal_name": "IEEE Transactions",
                    "publication_year": 2024,
                }
            ],
        )

        cls.session.commit()
        cls.service = BooksAnalyticsService(cls.session)

    def test_overview(self):
        ov = self.service.overview({})
        self.assertEqual(ov["total_book_publication_records"], 2)
        self.assertEqual(ov["faculty_publishing_books"], 1)
        self.assertEqual(ov["total_active_faculty"], 2)
        self.assertEqual(ov["book_participation_rate"], 50.0)
        self.assertEqual(ov["books_per_active_faculty"], 1.0)
        self.assertEqual(ov["books_per_publishing_faculty"], 2.0)
        self.assertEqual(ov["publications_with_isbn"], 2)
        self.assertEqual(ov["isbn_completion_rate"], 100.0)
        self.assertEqual(ov["first_author_contributions"], 1)
        self.assertEqual(ov["coauthored_contributions"], 1)
        self.assertEqual(ov["faculty_with_multiple_books"], 1)
        self.assertEqual(ov["faculty_publishing_both_books_and_journals"], 1)

    def test_departments(self):
        deps = self.service.departments(1, 10, {})
        self.assertEqual(deps["total"], 2)
        self.assertGreaterEqual(len(deps["items"]), 1)

    def test_publishers(self):
        pubs = self.service.publishers({})
        self.assertEqual(len(pubs), 1)
        self.assertEqual(pubs[0]["publisher"], "Springer")
        self.assertEqual(pubs[0]["total_books"], 2)

    def test_authorship(self):
        auth = self.service.authorship({})
        self.assertEqual(auth["first_author_contributions"], 1)
        self.assertEqual(auth["coauthored_contributions"], 1)

    def test_quality(self):
        qual = self.service.quality({})
        self.assertEqual(qual["isbn_completion_rate"], 100.0)
        self.assertGreater(qual["duplicate_isbn_count"], 0)

    def test_records(self):
        recs = self.service.records(1, 10, {})
        self.assertEqual(recs["total"], 2)
        scores = {item["final_validated_score"] for item in recs["items"]}
        self.assertIn(15.0, scores)
        self.assertIn(10.0, scores)

    def test_faculty_detail(self):
        fac = self.service.faculty_detail("alice@university.edu")
        self.assertEqual(fac["total_books"], 2)
        self.assertEqual(len(fac["records"]), 2)

    def test_export(self):
        export = self.service.export_csv_rows({})
        self.assertEqual(len(export), 2)


if __name__ == "__main__":
    unittest.main()
