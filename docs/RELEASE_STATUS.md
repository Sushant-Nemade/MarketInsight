# Release Evidence: 0.2.0

Reviewed 2026-10-17. Attributed GPLv3 reference derived from
KalyanM45/MarketInsight at 7fae6d81d09810273fa30f7f50003f42dc51646a.
Source history, license and modification notices are preserved.

## Implemented and Verified Locally

- Complete synthetic research workspace with profiles, charts, financials,
  ownership, events, coverage, news, provenance, JSON export and private history.
- Typed bounded API, owner authentication, request-body limits, quotas, exact
  CORS, redacted failures and transactional bounded report persistence.
- Maintained renderer dependencies: inherited C1/KaTeX/Prism chains removed.
  The frontend and Python dependency audits report no known vulnerabilities in
  the tested frozen sets; this is not a permanent security guarantee.
- Twenty desktop/mobile Playwright cases cover actual backend
  save/reopen/clear, chart pixels, all sections, lookup, errors, export and safe
  text rendering, retry, keyboard dialogs and 320px framing. Thirty-seven Python
  API/contract/provider/storage/SDK regressions passed locally.
- Official OpenAI SDK requests are tested with MockTransport for fixed origins,
  evidence grounding, completion limits, redaction and truncated-output rejection.
  These are not paid live inference tests.
- A real Yahoo Finance AAPL quote and 251 daily history rows were fetched on
  2026-10-17. Provider quote timestamp was 2026-10-16T20:00:01+00:00. An approved
  platform trust bundle resolved an enterprise Windows certificate chain; TLS
  verification stayed enabled. No raw live dataset is committed as demo data.
- Main JavaScript bundle is roughly 485 KB, replacing the inherited ~2.9 MB bundle.
  Fonts are bundled locally; required production dependency notices are retained.

## Required Remote Gates

Linux/Windows frozen builds, installed-wheel/source checks and the non-root
container check must pass in the repository's Verify Market Insight workflow.
Static reference deployment is gated on its success. Final remote run URLs are
recorded after those gates complete; local success alone is not deployment proof.

## Explicit Boundaries

No paid OpenAI/Thesys inference was invoked or certified. Individual live
financial endpoints may be unavailable, delayed or restricted; their missing
states remain explicit. Source/model output requires human interpretation and
review. No prediction accuracy, personalized advice, trading execution, multi-user
tenant isolation, managed private hosting or operational SLA is claimed.

The public reference uses fictional companies and authored synthetic figures.
Private live research requires the operator's own access/credentials and review
of data/provider terms. Model availability is independent of the installed app.