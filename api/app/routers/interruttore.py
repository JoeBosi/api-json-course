"""Accensione dell'API di prova dalla pagina /api-attiva del sito.

Questi due endpoint rispondono anche quando l'API è spenta: sono l'unico modo per riaccenderla.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from slowapi.util import get_remote_address

from .. import interruttore

router = APIRouter(prefix="/interruttore", tags=["interruttore"])


class AccendiIn(BaseModel):
    password: Annotated[str, Field(min_length=1, max_length=200, description="Password dell'API di prova")]


@router.get("", summary="L'API di prova è accesa? Quanto manca allo spegnimento?")
def stato() -> dict:
    return interruttore.stato()


@router.post("/accendi", summary="Accende l'API di prova per chi conosce la password")
def accendi(dati: AccendiIn, request: Request) -> dict:
    return interruttore.prova_password(dati.password, get_remote_address(request))
