import duckdb
import os
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from loguru import logger
from app.core.config import settings
import atexit


class DuckDBManager:
    def __init__(self):
        self.connection: Optional[duckdb.DuckDBPyConnection] = None
        self.database_path = settings.DATABASE_PATH
        self._initialize_database()
        atexit.register(self.close)

    def _initialize_database(self):
        try:
            os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
            logger.debug(f"Database path resolved to: {self.database_path}")

            if settings.DATABASE_MEMORY:
                self.connection = duckdb.connect(":memory:")
                logger.info("Connected to in-memory DuckDB database")
            else:
                # Safety check: If file exists but is invalid, delete and recreate
                if os.path.exists(self.database_path):
                    try:
                        test_conn = duckdb.connect(self.database_path)
                        test_conn.close()
                    except duckdb.IOException:
                        logger.warning(f"Invalid DuckDB file detected at {self.database_path}. Deleting and recreating.")
                        os.remove(self.database_path)

                self.connection = duckdb.connect(self.database_path)
                logger.info(f"Connected to DuckDB database at {self.database_path}")

            self._create_schema()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _create_schema(self):
        schema_sql = """
        CREATE TABLE IF NOT EXISTS stocks (
            symbol VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            exchange VARCHAR NOT NULL,
            sector VARCHAR,
            industry VARCHAR,
            isin VARCHAR,
            market_cap BIGINT,
            segment VARCHAR,
            listing_date DATE,
            face_value DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY,
            symbol VARCHAR NOT NULL,
            exchange VARCHAR NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            change_amount DECIMAL(10,2),
            change_percent DECIMAL(5,2),
            volume BIGINT,
            value BIGINT,
            high DECIMAL(10,2),
            low DECIMAL(10,2),
            open DECIMAL(10,2),
            close DECIMAL(10,2),
            bid DECIMAL(10,2),
            ask DECIMAL(10,2),
            delivery_qty BIGINT,
            delivery_percent DECIMAL(5,2),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_source VARCHAR DEFAULT 'API',
            FOREIGN KEY (symbol) REFERENCES stocks(symbol)
        );
        CREATE TABLE IF NOT EXISTS gold_rates (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            city VARCHAR NOT NULL DEFAULT 'Coimbatore',
            purity VARCHAR NOT NULL DEFAULT '22K',
            rate_per_gram DECIMAL(10,2) NOT NULL,
            rate_per_10g DECIMAL(10,2) NOT NULL,
            change_amount DECIMAL(10,2),
            change_percent DECIMAL(5,2),
            previous_rate DECIMAL(10,2),
            data_source VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, city, purity)
        );
        CREATE TABLE IF NOT EXISTS data_quality_log (
            id INTEGER PRIMARY KEY,
            source VARCHAR NOT NULL,
            check_type VARCHAR NOT NULL,
            status VARCHAR NOT NULL,
            details JSON,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS system_health (
            id INTEGER PRIMARY KEY,
            component VARCHAR NOT NULL,
            status VARCHAR NOT NULL,
            response_time_ms INTEGER,
            error_message TEXT,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY,
            user_id VARCHAR,
            symbol VARCHAR NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (symbol) REFERENCES stocks(symbol)
        );
        CREATE INDEX IF NOT EXISTS idx_quotes_symbol_timestamp ON quotes(symbol, timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_quotes_timestamp ON quotes(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_stocks_exchange ON stocks(exchange);
        CREATE INDEX IF NOT EXISTS idx_stocks_sector ON stocks(sector);
        CREATE INDEX IF NOT EXISTS idx_gold_rates_date ON gold_rates(date DESC);
        CREATE INDEX IF NOT EXISTS idx_data_quality_checked_at ON data_quality_log(checked_at DESC);
        """
        try:
            statements = [stmt.strip() for stmt in schema_sql.strip().split(";") if stmt.strip()]
            for statement in statements:
                self.connection.execute(statement)
            logger.info("Database schema created successfully")
        except Exception as e:
            logger.error(f"Failed to create database schema: {e}")
            raise

    @contextmanager
    def get_connection(self):
        try:
            yield self.connection
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        try:
            with self.get_connection() as conn:
                result = conn.execute(query, params) if params else conn.execute(query)
                columns = [desc[0] for desc in result.description]
                rows = result.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Query execution failed: {query[:100]}... Error: {e}")
            raise

    def execute_insert(self, query: str, params: Optional[Dict] = None) -> int:
        try:
            with self.get_connection() as conn:
                result = conn.execute(query, params) if params else conn.execute(query)
                return result.rowcount
        except Exception as e:
            logger.error(f"Insert execution failed: {query[:100]}... Error: {e}")
            raise

    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


db_manager = DuckDBManager()

def get_db() -> DuckDBManager:
    return db_manager
