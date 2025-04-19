
import pytest
from fastapi.testclient import TestClient
from app.api import get_app  
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.entity import base

@pytest.fixture
def client() -> TestClient:
    return TestClient(get_app())

