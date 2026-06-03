"""Phase 0 smoke test: the backend boots and the health endpoint responds."""

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_endpoint_ok() -> None:
    client = APIClient()
    response = client.get("/api/health/")
    assert response.status_code == 200
    assert response.json() == {"service": "gestion", "status": "ok"}


def test_index_endpoint_ok() -> None:
    client = APIClient()
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "gestion"
