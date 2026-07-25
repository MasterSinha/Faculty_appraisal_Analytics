import unittest
from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from app.services.patents_analytics_service import PatentsAnalyticsService


class TestPatentsAnalyticsModule(unittest.TestCase):
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

        patents = Table(
            "patents",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("type", String),
            Column("scope", String),
            Column("patent_date", String),
            Column("patent_status", String),
            Column("file_no", String),
            Column("academic_year", String),
            Column("score", Float),
            Column("hod_score", Float),
            Column("director_score", Float),
            Column("dean_score", Float),
            Column("vc_score", Float),
        )

        ipr = Table(
            "ipr_records",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("scope", String),
            Column("ipr_date", String),
            Column("ipr_status", String),
            Column("file_no", String),
            Column("score", Float),
        )

        journal = Table(
            "journal_publications",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("publication_year", Integer),
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
                    "email": "  ALICE@university.edu  ",
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
                    "department": "Mechanical Engineering",
                    "designation": "Assistant Professor",
                    "is_active": True,
                },
            ],
        )

        # Insert test patents
        cls.session.execute(
            patents.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "AI Neural Chip Architecture",
                    "type": "Utility Patent",
                    "scope": "National",
                    "patent_date": "2023-05-15",
                    "patent_status": "Patent Granted",
                    "file_no": "PAT-2023-001",
                    "academic_year": "2023-24",
                    "score": 20.0,
                    "hod_score": 20.0,
                    "director_score": 20.0,
                    "dean_score": 20.0,
                    "vc_score": 20.0,
                },
                {
                    "id": 2,
                    "faculty_email": "alice@university.edu",
                    "title": "Quantum Error Correction Method",
                    "type": "Process Patent",
                    "scope": "PCT International",
                    "patent_date": "2024-02-10",
                    "patent_status": "Filing Done",
                    "file_no": "PAT-2024-002",
                    "academic_year": "2023-24",
                    "score": 15.0,
                    "hod_score": 15.0,
                    "director_score": 15.0,
                    "dean_score": 15.0,
                    "vc_score": 15.0,
                },
                {
                    "id": 3,
                    "faculty_email": "alice@university.edu",
                    "title": "   ",  # Invalid title -> must be excluded
                    "type": "Design",
                    "scope": "Domestic",
                    "patent_date": "2024-01-01",
                    "patent_status": "Granted",
                    "file_no": "PAT-2024-003",
                    "academic_year": "2023-24",
                    "score": 0.0,
                    "hod_score": 0.0,
                    "director_score": 0.0,
                    "dean_score": 0.0,
                    "vc_score": 0.0,
                },
            ],
        )

        # Insert test IPR records
        cls.session.execute(
            ipr.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "bob@university.edu",
                    "title": "Quantum Sensor Design Copyright",
                    "scope": "Indian",
                    "ipr_date": "2024-03-20",
                    "ipr_status": "Registered",
                    "file_no": "IPR-2024-001",
                    "score": 10.0,
                }
            ],
        )

        # Insert test journal publication for Charlie (has journal paper but 0 patents)
        cls.session.execute(
            journal.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "charlie@university.edu",
                    "title": "Thermal Dynamics in Engines",
                    "publication_year": 2024,
                }
            ],
        )

        cls.session.commit()
        cls.service = PatentsAnalyticsService(cls.session)

    def test_overview(self):
        ov = self.service.overview({})
        self.assertEqual(ov["total_valid_patents"], 2)
        self.assertEqual(ov["patent_filing_faculty"], 1)
        self.assertEqual(ov["total_active_faculty"], 3)
        self.assertEqual(ov["patents_granted"], 1)
        self.assertEqual(ov["patents_pending"], 1)
        self.assertEqual(ov["patent_grant_rate"], 50.0)
        self.assertEqual(ov["total_ipr_records"], 1)
        self.assertEqual(ov["faculty_with_multiple_patents"], 1)
        self.assertEqual(ov["faculty_with_journal_papers_but_no_patents"], 1)
        self.assertIn("Mechanical Engineering", ov["departments_with_no_patent_contribution"])

    def test_status_analytics(self):
        st = self.service.status_analytics({})
        p_dist = {item["status"]: item["count"] for item in st["patent_status_distribution"]}
        self.assertEqual(p_dist.get("Granted"), 1)
        self.assertEqual(p_dist.get("Filed"), 1)

    def test_departments(self):
        deps = self.service.departments(1, 10, {})
        self.assertEqual(deps["total"], 3)

    def test_faculty(self):
        fac = self.service.faculty(1, 10, {})
        self.assertEqual(fac["total"], 3)

    def test_records_patents(self):
        recs = self.service.records_patents(1, 10, {})
        self.assertEqual(recs["total"], 2)
        item = recs["items"][0]
        self.assertIn("normalized_status", item)
        self.assertIn("normalized_scope", item)

    def test_records_ipr(self):
        recs = self.service.records_ipr(1, 10, {})
        self.assertEqual(recs["total"], 1)

    def test_trends(self):
        tr = self.service.trends({})
        self.assertGreaterEqual(len(tr["patents_by_year"]), 1)

    def test_export(self):
        rows = self.service.export_csv_rows({})
        self.assertEqual(len(rows), 3)


if __name__ == "__main__":
    unittest.main()
