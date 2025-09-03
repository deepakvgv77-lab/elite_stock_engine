from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
from loguru import logger

from app.core.models import RefreshResponse
from app.core.database import db_manager
from app.services.nse_fetcher import NSEFetcher
from app.services.bse_fetcher import BSEFetcher
from app.services.gold_fetcher import GoldFetcher
from app.core.validator import DataValidator

router = APIRouter(prefix="/refresh", tags=["Data Refresh"])


class RefreshService:
    """Manual refresh service for live data sources"""
    
    def __init__(self):
        self.nse_fetcher = NSEFetcher()
        self.bse_fetcher = BSEFetcher()
        self.gold_fetcher = GoldFetcher()
        self.validator = DataValidator()
        
    async def refresh_nse_data(self) -> Dict[str, int]:
        """Refresh NSE universe and quotes"""
        try:
            logger.info("Starting NSE data refresh")
            
            # Fetch NSE universe
            stocks = await self.nse_fetcher.fetch_stock_universe()
            stocks_updated = 0
            
            for stock in stocks:
                # Insert/update stock data
                query = """
                INSERT INTO stocks (symbol, name, exchange, sector, industry, isin, market_cap, segment, listing_date, face_value, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT (symbol) DO UPDATE SET
                    name = excluded.name,
                    sector = excluded.sector,
                    industry = excluded.industry,
                    market_cap = excluded.market_cap,
                    updated_at = CURRENT_TIMESTAMP
                """
                db_manager.execute_insert(query, {
                    'symbol': stock['symbol'],
                    'name': stock['name'],
                    'exchange': 'NSE',
                    'sector': stock.get('sector'),
                    'industry': stock.get('industry'),
                    'isin': stock.get('isin'),
                    'market_cap': stock.get('market_cap'),
                    'segment': stock.get('segment'),
                    'listing_date': stock.get('listing_date'),
                    'face_value': stock.get('face_value')
                })
                stocks_updated += 1
            
            # Fetch fresh quotes for active symbols
            quotes = await self.nse_fetcher.fetch_live_quotes()
            quotes_updated = 0
            
            for quote in quotes:
                quote_query = """
                INSERT INTO quotes (symbol, exchange, price, change_amount, change_percent, volume, value, 
                                  high, low, open, close, bid, ask, delivery_qty, delivery_percent, 
                                  timestamp, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'NSE_API')
                """
                db_manager.execute_insert(quote_query, quote)
                quotes_updated += 1
            
            logger.info(f"NSE refresh completed: {stocks_updated} stocks, {quotes_updated} quotes")
            return {"stocks": stocks_updated, "quotes": quotes_updated}
            
        except Exception as e:
            logger.error(f"NSE refresh failed: {e}")
            raise
    
    async def refresh_bse_data(self) -> Dict[str, int]:
        """Refresh BSE universe and quotes"""
        try:
            logger.info("Starting BSE data refresh")
            
            stocks = await self.bse_fetcher.fetch_stock_universe()
            stocks_updated = 0
            
            for stock in stocks:
                query = """
                INSERT INTO stocks (symbol, name, exchange, sector, industry, isin, market_cap, segment, listing_date, face_value, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT (symbol) DO UPDATE SET
                    name = excluded.name,
                    sector = excluded.sector,
                    industry = excluded.industry,
                    market_cap = excluded.market_cap,
                    updated_at = CURRENT_TIMESTAMP
                """
                db_manager.execute_insert(query, {
                    'symbol': stock['symbol'],
                    'name': stock['name'],
                    'exchange': 'BSE',
                    'sector': stock.get('sector'),
                    'industry': stock.get('industry'),
                    'isin': stock.get('isin'),
                    'market_cap': stock.get('market_cap'),
                    'segment': stock.get('segment'),
                    'listing_date': stock.get('listing_date'),
                    'face_value': stock.get('face_value')
                })
                stocks_updated += 1
            
            logger.info(f"BSE refresh completed: {stocks_updated} stocks")
            return {"stocks": stocks_updated, "quotes": 0}
            
        except Exception as e:
            logger.error(f"BSE refresh failed: {e}")
            raise
    
    async def refresh_gold_data(self) -> Dict[str, int]:
        """Refresh Coimbatore 22K gold rates"""
        try:
            logger.info("Starting gold data refresh")
            
            gold_rates = await self.gold_fetcher.fetch_gold_rates()
            rates_updated = 0
            
            for rate in gold_rates:
                query = """
                INSERT INTO gold_rates (date, city, purity, rate_per_gram, rate_per_10g, 
                                      change_amount, change_percent, previous_rate, data_source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT (date, city, purity) DO UPDATE SET
                    rate_per_gram = excluded.rate_per_gram,
                    rate_per_10g = excluded.rate_per_10g,
                    change_amount = excluded.change_amount,
                    change_percent = excluded.change_percent,
                    previous_rate = excluded.previous_rate,
                    data_source = excluded.data_source,
                    created_at = CURRENT_TIMESTAMP
                """
                db_manager.execute_insert(query, rate)
                rates_updated += 1
            
            logger.info(f"Gold refresh completed: {rates_updated} rates")
            return {"gold_rates": rates_updated}
            
        except Exception as e:
            logger.error(f"Gold refresh failed: {e}")
            raise
    
    async def validate_data_quality(self) -> Dict[str, str]:
        """Run Great Expectations validation gates"""
        try:
            logger.info("Running data quality validation")
            
            validation_results = {}
            
            # Validate stocks data
            stocks_validation = await self.validator.validate_stocks_data()
            validation_results["stocks"] = "PASSED" if stocks_validation else "FAILED"
            
            # Validate quotes data
            quotes_validation = await self.validator.validate_quotes_data()
            validation_results["quotes"] = "PASSED" if quotes_validation else "FAILED"
            
            # Validate gold data
            gold_validation = await self.validator.validate_gold_data()
            validation_results["gold_rates"] = "PASSED" if gold_validation else "FAILED"
            
            logger.info(f"Validation completed: {validation_results}")
            return validation_results
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {"error": str(e)}


