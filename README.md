# Market Insight

A financial research workbench with source-dated evidence, comparative tables,
private report history, JSON export and optional grounded AI synthesis.

**Status: tested reference implementation.** The complete synthetic workflow is
usable without accounts or API keys. Live Yahoo Finance quote/history access was
verified locally with TLS enabled. Paid model inference and managed production
hosting are not certified or silently activated.

## Provenance and License

Adapted from [Hema Kalyan Murapaka's MarketInsight](https://github.com/KalyanM45/MarketInsight),
revision `7fae6d81d09810273fa30f7f50003f42dc51646a`, discovered through
[AI Project Gallery](https://github.com/KalyanM45/AI-Project-Gallery).
Original Git history and [GNU GPLv3](LICENSE) are preserved. Modified by
Sushant Nemade on 2026-10-17; see [modification/source notice](NOTICE.md).
This is an attributed derivative, not a claim that the upstream work is original.

The inherited C1 renderer, unbounded agent execution, shared conversation
checkpoint and automatic tracing were replaced. Research now uses explicit
bounded sections and optional evidence-grounded synthesis. It is not an
autonomous trading agent or an assertion of exact upstream implementation parity.

## Working Application

- Search/select a company or ticker; inspect quoted prices and daily history.
- Review profile/ratios, balance sheet, income/cash flow, ownership, insider
  transactions, dividends/splits, analyst coverage and news where available.
- Keep missing, delayed and partially unavailable results visible with provenance.
- Create evidence inventories or explicitly configured AI summaries.
- Save, reopen and delete reports in a private SQLite workspace; export JSON
  with the research question, source information and limitations.
- Use an authored fictional dataset independently of live providers. Sample
  companies and values are visibly labeled and never substituted for live failures.

The React/TypeScript workspace uses Chart.js, Lucide, Zod and locally bundled
IBM Plex fonts. Financial retrieval uses yfinance with a bounded curl session;
optional synthesis uses the official OpenAI-compatible SDK. No third-party
renderer executes model-provided HTML.

## Quick Start

Requires Python 3.13, uv, and Node.js 24. From the repository root:

```text
uv sync --frozen --group dev
uv run --frozen python -m scripts.build_demo
cd frontend
npm ci --ignore-scripts
npm run build -- --logLevel error
node scripts/licenses.mjs
cd ..
uv run --frozen python -m uvicorn main:app --host 127.0.0.1 --port 8790
```

Open http://127.0.0.1:8790 . The built frontend and API are served by one process.
The default sample workflow makes no market-data or model requests. No token is
needed to explore synthetic reports and export them in the browser.

For frontend development, run `npm run dev` in frontend with the backend on port
8000; Vite proxies /api to that backend. Production/reference checks use the
compiled application, not a separate unverified mock UI.

## Private Live Research

Configure process variables through your terminal or secret manager; names are
listed in [.env.example](.env.example). The Python app does not automatically load
an .env file. Never paste keys in chat, browser source, URLs or a Git commit.

| Setting | Purpose |
| --- | --- |
| MARKET_API_TOKEN | Owner access token, 32-256 characters. Required for research/history APIs. |
| MARKET_LIVE_DATA=1 | Explicitly permit Yahoo Finance lookups; defaults off. |
| MARKET_DATABASE_PATH | Private SQLite location; defaults to data/reports.sqlite in the working directory. |
| MARKET_ALLOWED_ORIGINS | Exact comma-separated dashboard origins if cross-origin access is needed; never wildcard. |
| MARKET_PROVIDER | Optional openai or thesys selection; no implicit provider. |
| MARKET_MODEL | Explicit model name for the selected account. |
| OPENAI_API_KEY | Used only with the direct api.openai.com origin. |
| THESYS_API_KEY | Used only with the explicit api.thesys.dev origin. |
| MARKET_CA_BUNDLE | Optional trusted PEM bundle for environments with enterprise certificates; TLS is never disabled. |

Restart the API after configuring it. In the workspace's API connection dialog,
enter its HTTPS origin (or loopback HTTP origin) and the owner access token, not
a provider key. Tokens stay in memory and are cleared by disconnect/reload.
Search real symbols with live access enabled; AI synthesis is separately optional.

Current authentication is single-owner, not multi-user OAuth. Do not expose the
owner token to public visitors. Provider terms, data rights, quotas and model
costs apply. Yahoo Finance data availability is not an uptime guarantee.

## Deployment and Distribution

The public Pages reference contains fictional data only. It does not host a
Python API or a database. A configured private HTTPS API can be used separately,
subject to its access policy and permitted origins. Same-origin serving is the
default local/container delivery path.

For containers, create a private .env using the setting names, then:

```text
docker compose up --build
```

The container runs as a non-root user, binds the Compose port to loopback and
persists reports in a named volume. Add an approved HTTPS reverse proxy, backup
policy and secrets configuration before any remote deployment.

An installable wheel includes the compiled sample workspace and backend. Build it
after the frontend and license-copy steps:

```text
uv run --frozen python -m scripts.prepare_site
uv run --frozen --group dev python -m build
uv run --frozen --group dev python -m scripts.verify_release
```

No PyPI publication or paid hosting is configured. Corresponding source includes
frontend source/lock, fixtures, tests, build scripts and license notices.

## Verification

```text
uv run --frozen --group dev pytest -q
uv run --frozen --group dev ruff check .
uv run --frozen --group dev ruff format --check .
uv run --frozen --group dev pip-audit --local --skip-editable --progress-spinner off
cd frontend
npm audit
npm run lint
npm run format:check
npx playwright install chromium
npm test
```

CI verifies Linux and Windows, installs the actual wheel, builds/tests the
non-root container and deploys the static reference only after verification.
Tests use fixtures and SDK HTTP transports, never a paid account or private data.
See [release evidence](docs/RELEASE_STATUS.md) and [operations](docs/OPERATIONS.md).

## Research Boundaries

Financial values may be delayed, incomplete or revised. Observation time is not
necessarily trade time. Missing data stays missing; a historical close is labeled
as such. Statement currency is not inferred from quote currency. Analyst tables
are provider data, not an endorsement. AI summaries require human review.

This software provides educational research, not personalized investment advice,
forecasting guarantees, order execution, an operational SLA or production
certification. Preserve data/provider licensing and review permitted use before
redistributing real market observations.# Market Insight

**Local status: in progress, not released.** Startup, provider and security
boundaries are being adapted under the original GPLv3 license. Read
[readiness evidence and remaining gates](docs/READINESS.md) before following
the historical upstream instructions below. Live integrations are unverified,
and inherited frontend dependency findings block public release.

An AI-powered stock market analysis platform that provides comprehensive financial data and intelligent insights through a conversational interface.

## Overview

Market Insight leverages advanced AI agents to deliver real-time stock market information, financial analysis, and investment insights. The platform combines the power of LangChain and OpenAI's language models with Yahoo Finance data to create an intelligent assistant for stock market research.

## Technology Stack

**Backend:**
- FastAPI for high-performance API endpoints
- LangChain & LangGraph for AI agent orchestration
- OpenAI GPT models for intelligent responses
- YFinance for financial data retrieval
- Langfuse for observability and tracing

**Frontend:**
- Modern React-based interface
- Real-time streaming responses
- Responsive design for all devices

## Getting Started

### Prerequisites
- Python 3.x
- Node.js (for frontend)
- OpenAI API key

### Installation

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env` file
4. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```
5. Run the backend server:
   ```bash
   python main.py
   ```
6. Run the frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```
7. Access the API at `http://localhost:8000` and frontend at `http://localhost:5173`

## Project Structure

```
MarketInsight/
├── components/     # AI agent configuration
├── utils/          # Tools and utilities
├── config/         # Configuration files
├── frontend/       # React frontend application
└── main.py         # FastAPI server entry point
```

## API Capabilities

The platform provides 16 specialized tools for comprehensive stock analysis:
- Stock price tracking
- Historical data analysis
- Financial statements (Balance Sheet, Income Statement, Cash Flow)
- Company information and ratios
- Dividend and split history
- Ownership and holder data
- Insider transactions
- Analyst recommendations
- Company ticker lookup