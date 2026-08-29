"""
Integration Tests: PostgreSQL OLTP Database & Logical Replication (CDC)
"""

import pytest
import psycopg2


@pytest.mark.integration
class TestPostgresCDCIntegration:
    """Integration test suite for PostgreSQL and CDC publication."""

    def test_postgres_connection_and_version(self, pg_connection):
        with pg_connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version_str = cursor.fetchone()[0]
            assert "PostgreSQL" in version_str
            assert ("16." in version_str or "15." in version_str or "14." in version_str)

    def test_wal_level_is_logical(self, pg_connection):
        """Verifies that WAL level is set to 'logical' for Debezium CDC."""
        with pg_connection.cursor() as cursor:
            cursor.execute("SHOW wal_level;")
            wal_level = cursor.fetchone()[0]
            assert wal_level.lower() == "logical", f"wal_level must be 'logical', got: {wal_level}"

    def test_dbz_publication_exists(self, pg_connection):
        """Verifies that the publication for CDC events is registered."""
        with pg_connection.cursor() as cursor:
            cursor.execute("SELECT pubname FROM pg_publication WHERE pubname = 'dbz_publication';")
            result = cursor.fetchone()
            assert result is not None, "Publication 'dbz_publication' not found in PostgreSQL"

    def test_insert_and_replica_identity(self, pg_connection):
        """Tests CRUD operations and REPLICA IDENTITY settings."""
        with pg_connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ecommerce.test_orders (
                    id SERIAL PRIMARY KEY,
                    item_name VARCHAR(50),
                    amount NUMERIC(10, 2)
                );
                ALTER TABLE ecommerce.test_orders REPLICA IDENTITY FULL;
            """)

            cursor.execute("INSERT INTO ecommerce.test_orders (item_name, amount) VALUES ('Test Item', 99.50) RETURNING id;")
            inserted_id = cursor.fetchone()[0]
            assert inserted_id is not None

            cursor.execute("SELECT item_name, amount FROM ecommerce.test_orders WHERE id = %s;", (inserted_id,))
            row = cursor.fetchone()
            assert row[0] == "Test Item"
            assert float(row[1]) == 99.50

            cursor.execute("DROP TABLE ecommerce.test_orders;")
