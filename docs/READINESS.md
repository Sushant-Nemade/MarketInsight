# Historical Readiness Stage: 2026-10-14

This historical checkpoint is superseded by the complete 0.2.0 reference
implementation reviewed 2026-10-17. See [current release evidence](RELEASE_STATUS.md)
and [current setup](../README.md). The blockers below describe the earlier stage,
not the current implementation.

Reviewed 2026-10-14. This is in progress, not a fourth released reference.
Adapted locally from KalyanM45/MarketInsight, revision
7fae6d81d09810273fa30f7f50003f42dc51646a. The original GNU GPLv3 license and
Git history remain intact. Startup/authentication/provider boundaries were
modified by Sushant Nemade on 2026-10-14; no hosted or paid service was activated.

## Verified This Stage

Six Python readiness tests pass with provider keys removed and outbound socket
creation blocked. Startup and /health do not create log files or initialize model
or tracing clients. Private chat returns 503 when unconfigured and 401 without
the owner token. Missing selected provider configuration fails closed.
Prompt/identifier bounds and untrusted-origin rejection are tested.

Provider origins are fixed and explicitly selected. MARKET_PROVIDER=openai uses
OPENAI_API_KEY only at api.openai.com; MARKET_PROVIDER=thesys uses THESYS_API_KEY
only at api.thesys.dev. MARKET_MODEL must also be selected. An OpenAI key is
never silently reused for the inherited third-party gateway.

The frontend compiles with configurable VITE_MARKET_API_URL and a same-origin
/api/chat default; the upstream author's hosted API is no longer the default.
This is compilation evidence, not C1 SDK end-to-end protocol validation.

## Local Verification

Create a Python 3.13 environment and install requirements-readiness.txt. This
small environment tests startup, not the entire inherited AI/data stack.

```text
python -m pytest tests/test_readiness.py -q
python -m uvicorn main:app --host 127.0.0.1 --port 8790
```

/health reports stage=readiness and live_provider_verified=false. No model key
is needed. Do not expose this stage publicly. Real generation needs the full
AI/data dependencies, an approved provider account and MARKET_API_TOKEN of at
least 32 characters. Never commit or publicly share the owner token.
Settings use process variables; private .env files are not automatically loaded.

## Remaining Gates

1. Resolve the C1 SDK renderer dependency chains: npm audit reports ten findings
   (six low, four moderate), including KaTeX and Prism. Compatible npm audit fix
   found no available fixes. Select a maintained renderer/SDK with compatibility
   tests; do not use --force to conceal this release blocker.
2. Validate stream rendering and owner authentication in the actual UI. The
   readiness endpoint uses plain text, not unframed content mislabeled SSE.
3. Audit and bound financial-data tools; retain provenance and observation dates,
   and distinguish unavailable data from factual results. No trading integration,
   personalized investment advice or performance guarantee is included.
4. Regenerate/audit the full backend lockfile and trace tracing/legacy dependency
   consumers. The upstream uv.lock is not the tested readiness environment.
5. Verify the chosen provider/data flow with an approved budget and test account.
   No such keys were available during this stage.
6. Complete browser, packaging and CI gates and review bundle performance. The
   inherited build has a roughly 2.9 MB main JavaScript chunk.

Conversation persistence is deliberately absent: do not reuse caller-controlled
shared checkpoints without user isolation. No Langfuse tracing is initialized
by the readiness application. Local stream/model limits do not certify financial
tool timeouts or public-service resource isolation. Complete these gates before
calling this candidate a released reference or live production application.