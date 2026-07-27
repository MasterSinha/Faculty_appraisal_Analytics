-- =============================================================================
-- FACULTY RESEARCH ANALYTICS MATERIALIZED VIEWS (PRE-AGGREGATED PER-TABLE CTEs)
-- =============================================================================
-- Note: Pre-aggregating per activity table avoids row multiplication from multi-table LEFT JOINs.

-- 1. Faculty Summary Materialized View
DROP MATERIALIZED VIEW IF EXISTS mv_research_faculty_summary CASCADE;
CREATE MATERIALIZED VIEW mv_research_faculty_summary AS
WITH journal_summary AS (
  SELECT
    LOWER(TRIM(faculty_email)) AS faculty_email,
    COUNT(*) AS total_journals,
    SUM(COALESCE(score, 0)) AS journal_score
  FROM journal_publications
  WHERE NULLIF(TRIM(title), '') IS NOT NULL
  GROUP BY LOWER(TRIM(faculty_email))
),
book_summary AS (
  SELECT
    LOWER(TRIM(faculty_email)) AS faculty_email,
    COUNT(*) AS total_books,
    SUM(COALESCE(score, 0)) AS book_score
  FROM book_publications
  WHERE COALESCE(NULLIF(TRIM(title), ''), NULLIF(TRIM(book), '')) IS NOT NULL
  GROUP BY LOWER(TRIM(faculty_email))
),
patent_summary AS (
  SELECT
    LOWER(TRIM(faculty_email)) AS faculty_email,
    COUNT(*) AS total_patents,
    COUNT(*) FILTER (WHERE LOWER(COALESCE(patent_status, '')) LIKE '%grant%') AS patents_granted,
    SUM(COALESCE(score, 0)) AS patent_score
  FROM patents
  WHERE NULLIF(TRIM(title), '') IS NOT NULL
  GROUP BY LOWER(TRIM(faculty_email))
),
project_summary AS (
  SELECT
    LOWER(TRIM(faculty_email)) AS faculty_email,
    COUNT(*) AS total_projects,
    SUM(COALESCE(amount, 0)) AS total_funding,
    COUNT(*) FILTER (WHERE external_project = TRUE) AS external_projects,
    SUM(CASE WHEN external_project = TRUE THEN COALESCE(amount, 0) ELSE 0 END) AS external_funding,
    SUM(COALESCE(score, 0)) AS project_score
  FROM (
    SELECT
      x.faculty_email,
      x.amount,
      x.score,
      x.external_project
    FROM (
      SELECT
        up.*,
        ROW_NUMBER() OVER (
          PARTITION BY up.project_key
          ORDER BY
            CASE WHEN LOWER(COALESCE(up.role, '')) LIKE '%principal%' OR LOWER(COALESCE(up.role, '')) = 'pi' THEN 1 ELSE 2 END ASC,
            up.id ASC
        ) AS rn
      FROM (
        SELECT 'research_projects' AS source_table, id, faculty_email, title, amount, score, role, project_status, FALSE AS external_project,
               MD5(LOWER(TRIM(title)) || '|' || COALESCE(amount::text, '0') || '|' || LOWER(TRIM(COALESCE(agency, '')))) AS project_key
        FROM research_projects
        WHERE NULLIF(TRIM(title), '') IS NOT NULL
          AND (COALESCE(TRIM(project_status), '') = '' OR LOWER(COALESCE(project_status, '')) SIMILAR TO '%(sanction|ongoing|complete|closed|approved|active|grant)%')
          AND LOWER(COALESCE(project_status, '')) NOT IN ('proposed', 'submitted', 'rejected', 'unknown', 'draft')

        UNION ALL

        SELECT 'external_research_projects' AS source_table, id, faculty_email, title, amount, 0::numeric AS score, '' AS role, project_status, TRUE AS external_project,
               MD5(LOWER(TRIM(title)) || '|' || COALESCE(amount::text, '0') || '|' || LOWER(TRIM(COALESCE(agency, '')))) AS project_key
        FROM external_research_projects
        WHERE NULLIF(TRIM(title), '') IS NOT NULL
          AND (COALESCE(TRIM(project_status), '') = '' OR LOWER(COALESCE(project_status, '')) SIMILAR TO '%(sanction|ongoing|complete|closed|approved|active|grant)%')
          AND LOWER(COALESCE(project_status, '')) NOT IN ('proposed', 'submitted', 'rejected', 'unknown', 'draft')
      ) up
      JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(up.faculty_email))
      WHERE fp.is_active = TRUE
    ) x
    WHERE x.rn = 1
  ) deduped
  GROUP BY LOWER(TRIM(faculty_email))
),
proposal_summary AS (
  SELECT
    LOWER(TRIM(faculty_email)) AS faculty_email,
    COUNT(*) AS total_proposals,
    SUM(COALESCE(amount, 0)) AS total_proposal_amount
  FROM research_proposals
  WHERE NULLIF(TRIM(title), '') IS NOT NULL
  GROUP BY LOWER(TRIM(faculty_email))
),
guidance_summary AS (
  SELECT
    LOWER(TRIM(faculty_email)) AS faculty_email,
    COUNT(*) AS total_scholars_guided
  FROM research_guidance
  GROUP BY LOWER(TRIM(faculty_email))
),
conference_summary AS (
  SELECT
    LOWER(TRIM(faculty_email)) AS faculty_email,
    COUNT(*) AS total_conferences
  FROM conferences
  WHERE NULLIF(TRIM(title), '') IS NOT NULL
  GROUP BY LOWER(TRIM(faculty_email))
),
award_summary AS (
  SELECT
    LOWER(TRIM(faculty_email)) AS faculty_email,
    COUNT(*) AS total_awards
  FROM awards
  WHERE NULLIF(TRIM(title), '') IS NOT NULL
  GROUP BY LOWER(TRIM(faculty_email))
),
product_summary AS (
  SELECT
    LOWER(TRIM(faculty_email)) AS faculty_email,
    COUNT(*) AS total_products
  FROM products_developed
  WHERE COALESCE(NULLIF(TRIM(title), ''), NULLIF(TRIM(details), '')) IS NOT NULL
  GROUP BY LOWER(TRIM(faculty_email))
)
SELECT
  LOWER(TRIM(fp.email)) AS faculty_email,
  fp.employee_id,
  fp.full_name AS faculty_name,
  COALESCE(NULLIF(TRIM(fp.school), ''), 'Unassigned') AS school,
  COALESCE(NULLIF(TRIM(fp.department), ''), COALESCE(NULLIF(TRIM(fp.school), ''), 'Unassigned') || ' (No department mapped)') AS department,
  fp.designation,
  fp.is_active,
  COALESCE(js.total_journals, 0) AS total_journals,
  COALESCE(bs.total_books, 0) AS total_books,
  COALESCE(ps.total_patents, 0) AS total_patents,
  COALESCE(ps.patents_granted, 0) AS patents_granted,
  COALESCE(prs.total_projects, 0) AS total_projects,
  COALESCE(prs.total_funding, 0) AS total_funding,
  COALESCE(prs.external_projects, 0) AS external_projects,
  COALESCE(prs.external_funding, 0) AS external_funding,
  COALESCE(props.total_proposals, 0) AS total_proposals,
  COALESCE(props.total_proposal_amount, 0) AS total_proposal_amount,
  COALESCE(gs.total_scholars_guided, 0) AS total_scholars_guided,
  COALESCE(cs.total_conferences, 0) AS total_conferences,
  COALESCE(aws.total_awards, 0) AS total_awards,
  COALESCE(prods.total_products, 0) AS total_products,
  COALESCE(js.journal_score, 0)
    + COALESCE(bs.book_score, 0)
    + COALESCE(ps.patent_score, 0)
    + COALESCE(prs.project_score, 0) AS total_research_score
