-- =============================================================================
-- POSTGRESQL OLTP INITIALIZATION (CLEAN BASE)
-- =============================================================================

DROP PUBLICATION IF EXISTS dbz_publication;
CREATE PUBLICATION dbz_publication FOR ALL TABLES;

