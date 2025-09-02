from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Elite Stock Recommendation Engine"
    VERSION: str = "0.2R"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATABASE_PATH: str = "data/elite_stock.db"
    AUTO_REFRESH_INTERVAL: int = 15
    MANUAL_REFRESH_ENABLED: bool = True
    DATA_STALENESS_THRESHOLD: int = 300
    NSE_BASE_URL: str = "https://www.nseindia.com"
    BSE_BASE_URL: str = "https://www.bseindia.com"
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    GOLD_CITY: str = "Coimbatore"
    GOLD_PURITY: str = "22K"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 30
    GX_ROOT_DIRECTORY: str = "app/validation/great_expectations"
    GX_ENABLE_VALIDATION: bool = True
    GX_FAIL_ON_VALIDATION_ERROR: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/elite_stock.log"
    RATE_LIMIT_PER_MINUTE: int = 60
    SCHEDULER_ENABLED: bool = True
    DATA_REFRESH_CRON: str = "*/15 * * * * *"
    HEALTH_CHECK_CRON: str = "*/30 * * * * *"
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

settings = Settings()

# NSE Endpoints
NSE_ENDPOINTS = {
    "market_status": "/api/marketStatus",
    "all_indices": "/api/allIndices",
    "equity_master": "/api/master-quote",
    "option_chain": "/api/option-chain-indices?symbol=NIFTY",
    "equity_info": "/api/quote-equity?symbol=",
    "market_data": "/api/marketData",
}

# BSE Endpoints
BSE_ENDPOINTS = {
    "market_status": "/markets.html",
    "sensex_data": "/sensex/code/16/",
    "equity_info": "/stock-share-price/",
    "corporate_info": "/corporates/",
}

# Gold Rate Sources
GOLD_SOURCES = {
    "primary": "https://www.goodreturns.in/gold-rates/coimbatore.html",
    "secondary": "https://www.bajajfinserv.in/gold-rate-today-in-coimbatore",
    "tertiary": "https://www.candere.com/gold-rate-today/coimbatore"
}