FROM faculty_profiles fp
LEFT JOIN journal_summary js ON LOWER(TRIM(fp.email)) = js.faculty_email
LEFT JOIN book_summary bs ON LOWER(TRIM(fp.email)) = bs.faculty_email
LEFT JOIN patent_summary ps ON LOWER(TRIM(fp.email)) = ps.faculty_email
LEFT JOIN project_summary prs ON LOWER(TRIM(fp.email)) = prs.faculty_email
LEFT JOIN proposal_summary props ON LOWER(TRIM(fp.email)) = props.faculty_email
LEFT JOIN guidance_summary gs ON LOWER(TRIM(fp.email)) = gs.faculty_email
LEFT JOIN conference_summary cs ON LOWER(TRIM(fp.email)) = cs.faculty_email
LEFT JOIN award_summary aws ON LOWER(TRIM(fp.email)) = aws.faculty_email
LEFT JOIN product_summary prods ON LOWER(TRIM(fp.email)) = prods.faculty_email
WHERE fp.is_active = TRUE;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_res_fac_email ON mv_research_faculty_summary (faculty_email);
CREATE INDEX IF NOT EXISTS idx_mv_res_fac_school ON mv_research_faculty_summary (school);

-- 2. Department Summary Materialized View
DROP MATERIALIZED VIEW IF EXISTS mv_research_department_summary CASCADE;
CREATE MATERIALIZED VIEW mv_research_department_summary AS
SELECT
  school,
  department,
  COUNT(faculty_email) AS total_active_faculty,
  COUNT(CASE WHEN total_journals > 0 THEN 1 END) AS research_active_faculty,
  SUM(total_journals) AS journal_publications,
  SUM(total_books) AS book_publications,
  SUM(total_patents) AS patents,
  SUM(patents_granted) AS patents_granted,
  SUM(total_projects) AS research_projects,
  SUM(total_funding) AS total_project_funding,
  SUM(total_proposals) AS research_proposals,
  SUM(total_proposal_amount) AS total_proposal_amount,
  SUM(total_scholars_guided) AS research_scholars_guided,
  SUM(total_conferences) AS conferences,
  SUM(total_awards) AS awards,
  SUM(total_products) AS products_developed,
  SUM(total_research_score) AS total_research_score
