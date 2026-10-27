import os
import pytest

os.environ["CORSO_RATE_LIMIT"] = "1000/minute"
# password di prova dell'interruttore: l'hash si calcola qui, la password resta solo nei test
PASSWORD = "prova-interruttore-123"


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    os.environ["CORSO_DATA_DIR"] = str(tmp_path_factory.mktemp("data"))
    from importlib import reload
    from app import config
    reload(config)
    from app import interruttore
    reload(interruttore)
    os.environ["CORSO_API_PASSWORD_HASH"] = interruttore.genera_hash(PASSWORD)
    reload(config)
    from app import main
    reload(main)
    interruttore.accendi()          # gli altri test lavorano con l'API accesa
    from fastapi.testclient import TestClient
    with TestClient(main.app) as c:
        yield c


@pytest.fixture()
def sandbox(client):
    r = client.post("/api/v1/sandbox")
    assert r.status_code == 201
    tok = r.json()["token"]
    yield {"Authorization": f"Bearer {tok}"}
    client.delete("/api/v1/sandbox", headers={"Authorization": f"Bearer {tok}"})
