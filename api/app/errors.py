"""Formato unico degli errori: {"error": {"code", "message", "details"}}.

Il corso insegna a leggere questo formato, quindi ogni errore (404, 422, 401, 429...)
passa da qui ed esce con la stessa forma.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, details=None, headers=None):
        super().__init__(status_code=status_code, detail=message, headers=headers)
        self.code = code
        self.details = details


def error_body(code: str, message: str, details=None) -> dict:
    body = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return body


CODES = {400: "bad_request", 401: "unauthorized", 403: "forbidden", 404: "not_found",
         405: "method_not_allowed", 409: "conflict", 413: "payload_too_large",
         415: "unsupported_media_type", 422: "validation_error", 429: "rate_limited"}


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError):
        return JSONResponse(status_code=exc.status_code, content=error_body(exc.code, exc.detail, exc.details), headers=exc.headers)

    @app.exception_handler(HTTPException)
    async def _http_error(_: Request, exc: HTTPException):
        code = CODES.get(exc.status_code, "error")
        return JSONResponse(status_code=exc.status_code, content=error_body(code, str(exc.detail)), headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        details = [{"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
        return JSONResponse(status_code=422, content=error_body("validation_error", "Richiesta non valida: controlla i campi in details", details))
