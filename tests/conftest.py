import pytest
from fastapi.testclient import TestClient

from app.api import get_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(get_app())
