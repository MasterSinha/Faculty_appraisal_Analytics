-- =============================================================================
-- FACULTY RESEARCH ANALYTICS - DATABASE INDEXES
-- Indexes on commonly filtered and joined columns for fast query execution
-- =============================================================================

-- 1. faculty_profiles indexes
CREATE INDEX IF NOT EXISTS idx_faculty_profiles_email ON faculty_profiles(email);
CREATE INDEX IF NOT EXISTS idx_faculty_profiles_email_lower ON faculty_profiles((LOWER(TRIM(email))));
CREATE INDEX IF NOT EXISTS idx_faculty_profiles_school ON faculty_profiles(school);
CREATE INDEX IF NOT EXISTS idx_faculty_profiles_department ON faculty_profiles(department);
CREATE INDEX IF NOT EXISTS idx_faculty_profiles_designation ON faculty_profiles(designation);
CREATE INDEX IF NOT EXISTS idx_faculty_profiles_is_active ON faculty_profiles(is_active);
CREATE INDEX IF NOT EXISTS idx_faculty_profiles_school_dept ON faculty_profiles(school, department);

-- 2. journal_publications indexes
CREATE INDEX IF NOT EXISTS idx_journal_publications_faculty_email ON journal_publications(faculty_email);
CREATE INDEX IF NOT EXISTS idx_journal_publications_email_lower ON journal_publications((LOWER(TRIM(faculty_email))));
CREATE INDEX IF NOT EXISTS idx_journal_publications_academic_year ON journal_publications(publication_year);
CREATE INDEX IF NOT EXISTS idx_journal_publications_indexing ON journal_publications(indexing);
CREATE INDEX IF NOT EXISTS idx_journal_faculty_year ON journal_publications((LOWER(TRIM(faculty_email))), publication_year);

-- 3. book_publications indexes
CREATE INDEX IF NOT EXISTS idx_book_publications_faculty_email ON book_publications(faculty_email);
CREATE INDEX IF NOT EXISTS idx_book_publications_email_lower ON book_publications((LOWER(TRIM(faculty_email))));
CREATE INDEX IF NOT EXISTS idx_book_publications_academic_year ON book_publications(publication_year);
CREATE INDEX IF NOT EXISTS idx_books_faculty_year ON book_publications((LOWER(TRIM(faculty_email))), publication_year);

-- 4. patents indexes
CREATE INDEX IF NOT EXISTS idx_patents_faculty_email ON patents(faculty_email);
CREATE INDEX IF NOT EXISTS idx_patents_email_lower ON patents((LOWER(TRIM(faculty_email))));
CREATE INDEX IF NOT EXISTS idx_patents_academic_year ON patents(academic_year);
CREATE INDEX IF NOT EXISTS idx_patents_status ON patents(patent_status);
CREATE INDEX IF NOT EXISTS idx_patents_faculty_year ON patents((LOWER(TRIM(faculty_email))), academic_year);

-- 5. research_projects indexes
CREATE INDEX IF NOT EXISTS idx_research_projects_faculty_email ON research_projects(faculty_email);
CREATE INDEX IF NOT EXISTS idx_research_projects_email_lower ON research_projects((LOWER(TRIM(faculty_email))));
CREATE INDEX IF NOT EXISTS idx_research_projects_academic_year ON research_projects(academic_year);
CREATE INDEX IF NOT EXISTS idx_research_projects_status ON research_projects(project_status);
CREATE INDEX IF NOT EXISTS idx_projects_faculty_year ON research_projects((LOWER(TRIM(faculty_email))), academic_year);

-- 6. external_research_projects indexes
CREATE INDEX IF NOT EXISTS idx_external_projects_faculty_email ON external_research_projects(faculty_email);
CREATE INDEX IF NOT EXISTS idx_external_projects_email_year ON external_research_projects((LOWER(TRIM(faculty_email))), academic_year);

-- 7. research_proposals indexes
CREATE INDEX IF NOT EXISTS idx_research_proposals_faculty_email ON research_proposals(faculty_email);
CREATE INDEX IF NOT EXISTS idx_research_proposals_email_year ON research_proposals((LOWER(TRIM(faculty_email))), academic_year);

-- 8. ipr_records indexes
CREATE INDEX IF NOT EXISTS idx_ipr_records_faculty_email ON ipr_records(faculty_email);
CREATE INDEX IF NOT EXISTS idx_ipr_records_email_year ON ipr_records((LOWER(TRIM(faculty_email))), academic_year);

-- 9. research_guidance indexes
CREATE INDEX IF NOT EXISTS idx_research_guidance_faculty_email ON research_guidance(faculty_email);
CREATE INDEX IF NOT EXISTS idx_research_guidance_email_year ON research_guidance((LOWER(TRIM(faculty_email))), academic_year);

-- 10. conferences indexes
CREATE INDEX IF NOT EXISTS idx_conferences_faculty_email ON conferences(faculty_email);
CREATE INDEX IF NOT EXISTS idx_conferences_email_year ON conferences((LOWER(TRIM(faculty_email))), academic_year);

-- 11. awards indexes
CREATE INDEX IF NOT EXISTS idx_awards_faculty_email ON awards(faculty_email);
CREATE INDEX IF NOT EXISTS idx_awards_email_year ON awards((LOWER(TRIM(faculty_email))), academic_year);

-- 12. products_developed indexes
CREATE INDEX IF NOT EXISTS idx_products_developed_faculty_email ON products_developed(faculty_email);
CREATE INDEX IF NOT EXISTS idx_products_developed_email_year ON products_developed((LOWER(TRIM(faculty_email))), academic_year);