FROM mv_research_faculty_summary
GROUP BY school, department;

CREATE INDEX IF NOT EXISTS idx_mv_res_dept_school ON mv_research_department_summary (school, department);

-- 3. School Summary Materialized View
DROP MATERIALIZED VIEW IF EXISTS mv_research_school_summary CASCADE;
CREATE MATERIALIZED VIEW mv_research_school_summary AS
SELECT
  school,
  COUNT(faculty_email) AS total_active_faculty,
  COUNT(CASE WHEN total_journals > 0 THEN 1 END) AS faculty_who_published_papers,
  SUM(total_journals) AS journal_publications,
  SUM(total_books) AS book_publications,
  SUM(total_patents) AS patents,
  SUM(total_projects) AS research_projects,
  SUM(total_funding) AS total_project_funding,
  SUM(total_research_score) AS total_research_score,
  ROUND((COUNT(CASE WHEN total_journals > 0 THEN 1 END)::numeric / NULLIF(COUNT(faculty_email), 0)) * 100, 2) AS participation_rate
FROM mv_research_faculty_summary
GROUP BY school;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_res_sch_name ON mv_research_school_summary (school);

-- 4. Yearly Trend Materialized View
DROP MATERIALIZED VIEW IF EXISTS mv_research_yearly_trend CASCADE;
CREATE MATERIALIZED VIEW mv_research_yearly_trend AS
WITH year_union AS (
  SELECT academic_year::text AS academic_year, 'pub' AS type, 0::numeric AS amount FROM journal_publications WHERE NULLIF(TRIM(title), '') IS NOT NULL
  UNION ALL
  SELECT academic_year::text AS academic_year, 'book' AS type, 0::numeric AS amount FROM book_publications WHERE COALESCE(NULLIF(TRIM(title), ''), NULLIF(TRIM(book), '')) IS NOT NULL
  UNION ALL
  SELECT academic_year::text AS academic_year, 'patent' AS type, 0::numeric AS amount FROM patents WHERE NULLIF(TRIM(title), '') IS NOT NULL
  UNION ALL
  SELECT
    academic_year::text AS academic_year,
    'proj' AS type,
    COALESCE(amount, 0) AS amount
  FROM (
    SELECT
      x.academic_year,
      x.amount
    FROM (
      SELECT
        up.*,
        ROW_NUMBER() OVER (
          PARTITION BY up.project_key
          ORDER BY
            CASE WHEN LOWER(COALESCE(up.role, '')) LIKE '%principal%' OR LOWER(COALESCE(up.role, '')) = 'pi' THEN 1 ELSE 2 END ASC,
            up.id ASC
        ) AS rn
      FROM (
        SELECT 'research_projects' AS source_table, id, faculty_email, title, amount, academic_year, role, project_status,
               MD5(LOWER(TRIM(title)) || '|' || COALESCE(amount::text, '0') || '|' || LOWER(TRIM(COALESCE(agency, '')))) AS project_key
        FROM research_projects
        WHERE NULLIF(TRIM(title), '') IS NOT NULL
          AND (COALESCE(TRIM(project_status), '') = '' OR LOWER(COALESCE(project_status, '')) SIMILAR TO '%(sanction|ongoing|complete|closed|approved|active|grant)%')
          AND LOWER(COALESCE(project_status, '')) NOT IN ('proposed', 'submitted', 'rejected', 'unknown', 'draft')

        UNION ALL

        SELECT 'external_research_projects' AS source_table, id, faculty_email, title, amount, academic_year, '' AS role, project_status,
               MD5(LOWER(TRIM(title)) || '|' || COALESCE(amount::text, '0') || '|' || LOWER(TRIM(COALESCE(agency, '')))) AS project_key
        FROM external_research_projects
        WHERE NULLIF(TRIM(title), '') IS NOT NULL
          AND (COALESCE(TRIM(project_status), '') = '' OR LOWER(COALESCE(project_status, '')) SIMILAR TO '%(sanction|ongoing|complete|closed|approved|active|grant)%')
          AND LOWER(COALESCE(project_status, '')) NOT IN ('proposed', 'submitted', 'rejected', 'unknown', 'draft')
      ) up
      JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(up.faculty_email))
      WHERE fp.is_active = TRUE
    ) x
    WHERE x.rn = 1
  ) deduped_projects
)
SELECT
  academic_year,
  COUNT(CASE WHEN type = 'pub' THEN 1 END) AS publications,
  COUNT(CASE WHEN type = 'book' THEN 1 END) AS books,
  COUNT(CASE WHEN type = 'patent' THEN 1 END) AS patents,
  COUNT(CASE WHEN type = 'proj' THEN 1 END) AS projects,
  SUM(CASE WHEN type = 'proj' THEN amount ELSE 0 END) AS funding
