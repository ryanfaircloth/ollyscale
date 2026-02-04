-- Attribute Key Analysis
-- This SQL script analyzes all JSONB attribute columns in the current schema
-- to help plan the migration to typed attribute tables.
--
-- For each key, it reports:
-- - Key name
-- - Detected type(s)
-- - Total occurrence count
-- - Distinct value count (cardinality)
-- - Source table/column
--
-- Use this information to decide:
-- 1. Which keys to promote to typed tables (high frequency)
-- 2. Which indexing strategy to use (based on cardinality)
-- 3. Proper type mapping for each key

-- =============================================================================
-- RESOURCE ATTRIBUTES ANALYSIS
-- =============================================================================

-- Resource attributes from resource_dim.attributes
CREATE TEMP TABLE resource_attr_analysis AS
SELECT
    'resource_dim' as source_table,
    'attributes' as source_column,
    key,
    jsonb_typeof(value) as detected_type,
    COUNT(*) as occurrence_count,
    COUNT(DISTINCT value) as distinct_value_count,
    -- Sample values for manual inspection
    MIN(value #>> '{}') as sample_value_1,
    (array_agg(DISTINCT value #>> '{}' ORDER BY value #>> '{}'))[2] as sample_value_2
FROM resource_dim,
    LATERAL jsonb_each(attributes) as attrs(key, value)
WHERE attributes IS NOT NULL AND attributes != '{}'::jsonb
GROUP BY key, jsonb_typeof(value)
ORDER BY occurrence_count DESC, key;

-- Resource attributes from spans_fact.resource
INSERT INTO resource_attr_analysis
SELECT
    'spans_fact' as source_table,
    'resource' as source_column,
    key,
    jsonb_typeof(value) as detected_type,
    COUNT(*) as occurrence_count,
    COUNT(DISTINCT value) as distinct_value_count,
    MIN(value #>> '{}') as sample_value_1,
    (array_agg(DISTINCT value #>> '{}' ORDER BY value #>> '{}'))[2] as sample_value_2
FROM spans_fact,
    LATERAL jsonb_each(resource) as attrs(key, value)
WHERE resource IS NOT NULL AND resource != '{}'::jsonb
GROUP BY key, jsonb_typeof(value);

-- Resource attributes from logs_fact.resource
INSERT INTO resource_attr_analysis
SELECT
    'logs_fact' as source_table,
    'resource' as source_column,
    key,
    jsonb_typeof(value) as detected_type,
    COUNT(*) as occurrence_count,
    COUNT(DISTINCT value) as distinct_value_count,
    MIN(value #>> '{}') as sample_value_1,
    (array_agg(DISTINCT value #>> '{}' ORDER BY value #>> '{}'))[2] as sample_value_2
FROM logs_fact,
    LATERAL jsonb_each(resource) as attrs(key, value)
WHERE resource IS NOT NULL AND resource != '{}'::jsonb
GROUP BY key, jsonb_typeof(value);

-- Resource attributes from metrics_fact.resource
INSERT INTO resource_attr_analysis
SELECT
    'metrics_fact' as source_table,
    'resource' as source_column,
    key,
    jsonb_typeof(value) as detected_type,
    COUNT(*) as occurrence_count,
    COUNT(DISTINCT value) as distinct_value_count,
    MIN(value #>> '{}') as sample_value_1,
    (array_agg(DISTINCT value #>> '{}' ORDER BY value #>> '{}'))[2] as sample_value_2
FROM metrics_fact,
    LATERAL jsonb_each(resource) as attrs(key, value)
WHERE resource IS NOT NULL AND resource != '{}'::jsonb
GROUP BY key, jsonb_typeof(value);

-- Aggregate resource attributes across all sources
SELECT
    key,
    detected_type,
    SUM(occurrence_count) as total_occurrences,
    MAX(distinct_value_count) as max_distinct_values,
    STRING_AGG(DISTINCT source_table || '.' || source_column, ', ') as found_in,
    MIN(sample_value_1) as sample_value_1,
    MIN(sample_value_2) as sample_value_2
FROM resource_attr_analysis
GROUP BY key, detected_type
ORDER BY total_occurrences DESC, key;

-- =============================================================================
-- SCOPE ATTRIBUTES ANALYSIS
-- =============================================================================

CREATE TEMP TABLE scope_attr_analysis AS
SELECT
    'spans_fact' as source_table,
    'scope' as source_column,
    key,
    jsonb_typeof(value) as detected_type,
    COUNT(*) as occurrence_count,
    COUNT(DISTINCT value) as distinct_value_count,
    MIN(value #>> '{}') as sample_value_1,
    (array_agg(DISTINCT value #>> '{}' ORDER BY value #>> '{}'))[2] as sample_value_2
FROM spans_fact,
    LATERAL jsonb_each(scope) as attrs(key, value)
WHERE scope IS NOT NULL AND scope != '{}'::jsonb
GROUP BY key, jsonb_typeof(value);

-- Scope from logs_fact
INSERT INTO scope_attr_analysis
SELECT
    'logs_fact' as source_table,
    'scope' as source_column,
    key,
    jsonb_typeof(value) as detected_type,
    COUNT(*) as occurrence_count,
    COUNT(DISTINCT value) as distinct_value_count,
    MIN(value #>> '{}') as sample_value_1,
    (array_agg(DISTINCT value #>> '{}' ORDER BY value #>> '{}'))[2] as sample_value_2
FROM logs_fact,
    LATERAL jsonb_each(scope) as attrs(key, value)
WHERE scope IS NOT NULL AND scope != '{}'::jsonb
GROUP BY key, jsonb_typeof(value);

-- Scope from metrics_fact
INSERT INTO scope_attr_analysis
SELECT
    'metrics_fact' as source_table,
    'scope' as source_column,
    key,
    jsonb_typeof(value) as detected_type,
    COUNT(*) as occurrence_count,
    COUNT(DISTINCT value) as distinct_value_count,
    MIN(value #>> '{}') as sample_value_1,
    (array_agg(DISTINCT value #>> '{}' ORDER BY value #>> '{}'))[2] as sample_value_2
FROM metrics_fact,
    LATERAL jsonb_each(scope) as attrs(key, value)
WHERE scope IS NOT NULL AND scope != '{}'::jsonb
GROUP BY key, jsonb_typeof(value);

-- Aggregate scope attributes
SELECT
    key,
    detected_type,
    SUM(occurrence_count) as total_occurrences,
    MAX(distinct_value_count) as max_distinct_values,
    STRING_AGG(DISTINCT source_table || '.' || source_column, ', ') as found_in,
    MIN(sample_value_1) as sample_value_1,
    MIN(sample_value_2) as sample_value_2
FROM scope_attr_analysis
GROUP BY key, detected_type
ORDER BY total_occurrences DESC, key;

-- =============================================================================
-- SPAN ATTRIBUTES ANALYSIS
-- =============================================================================

SELECT
    'spans_fact' as source_table,
    'attributes' as source_column,
    key,
    jsonb_typeof(value) as detected_type,
    COUNT(*) as occurrence_count,
    COUNT(DISTINCT value) as distinct_value_count,
    MIN(value #>> '{}') as sample_value_1,
    (array_agg(DISTINCT value #>> '{}' ORDER BY value #>> '{}'))[2] as sample_value_2
FROM spans_fact,
    LATERAL jsonb_each(attributes) as attrs(key, value)
WHERE attributes IS NOT NULL AND attributes != '{}'::jsonb
GROUP BY key, jsonb_typeof(value)
ORDER BY occurrence_count DESC, key;

-- =============================================================================
-- LOG ATTRIBUTES ANALYSIS
-- =============================================================================

SELECT
    'logs_fact' as source_table,
    'attributes' as source_column,
    key,
    jsonb_typeof(value) as detected_type,
    COUNT(*) as occurrence_count,
    COUNT(DISTINCT value) as distinct_value_count,
    MIN(value #>> '{}') as sample_value_1,
    (array_agg(DISTINCT value #>> '{}' ORDER BY value #>> '{}'))[2] as sample_value_2
FROM logs_fact,
    LATERAL jsonb_each(attributes) as attrs(key, value)
WHERE attributes IS NOT NULL AND attributes != '{}'::jsonb
GROUP BY key, jsonb_typeof(value)
ORDER BY occurrence_count DESC, key;

-- =============================================================================
-- METRIC ATTRIBUTES ANALYSIS
-- =============================================================================

SELECT
    'metrics_fact' as source_table,
    'attributes' as source_column,
    key,
    jsonb_typeof(value) as detected_type,
    COUNT(*) as occurrence_count,
    COUNT(DISTINCT value) as distinct_value_count,
    MIN(value #>> '{}') as sample_value_1,
    (array_agg(DISTINCT value #>> '{}' ORDER BY value #>> '{}'))[2] as sample_value_2
FROM metrics_fact,
    LATERAL jsonb_each(attributes) as attrs(key, value)
WHERE attributes IS NOT NULL AND attributes != '{}'::jsonb
GROUP BY key, jsonb_typeof(value)
ORDER BY occurrence_count DESC, key;

-- =============================================================================
-- SERVICE ATTRIBUTES ANALYSIS
-- =============================================================================

SELECT
    'service_dim' as source_table,
    'attributes' as source_column,
    key,
    jsonb_typeof(value) as detected_type,
    COUNT(*) as occurrence_count,
    COUNT(DISTINCT value) as distinct_value_count,
    MIN(value #>> '{}') as sample_value_1,
    (array_agg(DISTINCT value #>> '{}' ORDER BY value #>> '{}'))[2] as sample_value_2
FROM service_dim,
    LATERAL jsonb_each(attributes) as attrs(key, value)
WHERE attributes IS NOT NULL AND attributes != '{}'::jsonb
GROUP BY key, jsonb_typeof(value)
ORDER BY occurrence_count DESC, key;

-- =============================================================================
-- SUMMARY: TOP CANDIDATE KEYS FOR TYPED TABLES
-- =============================================================================

-- Keys that appear frequently and should be considered for typed tables
-- Combine all attribute sources and identify high-frequency keys

CREATE TEMP TABLE all_keys AS
SELECT key, detected_type, occurrence_count, distinct_value_count, 'resource' as context
FROM resource_attr_analysis
UNION ALL
SELECT key, detected_type, occurrence_count, distinct_value_count, 'scope' as context
FROM scope_attr_analysis
UNION ALL
SELECT key, detected_type, occurrence_count, distinct_value_count, 'span' as context
FROM (
    SELECT key, jsonb_typeof(value) as detected_type, COUNT(*) as occurrence_count, COUNT(DISTINCT value) as distinct_value_count
    FROM spans_fact, LATERAL jsonb_each(attributes) as attrs(key, value)
    WHERE attributes IS NOT NULL AND attributes != '{}'::jsonb
    GROUP BY key, jsonb_typeof(value)
) span_attrs
UNION ALL
SELECT key, detected_type, occurrence_count, distinct_value_count, 'log' as context
FROM (
    SELECT key, jsonb_typeof(value) as detected_type, COUNT(*) as occurrence_count, COUNT(DISTINCT value) as distinct_value_count
    FROM logs_fact, LATERAL jsonb_each(attributes) as attrs(key, value)
    WHERE attributes IS NOT NULL AND attributes != '{}'::jsonb
    GROUP BY key, jsonb_typeof(value)
) log_attrs
UNION ALL
SELECT key, detected_type, occurrence_count, distinct_value_count, 'metric' as context
FROM (
    SELECT key, jsonb_typeof(value) as detected_type, COUNT(*) as occurrence_count, COUNT(DISTINCT value) as distinct_value_count
    FROM metrics_fact, LATERAL jsonb_each(attributes) as attrs(key, value)
    WHERE attributes IS NOT NULL AND attributes != '{}'::jsonb
    GROUP BY key, jsonb_typeof(value)
) metric_attrs;

-- Final summary: top keys by occurrence
SELECT
    key,
    detected_type,
    SUM(occurrence_count) as total_occurrences,
    MAX(distinct_value_count) as max_distinct_values,
    STRING_AGG(DISTINCT context, ', ') as used_in_contexts,
    -- Recommendation based on frequency
    CASE
        WHEN SUM(occurrence_count) > 10000 THEN 'HIGH-PRIORITY: Promote to typed table'
        WHEN SUM(occurrence_count) > 1000 THEN 'MEDIUM-PRIORITY: Consider promoting'
        ELSE 'LOW-PRIORITY: Keep in JSONB catch-all'
    END as recommendation,
    -- Index recommendation based on cardinality
    CASE
        WHEN MAX(distinct_value_count) < 100 THEN 'Low cardinality - good for B-tree index'
        WHEN MAX(distinct_value_count) < 10000 THEN 'Medium cardinality - B-tree index OK'
        ELSE 'High cardinality - index may be expensive'
    END as index_recommendation
FROM all_keys
GROUP BY key, detected_type
ORDER BY total_occurrences DESC, key
LIMIT 100;

-- =============================================================================
-- TYPE CONSISTENCY CHECK
-- =============================================================================

-- Check if any keys have multiple detected types (type inconsistency)
SELECT
    key,
    STRING_AGG(DISTINCT detected_type, ', ') as detected_types,
    COUNT(DISTINCT detected_type) as type_count,
    STRING_AGG(DISTINCT context, ', ') as contexts
FROM all_keys
GROUP BY key
HAVING COUNT(DISTINCT detected_type) > 1
ORDER BY type_count DESC, key;

-- Cleanup temporary tables
DROP TABLE resource_attr_analysis;
DROP TABLE scope_attr_analysis;
DROP TABLE all_keys;
