import pytest
from fastapi.testclient import TestClient
from agents.api import app
from agents.base import AuditTrail

client = TestClient(app)


def test_audit_signatures_verify_and_detect_tampering():
    audit = AuditTrail(secret_key="unit-test-only")
    entry = audit.log("tester", "test", "CHECK", {"value": 1})
    assert audit.verify_integrity()
    returned = audit.get_trail()
    returned[0]["current_hash"] = "0" * 64
    assert audit.verify_integrity()  # Accessors cannot mutate the ledger.
    audit.logs[0]["payload_hash"] = "0" * 64
    assert not audit.verify_integrity()


def test_calculator_api_and_frontend_files():
    assert client.get("/").status_code == 200
    assert "Standardized mean difference" in client.get("/").text
    assert client.get("/app.js").status_code == 200
    assert client.get("/audit-console").status_code == 200
    r = client.post("/api/effect-size", json={
        "mean1": 10, "mean2": 8, "std1": 2, "std2": 2, "n1": 30, "n2": 30
    })
    assert r.status_code == 200
    assert r.json()["cohens_d"] == 1.0


def test_api_rejects_invalid_statistical_inputs():
    response = client.post("/api/effect-size", json={
        "mean1": 10, "mean2": 8, "std1": 0, "std2": 0, "n1": 30, "n2": 30
    })
    assert response.status_code == 422


def test_audit_api_rejects_identifiers_in_nested_payloads():
    response = client.post("/api/audit", json={
        "task_id": "T1", "target_identifier": "X1",
        "primary_metric": 1.0, "attributes": {"email": "alice@example.org"}
    })
    assert response.status_code == 400
    assert "identifier" in response.json()["detail"].lower()
