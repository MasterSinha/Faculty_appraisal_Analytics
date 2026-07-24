-- Research analytics views for PostgreSQL.
-- Review before applying. These statements do not modify existing tables.

CREATE OR REPLACE VIEW vw_research_activity_union AS
SELECT id::text AS activity_id, faculty_email, academic_year, 'Journals' AS category,
       title, NULL::date AS activity_date, 0::numeric AS amount, indexing AS status,
       journal AS agency, COALESCE(vc_score, dean_score, director_score, hod_score, score, 0)::numeric AS score
FROM journal_publications
WHERE NULLIF(TRIM(title), '') IS NOT NULL
UNION ALL
SELECT id::text, faculty_email, academic_year, 'Books',
       COALESCE(NULLIF(TRIM(title), ''), NULLIF(TRIM(book), '')), NULL::date, 0::numeric,
       publisher, publisher, COALESCE(vc_score, dean_score, director_score, hod_score, score, 0)::numeric
FROM book_publications
WHERE COALESCE(NULLIF(TRIM(title), ''), NULLIF(TRIM(book), '')) IS NOT NULL
UNION ALL
SELECT id::text, faculty_email, academic_year, 'Patents',
       title, patent_date, 0::numeric, patent_status, type, COALESCE(score, 0)::numeric
FROM patents
WHERE NULLIF(TRIM(title), '') IS NOT NULL
UNION ALL
SELECT id::text, faculty_email, academic_year, 'IPR',
       title, ipr_date, 0::numeric, ipr_status, scope, COALESCE(score, 0)::numeric
FROM ipr_records
WHERE NULLIF(TRIM(title), '') IS NOT NULL
UNION ALL
SELECT id::text, faculty_email, academic_year, 'Projects',
       title, sanction_date, COALESCE(amount, 0)::numeric, project_status, agency, COALESCE(score, 0)::numeric
FROM research_projects
WHERE NULLIF(TRIM(title), '') IS NOT NULL
UNION ALL
SELECT id::text, faculty_email, academic_year, 'External Projects',
       title, sanction_date, COALESCE(amount, 0)::numeric, project_status, agency, COALESCE(score, 0)::numeric
FROM external_research_projects
WHERE NULLIF(TRIM(title), '') IS NOT NULL
UNION ALL
SELECT id::text, faculty_email, academic_year, 'Proposals',
       title, NULL::date, COALESCE(amount, 0)::numeric, NULL::text, agency, COALESCE(score, 0)::numeric
FROM research_proposals
WHERE NULLIF(TRIM(title), '') IS NOT NULL
UNION ALL
SELECT id::text, faculty_email, academic_year, 'Guidance',
       thesis, NULL::date, 0::numeric, degree, student_name, COALESCE(score, 0)::numeric
FROM research_guidance
WHERE COALESCE(NULLIF(TRIM(thesis), ''), NULLIF(TRIM(student_name), '')) IS NOT NULL
UNION ALL
SELECT id::text, faculty_email, academic_year, 'Conferences',
       title, NULL::date, 0::numeric, level, organization, COALESCE(score, 0)::numeric
FROM conferences
WHERE NULLIF(TRIM(title), '') IS NOT NULL
UNION ALL
SELECT id::text, faculty_email, academic_year, 'Awards',
       title, award_date, 0::numeric, level, agency, COALESCE(score, 0)::numeric
FROM awards
WHERE NULLIF(TRIM(title), '') IS NOT NULL
UNION ALL
SELECT id::text, faculty_email, academic_year, 'Products',
       details, NULL::date, 0::numeric, usage, NULL::text, COALESCE(score, 0)::numeric
FROM products_developed
WHERE NULLIF(TRIM(details), '') IS NOT NULL;

CREATE OR REPLACE VIEW vw_faculty_research_summary AS
SELECT
  fp.email AS faculty_email,
  fp.employee_id,
  fp.full_name,
  fp.qualification,
  fp.designation,
  fp.department,
  fp.school,
  fp.academic_year,
  fp.appraisal_role,
  fp.is_active,
  COUNT(DISTINCT rau.activity_id) FILTER (WHERE rau.category = 'Journals') AS journal_publications,
  COUNT(DISTINCT rau.activity_id) FILTER (WHERE rau.category = 'Books') AS book_publications,
  COUNT(DISTINCT rau.activity_id) FILTER (WHERE rau.category IN ('Patents', 'IPR')) AS patents,
  COUNT(DISTINCT rau.activity_id) FILTER (WHERE rau.category IN ('Projects', 'External Projects')) AS research_projects,
  COALESCE(SUM(rau.amount) FILTER (WHERE rau.category IN ('Projects', 'External Projects')), 0) AS project_funding,
  COUNT(DISTINCT rau.activity_id) FILTER (WHERE rau.category = 'Proposals') AS research_proposals,
  COALESCE(SUM(rau.amount) FILTER (WHERE rau.category = 'Proposals'), 0) AS proposal_amount,
  COUNT(DISTINCT rau.activity_id) FILTER (WHERE rau.category = 'Guidance') AS research_guidance,
  COUNT(DISTINCT rau.activity_id) FILTER (WHERE rau.category = 'Conferences') AS conferences,
  COUNT(DISTINCT rau.activity_id) FILTER (WHERE rau.category = 'Awards') AS awards,
  COUNT(DISTINCT rau.activity_id) FILTER (WHERE rau.category = 'Products') AS products_developed,
  COUNT(DISTINCT rau.activity_id) AS total_research_contribution_count,
  COALESCE(SUM(rau.score), 0) AS total_research_score
