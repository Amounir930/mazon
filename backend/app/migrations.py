"""
Database Migration Script
Handles schema evolution for SQLite (which doesn't support ALTER TABLE well)

This script checks for missing columns/tables and adds them incrementally.
Safe to run multiple times — idempotent.
"""
from sqlalchemy import text, inspect
from loguru import logger


def run_migrations(engine) -> None:
    """
    Run incremental database migrations.
    Checks for missing columns and tables, then adds them.
    """
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    with engine.connect() as conn:
        # ==========================================
        # Migration 1: Add 'currency' to products
        # ==========================================
        if "products" in existing_tables:
            _add_column_if_missing(conn, "products", "currency", "VARCHAR(10) DEFAULT 'EGP'")

        # ==========================================
        # Migration 2: Add Amazon fields to products
        # ==========================================
        if "products" in existing_tables:
            _add_column_if_missing(conn, "products", "condition", "VARCHAR(20) DEFAULT 'New'")
            _add_column_if_missing(conn, "products", "fulfillment_channel", "VARCHAR(20) DEFAULT 'MFN'")
            _add_column_if_missing(conn, "products", "handling_time", "INTEGER DEFAULT 0")
            _add_column_if_missing(conn, "products", "product_type", "VARCHAR(100)")
            _add_column_if_missing(conn, "products", "manufacturer", "VARCHAR(200)")
            _add_column_if_missing(conn, "products", "model_number", "VARCHAR(100)")
            _add_column_if_missing(conn, "products", "country_of_origin", "VARCHAR(10)")
            _add_column_if_missing(conn, "products", "package_quantity", "INTEGER DEFAULT 1")

        # ==========================================
        # Migration 3: Add stage + retry_count to listings
        # ==========================================
        if "listings" in existing_tables:
            _add_column_if_missing(conn, "listings", "stage", "VARCHAR(20) DEFAULT 'queued'")
            _add_column_if_missing(conn, "listings", "retry_count", "INTEGER DEFAULT 0")

        # ==========================================
        # Migration 4: Create activity_logs table
        # ==========================================
        if "activity_logs" not in existing_tables:
            logger.info("Migration: Creating 'activity_logs' table...")
            conn.execute(text("""
                CREATE TABLE activity_logs (
                    id VARCHAR(36) PRIMARY KEY,
                    product_id VARCHAR(36) NOT NULL,
                    listing_id VARCHAR(36),
                    action VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    FOREIGN KEY (listing_id) REFERENCES listings(id)
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_activity_logs_product_id ON activity_logs(product_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_activity_logs_listing_id ON activity_logs(listing_id)"))
            logger.info("Migration: 'activity_logs' table created")

        conn.commit()

    logger.info("Database migration completed successfully")


def _add_column_if_missing(conn, table_name: str, column_name: str, column_def: str) -> None:
    """Add a column to a table if it doesn't exist (idempotent)"""
    from sqlalchemy import inspect
    inspector = inspect(conn.engine)
    columns = [col["name"] for col in inspector.get_columns(table_name)]

    if column_name not in columns:
        logger.info(f"Migration: Adding column '{column_name}' to '{table_name}'")
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"))
    else:
        logger.debug(f"Migration: Column '{column_name}' already exists in '{table_name}'")
