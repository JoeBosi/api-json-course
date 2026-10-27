"""L'API di prova è spenta finché qualcuno non la accende dalla pagina /api-attiva."""
import pytest

from app import interruttore
from tests.conftest import PASSWORD


@pytest.fixture()
def spenta(client):
    interruttore.spegni()
    yield client
    interruttore.accendi()          # non lasciare l'API spenta agli altri test


def test_spenta_risponde_503_e_dice_dove_accenderla(spenta):
    r = spenta.get("/api/v1/books")
    assert r.status_code == 503
    corpo = r.json()["error"]
    assert corpo["code"] == "api_spenta"
    assert "api-attiva" in corpo["message"]
    assert r.headers["Retry-After"] == "60"


def test_lo_stato_si_legge_anche_da_spenta(spenta):
    r = spenta.get("/api/v1/interruttore")
    assert r.status_code == 200
    assert r.json()["attiva"] is False


def test_password_sbagliata_non_accende(spenta):
    r = spenta.post("/api/v1/interruttore/accendi", json={"password": "sbagliata"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "password_errata"
    assert spenta.get("/api/v1/books").status_code == 503


def test_password_giusta_accende_e_lapi_risponde(spenta):
    r = spenta.post("/api/v1/interruttore/accendi", json={"password": PASSWORD})
    assert r.status_code == 200
    assert r.json()["attiva"] is True
    assert spenta.get("/api/v1/books").status_code == 200


def test_troppi_tentativi_bloccano_per_un_po(spenta):
    interruttore._tentativi.clear()
    for _ in range(5):
        spenta.post("/api/v1/interruttore/accendi", json={"password": "sbagliata"})
    r = spenta.post("/api/v1/interruttore/accendi", json={"password": PASSWORD})
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "troppi_tentativi"
    interruttore._tentativi.clear()


def test_hash_scrypt_verifica_solo_la_password_giusta():
    h = interruttore.genera_hash("segreto-lungo")
    assert interruttore.verifica_password("segreto-lungo", h)
    assert not interruttore.verifica_password("segreto-lung", h)
    assert not interruttore.verifica_password("segreto-lungo", "formato-rotto")
    assert "segreto-lungo" not in h          # la password non compare nell'hash
