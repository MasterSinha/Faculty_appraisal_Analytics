import unittest
from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from app.services.journals_analytics_service import JournalsAnalyticsService


class TestJournalsAnalyticsModule(unittest.TestCase):
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

        journal = Table(
            "journal_publications",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("journal", String),
            Column("issn", String),
            Column("indexing", String),
            Column("publication_year", Integer),
            Column("score", Float),
            Column("hod_score", Float),
            Column("director_score", Float),
            Column("dean_score", Float),
            Column("vc_score", Float),
        )

        metadata.create_all(cls.engine)

        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()

        # Insert test faculty profiles
        cls.session.execute(
            faculty.insert(),
            [
                {
                    "id": 1,
                    "full_name": "Dr. Alice Smith",
                    "employee_id": "EMP101",
                    "email": "  ALICE@university.edu  ",  # Test case-insensitive trimmed join
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
                {
                    "id": 3,
                    "full_name": "Dr. Charlie Brown",
                    "employee_id": "EMP103",
                    "email": "charlie@university.edu",
                    "school": "School of Engineering",
                    "department": "Computer Science",
                    "designation": "Assistant Professor",
                    "is_active": False,  # Inactive faculty, should be excluded by default
                },
            ],
        )

        # Insert test journal publications
        cls.session.execute(
            journal.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Deep Learning Frontiers",
                    "journal": "IEEE Transactions on Neural Networks",
                    "issn": "2162-237X",
                    "indexing": "SCI",
                    "publication_year": 2023,
                    "score": 10.0,
                    "hod_score": 10.0,
                    "director_score": 10.0,
                    "dean_score": 10.0,
                    "vc_score": 10.0,
                },
                {
                    "id": 2,
                    "faculty_email": "alice@university.edu",
                    "title": "Quantum Neural Computing",
                    "journal": "IEEE Transactions on Neural Networks",  # Same journal
                    "issn": "2162-237X",
                    "indexing": "SCI",
                    "publication_year": 2024,
                    "score": 8.0,
                    "hod_score": 8.0,
                    "director_score": 12.0,
                    "dean_score": None,
                    "vc_score": 12.0,
                },
                {
                    "id": 3,
                    "faculty_email": "bob@university.edu",
                    "title": "Quantum Neural Computing",  # Same title submitted by multiple faculty
                    "journal": "Physical Review Letters",
                    "issn": "0031-9007",
                    "indexing": "Scopus",
                    "publication_year": 2024,
                    "score": 15.0,
                    "hod_score": 15.0,
                    "director_score": 15.0,
                    "dean_score": 15.0,
                    "vc_score": 15.0,
                },
                {
                    "id": 4,
                    "faculty_email": "charlie@university.edu",
                    "title": "Inactive Faculty Paper",
                    "journal": "Some Journal",
                    "issn": "1234-5678",
                    "indexing": "UGC CARE",
                    "publication_year": 2024,
                    "score": 5.0,
                    "hod_score": 5.0,
                    "director_score": 5.0,
                    "dean_score": 5.0,
                    "vc_score": 5.0,
                },
                {
                    "id": 5,
                    "faculty_email": "alice@university.edu",
                    "title": "   ",  # Invalid title (whitespace only), must be excluded
                    "journal": "Invalid Journal",
                    "issn": None,
                    "indexing": None,
                    "publication_year": 2024,
                    "score": 0.0,
                    "hod_score": 0.0,
                    "director_score": 0.0,
                    "dean_score": 0.0,
                    "vc_score": 0.0,
                },
            ],
        )

        cls.session.commit()
        cls.service = JournalsAnalyticsService(cls.session)

    def test_overview(self):
        ov = self.service.overview({})
        self.assertEqual(ov["total_valid_journal_publications"], 3)
        self.assertEqual(ov["publishing_faculty"], 2)
        self.assertEqual(ov["total_active_faculty"], 2)
        self.assertEqual(ov["publication_participation_rate"], 100.0)
        self.assertEqual(ov["papers_per_active_faculty"], 1.5)
        self.assertEqual(ov["papers_per_publishing_faculty"], 1.5)
        self.assertEqual(ov["indexed_publications"], 3)
        self.assertEqual(ov["indexed_publication_percentage"], 100.0)
        self.assertEqual(ov["unique_journal_count"], 2)
        self.assertEqual(ov["duplicate_title_count"], 1)
        self.assertEqual(ov["same_title_multiple_faculty_count"], 1)

    def test_departments(self):
        deps = self.service.departments(1, 10, {})
        self.assertEqual(deps["total"], 2)
        items = {item["department"]: item for item in deps["items"]}
        self.assertIn("Computer Science", items)
        self.assertIn("Physics", items)
        cs = items["Computer Science"]
        self.assertEqual(cs["total_papers"], 2)
        self.assertEqual(cs["active_faculty"], 1)

    def test_faculty(self):
        fac = self.service.faculty(1, 10, {})
        self.assertEqual(fac["total"], 2)
        self.assertEqual(len(fac["top_publishing_faculty"]), 2)
        self.assertEqual(len(fac["faculty_publishing_consecutive_years"]), 1)

    def test_quality_indexing(self):
        qual = self.service.quality_indexing({})
        self.assertEqual(qual["unique_journal_count"], 2)
        self.assertEqual(qual["duplicate_titles"], 1)
        self.assertEqual(qual["same_title_submitted_by_multiple_faculty"], 1)
        dist = {item["indexing"]: item["count"] for item in qual["indexing_category_distribution"]}
        self.assertEqual(dist.get("SCI"), 2)
        self.assertEqual(dist.get("SCOPUS"), 1)

    def test_records(self):
        recs = self.service.records(1, 10, {})
        self.assertEqual(recs["total"], 3)
        scores = [item["final_validated_score"] for item in recs["items"]]
        self.assertIn(10.0, scores)
        self.assertIn(12.0, scores)
        self.assertIn(15.0, scores)

    def test_faculty_detail(self):
        detail = self.service.faculty_detail("alice@university.edu")
        self.assertEqual(len(detail["publication_records"]), 2)
        self.assertEqual(detail["score_summary"]["total_score"], 22.0)

    def test_export(self):
        rows = self.service.export_csv_rows({})
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["Faculty Name"], "Dr. Alice Smith")


if __name__ == "__main__":
    unittest.main()
