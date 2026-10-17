# Operations

## Architecture and Access

The single-owner backend serves the compiled React workspace and a structured
JSON API. Public /health, /api/config and /api/sample expose no private reports,
credentials or provider clients. Model/data clients are lazy. Research, company
lookup, history, reopening and deletion require an owner bearer token.

The browser stores that token only in component memory; disconnect/reload clears
it. Provider credentials never leave the backend for the browser. Cross-origin
requests require an exact allowed origin. Non-loopback browser API origins must
be HTTPS; redirects are not followed by the API client.

The old /api/chat stream is retired with an authenticated 410 response. The new
/api/research contract returns validated JSON; no SDK-specific stream compatibility
is implied. User conversation history is not a shared model checkpoint. Saved
research reports are explicit owner records, not hidden cross-user conversation state.

## API

| Method/path | Access | Result |
| --- | --- | --- |
| GET /health | Public | Liveness/version, without live provider calls. |
| GET /api/config | Public | Capability booleans, never secret values. |
| GET /api/sample | Public | Three explicitly fictional reports. |
| GET /api/search?query=... | Owner | At most six bounded ticker matches. |
| POST /api/research | Owner | Validated research result, then private report save. |
| GET /api/reports | Owner | Latest 100 report references. |
| GET /api/reports/{uuid} | Owner | One validated stored report. |
| DELETE /api/reports | Owner | Explicit removal of saved reports. |

Research fields: ticker, question, sections, analysis and data_mode. Symbols use
an uppercase allowlist and maximum 20 characters. Questions are limited to 1,200
characters, section selections to six unique supported values and incoming write
bodies to 16 KB. Invalid requests return 422/413; unavailable configuration/data
returns a redacted 503, not a fabricated successful response.

## Resource Limits

One process permits twelve authenticated research/search submissions per minute.
One market-data worker avoids concurrent yfinance session mutation. Each lookup
uses a 24-request/40-second network budget, HTTPS origin allowlisting, no redirects
and at most eight seconds per network attempt. Awaiting the worker is bounded at
50 seconds; timed-out work is not replaced by an unbounded queue. Only one such
operation is admitted while the worker remains occupied.

Daily history is capped at 260 rows; tables at 20 rows and at most eight columns;
news at six entries. Provider frames/Series are normalized into JSON-safe finite
values and explicit unavailable tables. These limits do not make a hostile
provider's raw response memory use a sandbox guarantee.

Optional AI performs one SDK request with zero retries, a 30-second timeout and
2,048 completion tokens. Context is capped at 48,000 characters; raw prompts and
provider exceptions are not logged. Empty/truncated output fails before saving.
OpenAI and Thesys use separate explicitly selected origins/keys. Keys/models being
configured is not proof of model availability or output accuracy.

Use one application worker for these local admission limits. Horizontal/multi-user
deployment needs a shared limiter, tenant identity/isolation and an access design.
Do not claim the owner-token design is a public multi-user SaaS.

## Private Storage and Recovery

SQLite stores validated JSON with bound SQL parameters. Each operation closes its
connection. Insertion/pruning is one transaction; failed writes preserve existing
reports. Retention is the latest 100 reports, not an infinite archive. Set an
explicit owner-controlled database path on a persistent volume for ongoing use.
The sample public site contains no database, account snapshots or provider keys.

Back up the database while the service is stopped, or use SQLite's supported
backup API. Test restoration before relying on hosted history. Restrict parent
directory permissions/Windows ACLs; do not commit database files or backups.
JSON export is an explicit user download that may contain research questions;
handle exported files under the owner's retention/privacy policy.

Rollback means deploying the previous verified source/image and restoring a
compatible reviewed backup where needed. This reference does not provide managed
backup infrastructure, multi-host replication or an uptime SLA.

## TLS and Hosting

Never use verify=False. On enterprise Windows hosts, the curl-backed data client
may need an owner-approved PEM trust bundle through MARKET_CA_BUNDLE. Only use
trust anchors approved for that environment, and do not ship a machine-specific
trust bundle in the public repository. API/model trust may also use the platform's
SSL_CERT_FILE configuration where applicable.

Local sample use needs no secrets or network providers. Live Yahoo access needs
explicit enablement, and model inference additionally needs an approved provider
account/budget. Review Yahoo/provider terms and data redistribution rights.
The software GPLv3 license does not grant rights to vendor financial datasets.

Compose exposes loopback only, uses a non-root container and a persistent named
volume. For remote hosting, explicitly select an HTTPS reverse proxy, account,
secrets/rotation, exact CORS origins, storage, monitoring and maintenance owner.
No paid hosting or automatic collection is activated by the repository.

## Release Reproduction

Use frozen uv and npm locks; run Python tests/lint/audit and frontend tests/build.
Generate the sample JSON from MarketInsight/sample.py, copy production dependency
notices, prepare the packaged site, then build/check wheel and source artifacts.
The installed-wheel check proves the UI and API load outside the source checkout.
Container and desktop/mobile checks are separate required CI gates.

The source archive includes the preferred source, scripts, tests and license
notices. Public demo assets retain all bundled production dependency licenses.
Do not report synthetic research, mocked AI or a credential check as a successful
live model-backed financial evaluation.