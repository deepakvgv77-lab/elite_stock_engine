from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

class Exchange(str, Enum):
    NSE = "NSE"
    BSE = "BSE"

class Segment(str, Enum):
    MAINBOARD = "mainboard"
    SME = "SME"
    EMERGE = "emerge"
    STAR_MF = "Star MF"

class DataSource(str, Enum):
    NSE_API = "NSE_API"
    BSE_HTML = "BSE_HTML"
    GOLD_WEBSITE = "GOLD_WEBSITE"
    MANUAL = "MANUAL"

class HealthStatus(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    DEGRADED = "DEGRADED"

class TimestampedModel(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class StockBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    exchange: Exchange
    sector: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    isin: Optional[str] = Field(None, regex=r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")

class Stock(StockBase, TimestampedModel):
    market_cap: Optional[int] = Field(None, ge=0)
    segment: Optional[Segment] = None
    listing_date: Optional[date] = None
    face_value: Optional[Decimal] = Field(None, ge=0)

class QuoteBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    exchange: Exchange
    price: Decimal = Field(..., gt=0)
    change_amount: Optional[Decimal] = None
    change_percent: Optional[Decimal] = Field(None, ge=-100, le=100)
    volume: Optional[int] = Field(None, ge=0)
    value: Optional[int] = Field(None, ge=0)

class Quote(QuoteBase, TimestampedModel):
    id: Optional[int] = None
    high: Optional[Decimal] = Field(None, gt=0)
    low: Optional[Decimal] = Field(None, gt=0)
    open: Optional[Decimal] = Field(None, gt=0)
    close: Optional[Decimal] = Field(None, gt=0)
    bid: Optional[Decimal] = Field(None, gt=0)
    ask: Optional[Decimal] = Field(None, gt=0)
    delivery_qty: Optional[int] = Field(None, ge=0)
    delivery_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    timestamp: Optional[datetime] = None
    data_source: Optional[DataSource] = DataSource.NSE_API

    @validator('high', 'low', 'open', 'close')
    def validate_ohlc(cls, v, values):
        if v is not None and 'price' in values:
            if v > values['price'] * 2 or v < values['price'] * 0.5:
                raise ValueError(f"OHLC value {v} inconsistent with price {values['price']}")
        return v

class GoldRateBase(BaseModel):
    date: date
    city: str = Field(default="Coimbatore", max_length=50)
    purity: str = Field(default="22K")
    rate_per_gram: Decimal = Field(..., gt=0)
    rate_per_10g: Decimal = Field(..., gt=0)

class GoldRate(GoldRateBase, TimestampedModel):
    id: Optional[int] = None
    change_amount: Optional[Decimal] = None
    change_percent: Optional[Decimal] = Field(None, ge=-50, le=50)
    previous_rate: Optional[Decimal] = Field(None, gt=0)
    data_source: Optional[str] = Field(None, max_length=100)

    @validator('rate_per_10g')
    def validate_10g_rate(cls, v, values):
        if 'rate_per_gram' in values:
            expected_10g = values['rate_per_gram'] * 10
            if abs(v - expected_10g) > expected_10g * 0.01:
                raise ValueError(f"10g rate {v} inconsistent with per gram rate {values['rate_per_gram']}")
        return v

class DataQualityCheck(BaseModel):
    id: Optional[int] = None
    source: str = Field(..., max_length=50)
    check_type: str = Field(..., max_length=50)
    status: str = Field(..., regex=r"^(PASSED|FAILED)$")
    details: Optional[Dict[str, Any]] = None
    checked_at: Optional[datetime] = None

class SystemHealthCheck(BaseModel):
    id: Optional[int] = None
    component: str = Field(..., max_length=50)
    status: HealthStatus
    response_time_ms: Optional[int] = Field(None, ge=0)
    error_message: Optional[str] = None
    checked_at: Optional[datetime] = None

class WatchlistItem(BaseModel):
    id: Optional[int] = None
    user_id: Optional[str] = Field(None, max_length=50)
    symbol: str = Field(..., min_length=1, max_length=20)
    added_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)

class QuoteResponse(BaseModel):
    symbol: str
    name: Optional[str] = None
    exchange: Exchange
    price: Decimal
    change_amount: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    volume: Optional[int] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    timestamp: Optional[datetime] = None
    staleness_minutes: Optional[int] = None

class GoldRateResponse(BaseModel):
    date: date
    city: str
    purity: str
    rate_per_gram: Decimal
    rate_per_10g: Decimal
    change_amount: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    trend_direction: Optional[str] = None
    data_source: Optional[str] = None

class UniverseStatsResponse(BaseModel):
    total_stocks: int
    nse_stocks: int
    bse_stocks: int
    last_updated: Optional[datetime] = None
    data_freshness: Dict[str, Any]

class HealthResponse(BaseModel):
    status: HealthStatus
    timestamp: datetime
    components: List[SystemHealthCheck]
    data_freshness: Dict[str, Any]
    uptime_seconds: Optional[int] = None

class RefreshResponse(BaseModel):
    triggered_at: datetime
    sources_refreshed: List[str]
    records_updated: Dict[str, int]
    validation_status: Dict[str, str]
    duration_seconds: float
    success: bool
    errors: Optional[List[str]] = None

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
    timestamp: datetime
    path: Optional[str] = None
    request_id: Optional[str] = None
