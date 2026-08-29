-- =============================================================================
-- POSTGRESQL OLTP INITIALIZATION (CDC & LOGICAL REPLICATION)
-- =============================================================================
-- This script runs once on database initialization.
-- Add your schemas, DDL tables, indexes, and initial data below.

-- 1. Enable Logical Replication Publication for Debezium CDC
DROP PUBLICATION IF EXISTS dbz_publication;
CREATE PUBLICATION dbz_publication FOR ALL TABLES;

-- 2. Your custom schemas, tables and DDLs:
-- (Define your tables below. Remember to set REPLICA IDENTITY FULL if you want full before/after images)
-- Example:
-- CREATE SCHEMA IF NOT EXISTS ecommerce;
-- CREATE TABLE ecommerce.my_table (...);
-- ALTER TABLE ecommerce.my_table REPLICA IDENTITY FULL;
