import os
import pytest
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from intentledger.main import app

def test_health_reports_database_engine():
 client=TestClient(app);response=client.get("/api/v1/health");assert response.status_code==200;assert response.json()["readiness"]["database_engine"]=="sqlite-offline"
def test_auth_protected(monkeypatch):
 monkeypatch.setenv("LOCAL_API_TOKEN","secret");client=TestClient(app);assert client.get("/api/v1/repositories").status_code==401;assert client.get("/api/v1/repositories",headers={"authorization":"Bearer secret"}).status_code==200
