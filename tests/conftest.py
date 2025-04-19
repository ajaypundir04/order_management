import pytest as pytest
from starlette.testclient import TestClient

from app.api import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