refresh_service = RefreshService()


@router.post("/", response_model=RefreshResponse)
async def manual_refresh(
    sources: Optional[List[str]] = None
) -> RefreshResponse:
    """
    Manual refresh endpoint for live data sources
    
    Args:
        sources: List of sources to refresh ["nse", "bse", "gold"]. If None, refreshes all.
    
    Returns:
        RefreshResponse with status and metrics
    """
    start_time = datetime.now()
    
    try:
        # Default to all sources if none specified
        if sources is None:
            sources = ["nse", "bse", "gold"]
        
        # Validate source names
        valid_sources = {"nse", "bse", "gold"}
        invalid_sources = set(sources) - valid_sources
        if invalid_sources:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid sources: {list(invalid_sources)}. Valid sources: {list(valid_sources)}"
            )
        
        logger.info(f"Manual refresh triggered for sources: {sources}")
        
        sources_refreshed = []
        records_updated = {}
        errors = []
        
        # Refresh NSE data
        if "nse" in sources:
            try:
                nse_result = await refresh_service.refresh_nse_data()
                sources_refreshed.append("NSE")
                records_updated.update(nse_result)
            except Exception as e:
                errors.append(f"NSE refresh failed: {str(e)}")
        
        # Refresh BSE data
        if "bse" in sources:
            try:
                bse_result = await refresh_service.refresh_bse_data()
                sources_refreshed.append("BSE")
                records_updated.update(bse_result)
            except Exception as e:
                errors.append(f"BSE refresh failed: {str(e)}")
        
        # Refresh Gold data
        if "gold" in sources:
            try:
                gold_result = await refresh_service.refresh_gold_data()
                sources_refreshed.append("GOLD")
                records_updated.update(gold_result)
            except Exception as e:
                errors.append(f"Gold refresh failed: {str(e)}")
        
        # Run data quality validation
        validation_status = await refresh_service.validate_data_quality()
        
        # Calculate duration
        end_time = datetime.now()
        duration_seconds = (end_time - start_time).total_seconds()
        
        # Determine success status
        success = len(errors) == 0 and all(
            status == "PASSED" for status in validation_status.values() 
            if status != "error"
        )
        
        logger.info(f"Manual refresh completed in {duration_seconds:.2f}s. Success: {success}")
        
        return RefreshResponse(
            triggered_at=start_time,
            sources_refreshed=sources_refreshed,
            records_updated=records_updated,
            validation_status=validation_status,
            duration_seconds=duration_seconds,
            success=success,
            errors=errors if errors else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual refresh failed: {e}")
        duration_seconds = (datetime.now() - start_time).total_seconds()
        
        return RefreshResponse(
            triggered_at=start_time,
            sources_refreshed=[],
            records_updated={},
            validation_status={"error": str(e)},
            duration_seconds=duration_seconds,
            success=False,
            errors=[str(e)]
        )


@router.get("/status")
async def get_refresh_status():
    """Get current refresh status and data freshness"""
    try:
        # Get latest timestamps from each table
        latest_quotes = db_manager.execute_query(
            "SELECT MAX(timestamp) as latest_quote FROM quotes"
        )
        
        latest_stocks = db_manager.execute_query(
            "SELECT MAX(updated_at) as latest_stock FROM stocks"
        )
        
        latest_gold = db_manager.execute_query(
            "SELECT MAX(created_at) as latest_gold FROM gold_rates"
        )
        
        return {
            "status": "ready",
            "data_freshness": {
                "quotes": latest_quotes[0]["latest_quote"] if latest_quotes and latest_quotes[0]["latest_quote"] else None,
                "stocks": latest_stocks[0]["latest_stock"] if latest_stocks and latest_stocks[0]["latest_stock"] else None,
                "gold_rates": latest_gold[0]["latest_gold"] if latest_gold and latest_gold[0]["latest_gold"] else None
            },
            "timestamp": datetime.now()
        }
    
    except Exception as e:
        logger.error(f"Failed to get refresh status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get refresh status")


@router.post("/watchlist")
async def refresh_watchlist_data(symbols: List[str]):
    """
    Refresh specific watchlist symbols only
    
    Args:
        symbols: List of stock symbols to refresh
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Refreshing watchlist symbols: {symbols}")
        
        quotes_updated = 0
        errors = []
        
        for symbol in symbols:
            try:
                # Fetch fresh quote for this symbol
                quote = await refresh_service.nse_fetcher.fetch_symbol_quote(symbol)
                if quote:
                    quote_query = """
                    INSERT INTO quotes (symbol, exchange, price, change_amount, change_percent, volume, value, 
                                      high, low, open, close, timestamp, data_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'NSE_API')
                    """
                    db_manager.execute_insert(quote_query, quote)
                    quotes_updated += 1
            except Exception as e:
                errors.append(f"Failed to refresh {symbol}: {str(e)}")
        
        duration_seconds = (datetime.now() - start_time).total_seconds()
        
        return {
            "triggered_at": start_time,
            "symbols_requested": len(symbols),
            "quotes_updated": quotes_updated,
            "duration_seconds": duration_seconds,
            "success": len(errors) == 0,
            "errors": errors if errors else None
        }
    
    except Exception as e:
        logger.error(f"Watchlist refresh failed: {e}")
        raise HTTPException(status_code=500, detail=f"Watchlist refresh failed: {str(e)}")
