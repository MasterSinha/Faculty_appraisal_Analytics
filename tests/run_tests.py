import sys
import unittest
from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.endpoints.faculty_research_analytics import clamp_page_size
from app.core.cache import clear_cache
from app.database import get_db
from app.main import app
from app.repositories.department_performance_analytics_repository import DepartmentPerformanceAnalyticsRepository
from app.repositories.faculty_research_analytics_repository import FacultyResearchAnalyticsRepository, clean_filter, valid_condition_for_table
from app.repositories.school_performance_analytics_repository import SchoolPerformanceAnalyticsRepository
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
            Column("academic_year", String),
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
            Column("academic_year", String),
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
            Column("role", String),
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
            Column("academic_year", String),
        )

        conferences = Table(
            "conferences",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("academic_year", String),
        )

        awards = Table(
            "awards",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("academic_year", String),
        )

        products = Table(
            "products_developed",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("details", String),
            Column("academic_year", String),
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

        ipr = Table(
            "ipr_records",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("academic_year", String),
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
                    "academic_year": "2023-24",
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
                    "academic_year": "2023-24",
                    "publication_year": 2024,
                    "score": 15.0,
                    "vc_score": 15.0,
                },
            ],
        )

        # Primary PI Project for Alice (Engineering)
        cls.session.execute(
            projects.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Quantum AI Systems",
                    "project_title": "Quantum AI Systems",
                    "project_status": "Ongoing",
                    "role": "Principal Investigator",
                    "agency": "DST",
                    "funding_agency": "DST",
                    "amount": 750000.0,
                    "project_type": "External",
                    "academic_year": "2023-24",
                    "score": 15.0,
                    "vc_score": 15.0,
                },
                # Co-PI record for same project under Bob (Sciences) - should be deduplicated to PI Alice
                {
                    "id": 2,
                    "faculty_email": "bob@university.edu",
                    "title": "Quantum AI Systems",
                    "project_title": "Quantum AI Systems",
                    "project_status": "Ongoing",
                    "role": "Co-Investigator",
                    "agency": "DST",
                    "funding_agency": "DST",
                    "amount": 750000.0,
                    "project_type": "External",
                    "academic_year": "2023-24",
                    "score": 5.0,
                    "vc_score": 5.0,
                },
            ],
        )

        cls.session.execute(
            proposals.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Unsanctioned Proposal Idea",
                    "amount": 5000000.0,
                    "academic_year": "2023-24",
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

    def test_clean_filter_sanitization(self):
        self.assertIsNone(clean_filter("All Schools"))
        self.assertIsNone(clean_filter("All Departments"))
        self.assertIsNone(clean_filter("All Years"))
        self.assertIsNone(clean_filter("all"))
        self.assertIsNone(clean_filter(""))
        self.assertIsNone(clean_filter("undefined"))
        self.assertEqual(clean_filter("School of Engineering"), "School of Engineering")

    def test_clamp_page_size(self):
        self.assertEqual(clamp_page_size(5000, max_limit=100), 100)
        self.assertEqual(clamp_page_size(0, max_limit=100), 20)
        self.assertEqual(clamp_page_size(50, max_limit=100), 50)
        self.assertEqual(clamp_page_size(5000, max_limit=1000), 1000)

    def test_valid_condition_helper(self):
        self.assertIn("title", valid_condition_for_table("t", "journal_publications"))
        self.assertIn("book", valid_condition_for_table("t", "book_publications"))
        self.assertIn("title", valid_condition_for_table("t", "patents"))

    def test_dashboard_summary_structure(self):
        clear_cache()
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
        clear_cache()
        res1 = self.faculty_repo.dashboard_summary({"school": "School of Engineering"})
        self.assertFalse(res1["meta"]["cached"])

        res2 = self.faculty_repo.dashboard_summary({"school": "School of Engineering"})
        self.assertTrue(res2["meta"]["cached"])

        res3 = self.faculty_repo.dashboard_summary({"school": "School of Engineering"}, refresh=True)
        self.assertFalse(res3["meta"]["cached"])

    def test_all_schools_consistency(self):
        clear_cache()
        dash_all = self.faculty_repo.dashboard_summary({"school": "All Schools"}, refresh=True)
        dash_single = self.faculty_repo.dashboard_summary({"school": "School of Engineering"}, refresh=True)

        all_patents = dash_all["overview"]["total_patents"]
        single_patents = dash_single["overview"]["total_patents"]

        self.assertGreaterEqual(all_patents, single_patents)

    def test_pagination_unpaginated_summary(self):
        p10 = self.faculty_repo.category_records("patents", {}, 1, 10)
        p1 = self.faculty_repo.category_records("patents", {}, 1, 1)

        self.assertIn("summary", p10)
        self.assertEqual(p10["summary"]["total_valid_patents"], p1["summary"]["total_valid_patents"])

    def test_debug_counts_all_metrics(self):
        for m in ("patents", "journals", "books", "projects"):
            dbg = self.faculty_repo.debug_counts(m)
            self.assertIn("all_schools_total", dbg)
            self.assertIn("by_school", dbg)
            self.assertTrue(dbg["is_consistent"])
            self.assertTrue(dbg["dashboard_matches_detail"])

    def test_dashboard_overview_primary_owner_deduplication(self):
        clear_cache()
        dash = self.faculty_repo.dashboard_summary({}, refresh=True, debug=True)
        overview = dash["overview"]

        # 1. Total sanctioned funding must be 750,000 (deduplicated PI project) and exclude proposal (5,000,000)
        self.assertEqual(overview["total_sanctioned_funding"], 750000.0)
        self.assertEqual(overview["total_proposal_amount"], 5000000.0)

        # 2. Deduped project count must be 1 (not 2 because co-PI duplicate was removed)
        self.assertEqual(overview["total_research_projects"], 1)

        # 3. Primary owner PI belongs to "School of Engineering"
        eng_overview = self.faculty_repo.overview({"school": "School of Engineering"})
        sci_overview = self.faculty_repo.overview({"school": "School of Sciences"})

        self.assertEqual(eng_overview["total_sanctioned_funding"], 750000.0)
        self.assertEqual(sci_overview["total_sanctioned_funding"], 0.0)

        # 4. Debug meta verification
        debug_totals = dash["meta"]["debug_overview_totals"]
        self.assertEqual(debug_totals["funding_attribution_rule"], "primary_owner_deduplicated")
        self.assertEqual(debug_totals["all_schools_funding"], 750000.0)
        self.assertEqual(debug_totals["sum_of_school_funding"], 750000.0)
        self.assertTrue(debug_totals["funding_is_additive"])
        self.assertEqual(debug_totals["difference"], 0.0)

    def test_department_performance_soemr_scoping_and_meta(self):
        dept_repo = DepartmentPerformanceAnalyticsRepository(self.session)

        # 1. Default call returns only SoEMR rows
        res_default = dept_repo.get_analytics(1, 100, {})
        for item in res_default["items"]:
            self.assertEqual(item["school"], "SoEMR")
            self.assertNotIn("no department mapped", item["department"].lower())
            self.assertNotIn(item["department"].lower(), {"unassigned", "unknown", "n/a", ""})

        # 2. ?school=All Schools returns only SoEMR rows
        res_all = dept_repo.get_analytics(1, 100, {"school": "All Schools"})
        for item in res_all["items"]:
            self.assertEqual(item["school"], "SoEMR")

        # 3. ?school=SoCSEA still returns only SoEMR rows
        res_socsea = dept_repo.get_analytics(1, 100, {"school": "SoCSEA"})
        for item in res_socsea["items"]:
            self.assertEqual(item["school"], "SoEMR")

        # 4. Meta verification
        self.assertIn("meta", res_default)
        self.assertEqual(res_default["meta"]["scope"], "SoEMR departments only")
        self.assertEqual(res_default["meta"]["school_filter_forced"], "SoEMR")

    def test_school_performance_and_dashboard_unchanged(self):
        school_repo = SchoolPerformanceAnalyticsRepository(self.session)
        res_school = school_repo.get_analytics(1, 100, {})
        self.assertIn("items", res_school)

        dash = self.faculty_repo.dashboard_summary({}, refresh=True)
        self.assertIn("overview", dash)

    def test_deduplication_and_duplicate_aware_analytics(self):
        from app.utils.deduplication import (
            get_book_dedupe_key,
            get_document_dedupe_key,
            get_ipr_dedupe_key,
            get_journal_dedupe_key,
            get_patent_dedupe_key,
            group_records_by_key,
        )

        sample_journals = [
            {
                "id": 101,
                "title": "Impact of AI on Education",
                "journal": "IEEE Transactions",
                "issn": "1234-5678",
                "academic_year": "2025-2026",
                "faculty_email": "alice@university.edu",
                "faculty_name": "Dr. Alice Smith",
                "department": "Mechanical Engineering",
                "school": "SoEMR",
                "updated_at": "2026-01-01 10:00:00",
                "created_at": "2026-01-01 09:00:00",
                "final_validated_score": 20.0,
            },
            {
                "id": 102,
                "title": "Impact of AI on Education",
                "journal": "IEEE Transactions",
                "issn": "1234-5678",
                "academic_year": "2025-2026",
                "faculty_email": "alice@university.edu",
                "faculty_name": "Dr. Alice Smith",
                "department": "Mechanical Engineering",
                "school": "SoEMR",
                "updated_at": "2026-02-01 10:00:00",
                "created_at": "2026-01-01 09:00:00",
                "final_validated_score": 20.0,
            },
            {
                "id": 103,
                "title": "Impact of AI on Education",
                "journal": "IEEE Transactions",
                "issn": "1234-5678",
                "academic_year": "2025-2026",
                "faculty_email": "bob@university.edu",
                "faculty_name": "Dr. Bob Jones",
                "department": "Mechanical Engineering",
                "school": "SoEMR",
                "updated_at": "2026-01-15 10:00:00",
                "created_at": "2026-01-01 09:00:00",
                "final_validated_score": 20.0,
            },
        ]

        # 1. Grouped journals test (Same faculty duplicate + multiple faculty same paper)
        grouped, metrics = group_records_by_key(sample_journals, get_journal_dedupe_key, "publication")
        self.assertEqual(len(grouped), 1)
        group_item = grouped[0]
        self.assertEqual(group_item["record_count"], 3)
        self.assertEqual(group_item["faculty_count"], 2)
        self.assertTrue(group_item["is_duplicate_group"])
        self.assertEqual(len(group_item["contributors"]), 2)
        # Representative selection prefers newest updated_at (2026-02-01) -> id 102
        self.assertEqual(group_item["id"], 102)
        self.assertEqual(metrics["raw_filtered_count"], 3)
        self.assertEqual(metrics["grouped_filtered_count"], 1)
        self.assertEqual(metrics["duplicate_groups_count"], 1)
        self.assertEqual(metrics["duplicate_rows_removed"], 2)

        # 2. Missing ISSN / null / blank fallback test does not crash
        no_issn_pubs = [
            {"title": None, "journal": "", "issn": None, "academic_year": None, "faculty_email": None},
            {"title": "Quantum Computing 2026", "journal": "Nature Physics", "issn": "", "academic_year": "2025-2026", "faculty_email": "bob@university.edu"},
        ]
        key1 = get_journal_dedupe_key(no_issn_pubs[0])
        key2 = get_journal_dedupe_key(no_issn_pubs[1])
        self.assertIn("unknown_title", key1)
        self.assertIn("no_issn", key2)

        # 3. Patent file number match test
        patents = [
            {"file_number": "PAT-2026-999", "title": "Smart Solar Panel", "academic_year": "2025-2026", "faculty_email": "alice@university.edu"},
            {"file_number": "PAT-2026-999", "title": "Smart Solar Panel System", "academic_year": "2025-2026", "faculty_email": "bob@university.edu"},
        ]
        pkey1 = get_patent_dedupe_key(patents[0])
        pkey2 = get_patent_dedupe_key(patents[1])
        self.assertEqual(pkey1, pkey2)
        self.assertEqual(pkey1, "file_no:pat-2026-999")

        # 4. Filter first, then group test
        res_soemr = self.faculty_repo.category_records("journal_publications", {"school": "SoEMR", "view": "grouped"}, 1, 100)
        self.assertIn("summary", res_soemr)
        self.assertIn("grouped_filtered_count", res_soemr["summary"])

        # 5. Group first, then paginate test
        res_p1 = self.faculty_repo.category_records("journal_publications", {"view": "grouped"}, 1, 1)
        self.assertEqual(res_p1["page"], 1)
        self.assertEqual(res_p1["page_size"], 1)
        self.assertEqual(len(res_p1["items"]), 1 if res_p1["total"] > 0 else 0)

        # 6. All Schools total >= individual school total test
        res_all_schools = self.faculty_repo.category_records("journal_publications", {"school": "All Schools", "view": "grouped"}, 1, 100)
        self.assertGreaterEqual(res_all_schools["total"], res_soemr["total"])

        # 7. Duplicates API endpoint test
        dup_res = self.faculty_repo.duplicates({})
        self.assertIn("journal_publications", dup_res)
        self.assertIn("patents", dup_res)
        self.assertIn("duplicate_groups_count", dup_res["journal_publications"])


if __name__ == "__main__":
    unittest.main()
