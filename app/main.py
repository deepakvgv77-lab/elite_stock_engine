# app/main.py
import uvicorn
from fastapi import FastAPI

from app.api import quotes, universe, gold, health, refresh
from app.tasks.scheduler import start_scheduler
from app.utils.logger import setup_logging

# Feature routers (clear aliases to avoid collisions)
from app.api.ultra_elite import router as ultra_router
from app.api.btst import router as btst_router
from app.api.intraday import router as intraday_router
from app.api.events import router as events_router
from app.api.recipes import router as recipes_router
from app.api.heatmaps import router as heatmaps_router
from app.api.checklists import router as checklists_router
from app.api.diagnostics import router as diagnostics_router
from app.portfolio.routers import router as portfolio_router
from app.mf_etf.routers import router as mf_etf_router
from app.api.events_actions import router as events_actions_router  # <-- FIXED alias
from app.api.ipo import router as ipo_router
from app.api.ai import router as ai_router
from app.api.backtest import router as backtest_router
from app.api.governance import router as governance_router
from app.api.ui import router as ui_router
from app.api.security import router as security_router
from app.api.admin import router as admin_router          # <-- NEW: Admin-only router
from app.api.lineage import router as lineage_router
from app.api.compliance import router as compliance_router

app = FastAPI(title="Elite Stock Recommendation Engine", version="0.2R")

setup_logging()

# Public/basic routers
app.include_router(quotes.router)
app.include_router(universe.router)
app.include_router(gold.router)
app.include_router(health.router)
app.include_router(refresh.router)

# Versioned routers
app.include_router(ultra_router,          prefix="/api/v2/ultra",       tags=["Ultra"])
app.include_router(btst_router,           prefix="/api/v2/btst",        tags=["BTST"])
app.include_router(intraday_router,       prefix="/api/v2/intraday",    tags=["Intraday"])
app.include_router(events_router,         prefix="/api/v2/events",      tags=["Events"])
app.include_router(recipes_router,        prefix="/api/v2/recipes",     tags=["Recipes"])
app.include_router(heatmaps_router,       prefix="/api/v2/heatmaps",    tags=["Heatmaps"])
app.include_router(checklists_router,     prefix="/api/v2/checklists",  tags=["Checklists"])
app.include_router(diagnostics_router,    prefix="/api/v2/diagnostics", tags=["Diagnostics"])

app.include_router(portfolio_router)
app.include_router(mf_etf_router)

app.include_router(events_actions_router, prefix="/api/v4/events",      tags=["Events_Actions"])
app.include_router(ipo_router,            prefix="/api/v4/ipo",         tags=["IPO"])

app.include_router(ai_router,             prefix="/api/v5/ai",          tags=["AI"])
app.include_router(backtest_router,       prefix="/api/v5/backtest",    tags=["Backtesting"])
app.include_router(governance_router,     prefix="/api/v5/governance",  tags=["Governance"])

app.include_router(ui_router,             prefix="/api/v6/ui",          tags=["UI"])
app.include_router(security_router,       prefix="/api/v6/security",    tags=["Security"])
app.include_router(admin_router,          prefix="/api/v6/admin",       tags=["Admin"])   # <-- NEW

app.include_router(lineage_router,        prefix="/api/v6/lineage",     tags=["Lineage"])
app.include_router(compliance_router,     prefix="/api/v6/compliance",  tags=["Compliance"])

@app.on_event("startup")
async def startup_event():
    start_scheduler()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
