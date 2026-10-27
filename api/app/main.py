"""Server di prova del corso: API sotto /api/v1, documentazione su /api/docs,
sito statico (site/dist) su tutto il resto."""
from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from . import config, db, errors, interruttore, sandbox
from .routers import avanzati, books, meta, relazioni
from .routers import interruttore as interruttore_router
from .routers import sandbox as sandbox_router

log = logging.getLogger("corso")

DESCRIZIONE = """
Server di prova del **Corso JSON & API**. Dati inventati (libreria "Aurora").

* Senza token leggi il dataset pubblico (sola lettura).
* `POST /api/v1/sandbox` ti dà un token: con `Authorization: Bearer <token>` lavori su una
  **copia privata** del database e puoi creare, modificare e cancellare.
* Le sandbox scadono dopo alcune ore di inattività. Limite: %s per IP.

L'API di prova **è spenta** quando nessuno la usa: si accende da %s e si rispegne dopo
%d minuti di inattività.
""" % (config.RATE_LIMIT, config.PAGINA_ATTIVA, config.API_IDLE_MIN)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.assicura_seed()
    tolte = sandbox.pulisci_scadute()
    log.info("seed pronto in %s, sandbox scadute rimosse: %d", config.SEED_DB, tolte)
    yield


limiter = Limiter(key_func=get_remote_address, default_limits=[config.RATE_LIMIT], headers_enabled=True)

# docs_url/redoc_url disattivati: la pagina /api/docs la serviamo noi più sotto, con i file di
# Swagger UI presi dal sito e non da una CDN esterna (nessuna richiesta a terzi, vedi /privacy/).
app = FastAPI(title="Corso JSON & API — server di prova", version="1.0.0", description=DESCRIZIONE, lifespan=lifespan,
              docs_url=None, redoc_url=None, openapi_url="/api/openapi.json")
app.state.limiter = limiter
errors.install(app)


@app.exception_handler(RateLimitExceeded)
async def _troppe(request: Request, exc: RateLimitExceeded):
    resp = JSONResponse(status_code=429, content=errors.error_body("rate_limited", f"Troppe richieste: limite {exc.detail}. Riprova tra poco."))
    resp.headers["Retry-After"] = "10"
    return resp


# gzip anche sulle risposte in streaming (export): Caddy non le comprime da solo
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
                   expose_headers=["ETag", "Location", "Retry-After", "X-Request-Id", "X-RateLimit-Limit", "X-RateLimit-Remaining"])


SEMPRE_APERTI = ("/api/v1/interruttore", "/api/v1/interruttore/accendi")


@app.middleware("http")
async def request_id_e_limite(request: Request, call_next):
    """Un id per richiesta (utile nel corso per parlare di tracciamento) + rate limit per IP
    + interruttore: con l'API spenta risponde 503 e spiega dove accenderla."""
    if request.url.path.startswith("/api/"):
        if request.url.path.rstrip("/") not in SEMPRE_APERTI:
            if not interruttore.accesa():
                return JSONResponse(status_code=503, content=errors.error_body(
                    "api_spenta",
                    f"API di prova spenta: attivala da {config.PUBLIC_URL}{config.PAGINA_ATTIVA}",
                    {"attiva_da": config.PUBLIC_URL + config.PAGINA_ATTIVA,
                     "stato": "/api/v1/interruttore"}), headers={"Retry-After": "60"})
            interruttore.tocca()
        try:
            limiter._check_request_limit(request, None, False)  # noqa: SLF001 — API interna di slowapi, ma stabile
        except RateLimitExceeded as exc:
            return await _troppe(request, exc)
    response = await call_next(request)
    response.headers["X-Request-Id"] = uuid.uuid4().hex[:12]
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


for r in (interruttore_router.router, meta.router, sandbox_router.router, books.router, relazioni.router, avanzati.router):
    app.include_router(r, prefix="/api/v1")


@app.get("/api/docs", include_in_schema=False)
def swagger():
    """Swagger UI con i file serviti da questo stesso sito (site/public/swagger/)."""
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="Corso JSON & API — server di prova",
        swagger_js_url="/swagger/swagger-ui-bundle.js",
        swagger_css_url="/swagger/swagger-ui.css",
        swagger_favicon_url="/swagger/favicon-32x32.png",
        oauth2_redirect_url=None,
    )


@app.get("/api", include_in_schema=False)
def api_root():
    return RedirectResponse("/api/docs")


@app.api_route("/api/{rest:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
def api_404(rest: str):
    return JSONResponse(status_code=404, content=errors.error_body("not_found", f"Nessun endpoint /api/{rest}. Elenco: /api/v1/ e /api/docs"))


if (config.SITE_DIST / "index.html").exists():
    app.frontend("/", directory=str(config.SITE_DIST))
else:
    log.warning("site/dist assente (%s): servo solo /api", config.SITE_DIST)
