import hmac
import os
import sqlite3
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config.config import ResearchRequest, ResearchResult
from MarketInsight.research import ReportStore, ResearchService, ai_configuration
from MarketInsight.sample import sample_reports

ROOT = Path(__file__).resolve().parent


class BoundedBody:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > 16_384:
                return await JSONResponse({"detail": "Request body exceeds 16 KB"}, status_code=413)(
                    scope, receive, send
                )
            if not message.get("more_body", False):
                break
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        return await self.app(scope, bounded_receive, send)


def create_app(*, service=None, store=None):
    research_service = service or ResearchService()
    report_store = store or ReportStore(
        Path(os.environ.get("MARKET_DATABASE_PATH", str(Path.cwd() / "data/reports.sqlite")))
    )
    requests_window = deque()

    @asynccontextmanager
    async def lifespan(application):
        yield
        research_service.close()

    application = FastAPI(
        title="Market Insight Workbench", version="0.2.0", lifespan=lifespan, docs_url=None, redoc_url=None
    )
    application.state.research = research_service
    application.add_middleware(BoundedBody)
    origins = [
        origin.strip()
        for origin in os.environ.get(
            "MARKET_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
        ).split(",")
        if origin.strip()
    ]
    if "*" in origins:
        raise ValueError("Wildcard CORS is not supported for the private API")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @application.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/") else "no-cache"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'"
        )
        return response

    async def owner(authorization: str | None = Header(default=None)):
        token = os.environ.get("MARKET_API_TOKEN", "")
        if not 32 <= len(token) <= 256:
            raise HTTPException(503, "Private API is not configured")
        if (
            not authorization
            or len(authorization) > 512
            or not hmac.compare_digest(authorization.encode(), ("Bearer " + token).encode())
        ):
            raise HTTPException(401, "Authentication required")

    async def budget():
        now = time.monotonic()
        while requests_window and requests_window[0] <= now - 60:
            requests_window.popleft()
        if len(requests_window) >= 12:
            raise HTTPException(429, "Research request limit reached; retry in one minute")
        requests_window.append(now)

    @application.exception_handler(sqlite3.Error)
    async def database_error(request, error):
        return JSONResponse({"detail": "Private report storage is unavailable"}, status_code=503)

    @application.get("/health")
    async def health():
        return {"status": "ok", "version": "0.2.0"}

    @application.get("/api/config")
    async def configuration():
        try:
            ai_configuration()
            ai_ready = True
        except ValueError:
            ai_ready = False
        return {
            "private_api": 32 <= len(os.environ.get("MARKET_API_TOKEN", "")) <= 256,
            "live_data": os.environ.get("MARKET_LIVE_DATA") == "1",
            "ai": ai_ready,
            "version": "0.2.0",
        }

    @application.get("/api/sample", response_model=list[ResearchResult])
    async def sample():
        return sample_reports()

    @application.get("/api/search", dependencies=[Depends(owner), Depends(budget)])
    async def search(query: str = Query(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9 .&^=_-]+$")):
        try:
            return await research_service.search(query)
        except Exception:
            raise HTTPException(
                503, "Symbol lookup unavailable; verify data access and provider availability"
            ) from None

    @application.post(
        "/api/research", response_model=ResearchResult, dependencies=[Depends(owner), Depends(budget)]
    )
    async def research(payload: ResearchRequest):
        try:
            result = await research_service.research(payload)
        except ValueError:
            raise HTTPException(
                503, "Research unavailable; verify source availability, live access and provider settings"
            ) from None
        except Exception:
            raise HTTPException(503, "Research failed; provider details were not disclosed") from None
        report_store.save(result)
        return result

    @application.get("/api/reports", dependencies=[Depends(owner)])
    async def reports():
        return report_store.list()

    @application.get(
        "/api/reports/{identifier}", response_model=ResearchResult, dependencies=[Depends(owner)]
    )
    async def report(identifier: UUID):
        result = report_store.get(str(identifier))
        if result is None:
            raise HTTPException(404, "Report not found")
        return result

    @application.delete("/api/reports", dependencies=[Depends(owner)])
    async def clear_reports():
        report_store.clear()
        return {"deleted": True}

    @application.post("/api/chat", dependencies=[Depends(owner)])
    async def legacy_chat():
        raise HTTPException(410, "The legacy stream was replaced by the structured /api/research API")

    distribution = ROOT / "frontend/dist"
    if not distribution.is_dir():
        distribution = ROOT / "MarketInsight/web"
    if distribution.is_dir():
        application.mount("/", StaticFiles(directory=distribution, html=True), name="workspace")
    return application


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
