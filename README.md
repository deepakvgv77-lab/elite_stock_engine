# Elite Stock Recommendation Engine

**Version:** 0.2R

## Overview

Elite Stock Recommendation Engine is a production-grade platform providing real-time and historical Indian stock market and gold price data with multi-phase analytics and intelligence capabilities, built with Python and FastAPI.

This engine includes:

- **Phase 1:** Data fetching (NSE, BSE, Gold), validation, storage with DuckDB, scheduling, and health monitoring
- **Phase 2:** Advanced screeners and scoring engines (Ultra-Elite Screener, BTST, Intraday Packs, Event-Driven, Recipes, Heatmaps, Checklists, Diagnostics)
- **Phase 3:** Portfolio/watchlist management and Mutual Fund & ETF analytics
- **Phase 4:** Corporate actions integration, calendar events, catalyst cards, IPO scoring and strategy
- **Phase 5:** AI-powered features, sentiment analysis, backtesting, model governance
- **Phase 6:** UI theming and offline support, security (JWT, device binding), data lineage, risk & compliance guardrails, deployment ready

## Features

- Real-time and historical data ingestion from multiple verified sources
- Circuit breaker and retry logic for robust external API handling
- Extensive validation using Great Expectations
- Modular scoring engines for multiple trading strategies
- Portfolio and MF/ETF intelligence with risk & attribution analytics
- Corporate event-driven analysis and IPO monitoring
- AI explainability, adaptive scoring, scenario narratives
- Comprehensive backtesting and Monte Carlo simulation
- Governance with model registry, drift monitoring, and compliance rules
- Modern UI with support for dark mode and offline PWA
- Security hardened with JWT auth and hardware-backed secret management
- Data provenance tracking via OpenLineage integration

## Installation

git clone https://github.com/yourusername/elite-stock-engine.git
cd elite-stock-engine
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

## Usage

- Configure your settings in `app/core/config.py` or environment variables
- Run the FastAPI app with:

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

- Access interactive API docs at `http://localhost:8000/docs`

## Project Structure

app/
├── ai/ # AI & explainability modules
├── api/ # FastAPI routers (v1 - v6)
├── backtest/ # Backtesting & simulation
├── compliance/ # Risk guardrails and compliance modes
├── core/ # Config, models, DB utils
├── data/ # NSE, BSE, Gold API fetchers
├── events_actions/ # Corporate actions, calendars & catalyst cards
├── governance/ # Model lifecycle & drift detection
├── ipo/ # IPO scoring & monitoring
├── mf_etf/ # Mutual Fund & ETF analytics
├── portfolio/ # User portfolios and watchlist
├── scoring/ # Phase 2 multi-strategy scoring engines
├── tasks/ # Scheduled refresh and health monitoring tasks
├── ui/ # UI theming and PWA assets
├── utils/ # Helpers (logging, retry, circuit breakers)
└── validation/ # Great Expectations validation suites

## Configuration

- Sensitive and environment-specific settings are managed via `.env` file or environment variables
- See `.env.example` for template variables

## Testing

- Run tests using:

pytest --cov=app tests/

## Contributing

Please fork the repo, create branches for features or bugfixes, and open pull requests. Report issues via GitHub Issues.

## License

This project is licensed under the [MIT License](LICENSE).

---

Thank you for using the Elite Stock Recommendation Engine!
