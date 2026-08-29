-- =============================================================================
-- POSTGRESQL OLTP INITIALIZATION (CLEAN BASE)
-- =============================================================================
-- Add your custom schemas, tables and DDLs below:

DROP PUBLICATION IF EXISTS dbz_publication;
CREATE PUBLICATION dbz_publication FOR ALL TABLES;