FROM year_union
WHERE NULLIF(TRIM(academic_year), '') IS NOT NULL
GROUP BY academic_year
ORDER BY academic_year ASC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_res_yr_trend ON mv_research_yearly_trend (academic_year);

-- 5. Category Summary Materialized View
DROP MATERIALIZED VIEW IF EXISTS mv_research_category_summary CASCADE;
CREATE MATERIALIZED VIEW mv_research_category_summary AS
SELECT 'journal_publication' AS category, SUM(total_journals) AS count, 0.0::numeric AS total_score, 0.0::numeric AS total_amount FROM mv_research_faculty_summary
UNION ALL
SELECT 'book_publication' AS category, SUM(total_books) AS count, 0.0::numeric AS total_score, 0.0::numeric AS total_amount FROM mv_research_faculty_summary
UNION ALL
SELECT 'patent' AS category, SUM(total_patents) AS count, 0.0::numeric AS total_score, 0.0::numeric AS total_amount FROM mv_research_faculty_summary
UNION ALL
SELECT 'research_project' AS category, SUM(total_projects) AS count, 0.0::numeric AS total_score, SUM(total_funding) AS total_amount FROM mv_research_faculty_summary
UNION ALL
SELECT 'research_proposal' AS category, SUM(total_proposals) AS count, 0.0::numeric AS total_score, SUM(total_proposal_amount) AS total_amount FROM mv_research_faculty_summary;

-- 6. Data Quality Summary Materialized View
DROP MATERIALIZED VIEW IF EXISTS mv_research_data_quality_summary CASCADE;
CREATE MATERIALIZED VIEW mv_research_data_quality_summary AS
SELECT
  (SELECT COUNT(*) FROM journal_publications WHERE NULLIF(TRIM(title), '') IS NULL) AS publications_with_missing_titles,
  (SELECT COUNT(*) FROM book_publications WHERE NULLIF(TRIM(isbn), '') IS NULL) AS books_with_missing_isbn,
  (SELECT COUNT(*) FROM journal_publications WHERE NULLIF(TRIM(issn), '') IS NULL) AS journal_publications_with_missing_issn,
  (SELECT COUNT(*) FROM journal_publications WHERE NULLIF(TRIM(indexing), '') IS NULL) AS publications_with_missing_indexing,
  (SELECT COUNT(*) FROM patents WHERE NULLIF(TRIM(patent_status), '') IS NULL) AS patents_with_missing_status,
  (SELECT COUNT(*) FROM research_projects WHERE amount IS NULL) AS projects_with_missing_funding_amount,
  (SELECT COUNT(*) FROM journal_publications jp LEFT JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(jp.faculty_email)) WHERE fp.email IS NULL) AS records_without_matching_faculty_email,
  (SELECT COUNT(*) FROM faculty_profiles WHERE NULLIF(TRIM(department), '') IS NULL) AS blank_or_null_departments,
  (SELECT COUNT(*) FROM faculty_profiles WHERE NULLIF(TRIM(academic_year), '') IS NULL) AS unknown_academic_years;

-- 7. Filter Options Materialized View
DROP MATERIALIZED VIEW IF EXISTS mv_research_filter_options CASCADE;
CREATE MATERIALIZED VIEW mv_research_filter_options AS
SELECT
  (SELECT ARRAY_AGG(DISTINCT academic_year ORDER BY academic_year) FROM faculty_profiles WHERE NULLIF(TRIM(academic_year::text), '') IS NOT NULL) AS academic_years,
  (SELECT ARRAY_AGG(DISTINCT school ORDER BY school) FROM faculty_profiles WHERE NULLIF(TRIM(school), '') IS NOT NULL) AS schools,
  (SELECT ARRAY_AGG(DISTINCT department ORDER BY department) FROM faculty_profiles WHERE NULLIF(TRIM(department), '') IS NOT NULL) AS departments,
  (SELECT ARRAY_AGG(DISTINCT designation ORDER BY designation) FROM faculty_profiles WHERE NULLIF(TRIM(designation), '') IS NOT NULL) AS designations,
  (SELECT ARRAY_AGG(DISTINCT indexing ORDER BY indexing) FROM journal_publications WHERE NULLIF(TRIM(indexing), '') IS NOT NULL) AS indexing_options;
