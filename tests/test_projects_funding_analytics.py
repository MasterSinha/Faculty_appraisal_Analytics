import unittest
from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from app.services.projects_funding_analytics_service import ProjectsFundingAnalyticsService


class TestProjectsFundingAnalyticsModule(unittest.TestCase):
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

        internal_projects = Table(
            "research_projects",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("agency", String),
            Column("sanction_date", String),
            Column("amount", Float),
            Column("role", String),
            Column("project_status", String),
            Column("academic_year", String),
            Column("score", Float),
            Column("hod_score", Float),
            Column("director_score", Float),
            Column("dean_score", Float),
            Column("vc_score", Float),
        )

        external_projects = Table(
            "external_research_projects",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("agency", String),
            Column("sanction_date", String),
            Column("amount", Float),
            Column("role", String),
            Column("project_status", String),
            Column("academic_year", String),
            Column("score", Float),
            Column("hod_score", Float),
            Column("director_score", Float),
            Column("dean_score", Float),
            Column("vc_score", Float),
        )

        proposals = Table(
            "research_proposals",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("agency", String),
            Column("duration", String),
            Column("amount", Float),
            Column("academic_year", String),
            Column("score", Float),
        )

        metadata.create_all(cls.engine)

        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()

        # Insert faculty profiles
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

        # Insert internal research projects
        cls.session.execute(
            internal_projects.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Quantum Computing Lab Setup",
                    "agency": "DST",
                    "sanction_date": "2023-04-10",
                    "amount": 500000.0,
                    "role": "PI",
                    "project_status": "Sanctioned & Ongoing",
                    "academic_year": "2023-24",
                    "score": 15.0,
                    "hod_score": 15.0,
                    "director_score": 15.0,
                    "dean_score": 15.0,
                    "vc_score": 15.0,
                },
                {
                    "id": 2,
                    "faculty_email": "alice@university.edu",
                    "title": "   ",  # Invalid title -> must be excluded
                    "agency": "DST",
                    "sanction_date": "2023-05-10",
                    "amount": 100000.0,
                    "role": "PI",
                    "project_status": "Sanctioned",
                    "academic_year": "2023-24",
                    "score": 0.0,
                    "hod_score": 0.0,
                    "director_score": 0.0,
                    "dean_score": 0.0,
                    "vc_score": 0.0,
                },
            ],
        )

        # Insert external research projects
        cls.session.execute(
            external_projects.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "bob@university.edu",
                    "title": "Solar Cell Efficiency Research",
                    "agency": "ISRO",
                    "sanction_date": "2024-01-15",
                    "amount": 1200000.0,
                    "role": "Co-PI",
                    "project_status": "Completed",
                    "academic_year": "2023-24",
                    "score": 25.0,
                    "hod_score": 25.0,
                    "director_score": 25.0,
                    "dean_score": 25.0,
                    "vc_score": 25.0,
                }
            ],
        )

        # Insert proposals
        cls.session.execute(
            proposals.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "charlie@university.edu",
                    "title": "Robotic Automation System Proposal",
                    "agency": "SERB",
                    "duration": "2 Years",
                    "amount": 800000.0,
                    "academic_year": "2023-24",
                    "score": 10.0,
                }
            ],
        )

        cls.session.commit()
        cls.service = ProjectsFundingAnalyticsService(cls.session)

    def test_overview(self):
        ov = self.service.overview({})
        self.assertEqual(ov["total_sanctioned_funding"], 1700000.0)
        self.assertEqual(ov["total_proposed_funding"], 800000.0)
        self.assertEqual(ov["funded_project_count"], 2)
        self.assertEqual(ov["proposal_count"], 1)
        self.assertEqual(ov["average_project_amount"], 850000.0)
        self.assertEqual(ov["average_proposal_amount"], 800000.0)
        self.assertEqual(ov["faculty_receiving_project_funding"], 2)
        self.assertEqual(ov["principal_investigator_count"], 1)
        self.assertEqual(ov["ongoing_projects"], 1)
        self.assertEqual(ov["completed_projects"], 1)

    def test_projects(self):
        res = self.service.projects(1, 10, {})
        self.assertEqual(res["total"], 1)
        self.assertEqual(res["items"][0]["title"], "Quantum Computing Lab Setup")

    def test_external_projects(self):
        res = self.service.external_projects(1, 10, {})
        self.assertEqual(res["total"], 1)
        self.assertEqual(res["items"][0]["title"], "Solar Cell Efficiency Research")

    def test_proposals(self):
        res = self.service.proposals(1, 10, {})
        self.assertEqual(res["total"], 1)
        self.assertEqual(res["items"][0]["title"], "Robotic Automation System Proposal")

    def test_funding_agencies(self):
        agencies = self.service.funding_agencies({})
        self.assertEqual(len(agencies), 3)

    def test_departments(self):
        deps = self.service.departments(1, 10, {})
        self.assertEqual(deps["total"], 3)

    def test_faculty(self):
        fac = self.service.faculty(1, 10, {})
        self.assertEqual(fac["total"], 3)

    def test_trends(self):
        tr = self.service.trends({})
        self.assertGreaterEqual(len(tr["funding_trend_by_sanction_date"]), 1)

    def test_concentration(self):
        conc = self.service.concentration({})
        self.assertGreater(conc["top_five_faculty_funding_share"], 0)
        self.assertIn("Mechanical Engineering", conc["departments_with_proposals_but_no_funded_projects"])

    def test_export(self):
        rows = self.service.export_csv_rows({})
        self.assertEqual(len(rows), 3)


if __name__ == "__main__":
    unittest.main()