FROM faculty_profiles fp
LEFT JOIN vw_research_activity_union rau
  ON LOWER(TRIM(rau.faculty_email)) = LOWER(TRIM(fp.email))
 AND rau.academic_year = fp.academic_year
GROUP BY fp.email, fp.employee_id, fp.full_name, fp.qualification, fp.designation,
         fp.department, fp.school, fp.academic_year, fp.appraisal_role, fp.is_active;

CREATE OR REPLACE VIEW vw_department_research_summary AS
SELECT
  school,
  department,
  academic_year,
  COUNT(DISTINCT faculty_email) FILTER (WHERE is_active = TRUE) AS total_active_faculty,
  SUM(journal_publications) AS journal_publications,
  COUNT(DISTINCT faculty_email) FILTER (WHERE journal_publications > 0 AND is_active = TRUE) AS faculty_who_published_papers,
  SUM(book_publications) AS book_publications,
  COUNT(DISTINCT faculty_email) FILTER (WHERE book_publications > 0 AND is_active = TRUE) AS faculty_who_published_books,
  SUM(patents) AS patents,
  SUM(research_projects) AS research_projects,
  SUM(project_funding) AS total_project_funding,
  SUM(research_proposals) AS research_proposals,
  SUM(proposal_amount) AS total_proposal_amount,
  SUM(research_guidance) AS research_scholars_guided,
  SUM(conferences) AS conferences,
  SUM(awards) AS awards,
  SUM(products_developed) AS products_developed,
  SUM(total_research_score) AS total_research_score
FROM vw_faculty_research_summary
GROUP BY school, department, academic_year;

CREATE OR REPLACE VIEW vw_school_research_summary AS
SELECT
  school,
  academic_year,
  SUM(total_active_faculty) AS total_active_faculty,
  SUM(journal_publications) AS journal_publications,
  SUM(book_publications) AS book_publications,
  SUM(patents) AS patents,
  SUM(research_projects) AS research_projects,
  SUM(total_project_funding) AS total_project_funding,
  SUM(research_proposals) AS research_proposals,
  SUM(total_proposal_amount) AS total_proposal_amount,
  SUM(total_research_score) AS total_research_score
FROM vw_department_research_summary
GROUP BY school, academic_year;

CREATE OR REPLACE VIEW vw_research_data_quality AS
SELECT 'journal_publications_missing_title' AS issue, COUNT(*) AS total FROM journal_publications WHERE NULLIF(TRIM(title), '') IS NULL
UNION ALL SELECT 'journal_publications_missing_issn', COUNT(*) FROM journal_publications WHERE NULLIF(TRIM(issn), '') IS NULL
UNION ALL SELECT 'journal_publications_missing_indexing', COUNT(*) FROM journal_publications WHERE NULLIF(TRIM(indexing), '') IS NULL
UNION ALL SELECT 'book_publications_missing_isbn', COUNT(*) FROM book_publications WHERE NULLIF(TRIM(isbn), '') IS NULL
UNION ALL SELECT 'patents_missing_status', COUNT(*) FROM patents WHERE NULLIF(TRIM(patent_status), '') IS NULL
UNION ALL SELECT 'projects_missing_amount', COUNT(*) FROM research_projects WHERE amount IS NULL
UNION ALL SELECT 'external_projects_missing_amount', COUNT(*) FROM external_research_projects WHERE amount IS NULL
UNION ALL SELECT 'blank_or_null_departments', COUNT(*) FROM faculty_profiles WHERE NULLIF(TRIM(department), '') IS NULL
UNION ALL SELECT 'unknown_academic_years', COUNT(*) FROM faculty_profiles WHERE NULLIF(TRIM(academic_year), '') IS NULL;

-- Recommended indexes. Review existing indexes before applying.
-- CREATE INDEX IF NOT EXISTS idx_faculty_profiles_email ON faculty_profiles (LOWER(TRIM(email)));
-- CREATE INDEX IF NOT EXISTS idx_faculty_profiles_school_department ON faculty_profiles (school, department);
-- CREATE INDEX IF NOT EXISTS idx_faculty_profiles_active ON faculty_profiles (is_active);
-- CREATE INDEX IF NOT EXISTS idx_journal_publications_email_year ON journal_publications (LOWER(TRIM(faculty_email)), academic_year);
-- CREATE INDEX IF NOT EXISTS idx_book_publications_email_year ON book_publications (LOWER(TRIM(faculty_email)), academic_year);
-- CREATE INDEX IF NOT EXISTS idx_patents_email_year ON patents (LOWER(TRIM(faculty_email)), academic_year);
-- CREATE INDEX IF NOT EXISTS idx_research_projects_email_year ON research_projects (LOWER(TRIM(faculty_email)), academic_year);
-- CREATE INDEX IF NOT EXISTS idx_external_projects_email_year ON external_research_projects (LOWER(TRIM(faculty_email)), academic_year);
-- CREATE INDEX IF NOT EXISTS idx_research_proposals_email_year ON research_proposals (LOWER(TRIM(faculty_email)), academic_year);
-- CREATE INDEX IF NOT EXISTS idx_research_guidance_email_year ON research_guidance (LOWER(TRIM(faculty_email)), academic_year);
