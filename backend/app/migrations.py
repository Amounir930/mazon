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

        # ==========================================
        # Migration 5: Create orders table (Cookie Scraping)
        # ==========================================
        if "orders" not in existing_tables:
            logger.info("Migration: Creating 'orders' table...")
            conn.execute(text("""
                CREATE TABLE orders (
                    id VARCHAR(36) PRIMARY KEY,
                    seller_id VARCHAR(36),
                    amazon_order_id VARCHAR(50) NOT NULL UNIQUE,
                    merchant_order_id VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    purchase_date TIMESTAMP,
                    last_update_date TIMESTAMP,
                    order_status VARCHAR(30) DEFAULT 'Pending',
                    fulfillment_channel VARCHAR(20) DEFAULT 'MFN',
                    sales_channel VARCHAR(50),
                    buyer_name VARCHAR(200),
                    buyer_email VARCHAR(200),
                    buyer_phone VARCHAR(50),
                    ship_address TEXT,
                    ship_city VARCHAR(100),
                    ship_state VARCHAR(100),
                    ship_postal_code VARCHAR(20),
                    ship_country VARCHAR(10),
                    total NUMERIC(10, 2) DEFAULT 0,
                    item_total NUMERIC(10, 2) DEFAULT 0,
                    shipping_total NUMERIC(10, 2) DEFAULT 0,
                    tax_total NUMERIC(10, 2) DEFAULT 0,
                    currency VARCHAR(10) DEFAULT 'EGP',
                    items TEXT,
                    raw_data TEXT,
                    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source VARCHAR(20) DEFAULT 'cookie',
                    FOREIGN KEY (seller_id) REFERENCES sellers(id)
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_seller_id ON orders(seller_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_amazon_order_id ON orders(amazon_order_id)"))
            logger.info("Migration: 'orders' table created")

        # ==========================================
        # Migration 6: Create inventory table (Cookie Scraping)
        # ==========================================
        if "inventory" not in existing_tables:
            logger.info("Migration: Creating 'inventory' table...")
            conn.execute(text("""
                CREATE TABLE inventory (
                    id VARCHAR(36) PRIMARY KEY,
                    seller_id VARCHAR(36),
                    product_id VARCHAR(36),
                    sku VARCHAR(100) NOT NULL,
                    asin VARCHAR(20),
                    product_name VARCHAR(500),
                    available INTEGER DEFAULT 0,
                    reserved INTEGER DEFAULT 0,
                    inbound INTEGER DEFAULT 0,
                    unfulfillable INTEGER DEFAULT 0,
                    fulfillment_channel VARCHAR(20) DEFAULT 'MFN',
                    fba BOOLEAN DEFAULT FALSE,
                    fbm BOOLEAN DEFAULT TRUE,
                    price NUMERIC(10, 2) DEFAULT 0,
                    currency VARCHAR(10) DEFAULT 'EGP',
                    status VARCHAR(30) DEFAULT 'Active',
                    raw_data TEXT,
                    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source VARCHAR(20) DEFAULT 'cookie',
                    FOREIGN KEY (seller_id) REFERENCES sellers(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_inventory_seller_id ON inventory(seller_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_inventory_product_id ON inventory(product_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_inventory_sku ON inventory(sku)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_inventory_asin ON inventory(asin)"))
            logger.info("Migration: 'inventory' table created")

        # ==========================================
        # Migration 7: Add browse_node_id to products (FIX)
        # ==========================================
        if "products" in existing_tables:
            _add_column_if_missing(conn, "products", "browse_node_id", "VARCHAR(50)")

        # ==========================================
        # Migration 8: Add sale_price to products (FIX)
        # ==========================================
        if "products" in existing_tables:
            _add_column_if_missing(conn, "products", "sale_price", "NUMERIC(10, 2)")
            _add_column_if_missing(conn, "products", "sale_start_date", "TIMESTAMP")
            _add_column_if_missing(conn, "products", "sale_end_date", "TIMESTAMP")
            _add_column_if_missing(conn, "products", "compare_price", "NUMERIC(10, 2)")
            _add_column_if_missing(conn, "products", "cost", "NUMERIC(10, 2)")

        # ==========================================
        # Migration 9: Add parent_sku and is_parent to products (FIX)
        # ==========================================
        if "products" in existing_tables:
            _add_column_if_missing(conn, "products", "parent_sku", "VARCHAR(100)")
            _add_column_if_missing(conn, "products", "is_parent", "BOOLEAN DEFAULT FALSE")
            _add_column_if_missing(conn, "products", "name_ar", "VARCHAR(500)")
            _add_column_if_missing(conn, "products", "name_en", "VARCHAR(500)")
            _add_column_if_missing(conn, "products", "description_ar", "TEXT")
            _add_column_if_missing(conn, "products", "description_en", "TEXT")
            _add_column_if_missing(conn, "products", "bullet_points_ar", "TEXT DEFAULT '[]'")
            _add_column_if_missing(conn, "products", "bullet_points_en", "TEXT DEFAULT '[]'")
            _add_column_if_missing(conn, "products", "keywords", "TEXT DEFAULT '[]'")
            _add_column_if_missing(conn, "products", "weight", "NUMERIC(8, 2)")
            _add_column_if_missing(conn, "products", "dimensions", "TEXT DEFAULT '{}'")
            _add_column_if_missing(conn, "products", "optimized_data", "TEXT")

        # ==========================================
        # Migration 10: Add name_ar to products (FIX)
        # ==========================================
        if "products" in existing_tables:
            _add_column_if_missing(conn, "products", "name_ar", "VARCHAR(500)")

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
