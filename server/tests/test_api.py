import asyncio
import copy

import httpx
import pytest
from catalogmesh.fixtures import demo_catalog
from catalogmesh.main import create_app, csv_safe
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "app.db", live=False)) as c:
        yield c


def settle(client):
    async def wait():
        for _ in range(200):
            jobs = client.app.state.store.jobs()
            if jobs and jobs[0]["status"] not in ("running", "queued"):
                return
            await asyncio.sleep(0.02)
        raise AssertionError("Job did not complete")

    client.portal.call(wait)


def test_recorded_many_to_many_batch_review_export_and_persistence(client):
    response = client.post(
        "/api/jobs",
        json={"supplier_ids": ["northline"], "marketplace_ids": ["harbor", "bazaar", "mercury"]},
    )
    assert response.status_code == 201
    assert response.json()["total"] == 18
    settle(client)
    state = client.get("/api/state").json()
    assert len(state["mappings"]) == 18
    row = state["mappings"][0]
    original = row["category_id"]
    response = client.post(
        f"/api/mappings/{row['id']}/review",
        json={"category_id": "unmatched", "note": "Needs supplier clarification"},
    )
    assert response.status_code == 200
    assert response.json()["category_id"] == original
    assert response.json()["review"]["category_id"] == "unmatched"
    exported = client.get("/api/export")
    assert "Needs supplier clarification" in exported.text
    assert client.get(f"/api/mappings/{row['id']}/export").json()["metadata"]["model_revision"]


def test_new_destination_requires_live_and_versioned_edits(client):
    _, markets, _ = demo_catalog()
    imported = copy.deepcopy(markets[0])
    imported.update(id="fresh", name="Fresh destination")
    assert client.post("/api/marketplaces", json=imported).status_code == 201
    response = client.post(
        "/api/jobs", json={"supplier_ids": ["northline"], "marketplace_ids": ["fresh"]}
    )
    assert response.status_code == 400
    assert client.get("/api/state").json()["jobs"] == []
    imported["categories"][0]["description"] += " New scope."
    assert client.post("/api/marketplaces", json=imported).status_code == 409
    imported["version"] = "2"
    assert client.post("/api/marketplaces", json=imported).status_code == 201


def test_live_and_invalid_selection_fail_before_creating_jobs(client):
    for payload in [
        {"supplier_ids": ["northline"], "marketplace_ids": ["harbor"], "mode": "live"},
        {"supplier_ids": ["unknown"], "marketplace_ids": ["harbor"]},
        {"supplier_ids": ["northline"], "marketplace_ids": ["unknown"]},
    ]:
        assert client.post("/api/jobs", json=payload).status_code == 400
    assert client.get("/api/state").json()["jobs"] == []
    assert client.get("/api/mappings/missing/export").status_code == 404


def test_upstream_failure_never_becomes_a_recorded_success(tmp_path, monkeypatch):
    async def fail(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx.AsyncClient, "post", fail)
    with TestClient(create_app(db_path=tmp_path / "live.db", live=True)) as client:
        assert (
            client.post(
                "/api/jobs",
                json={"supplier_ids": ["northline"], "marketplace_ids": ["harbor"], "mode": "live"},
            ).status_code
            == 201
        )
        settle(client)
        state = client.get("/api/state").json()
        assert state["jobs"][0]["status"] == "completed_with_errors"
        assert all(r["status"] == "error" and r["mode"] == "live" for r in state["mappings"])


@pytest.mark.parametrize("text", ["=CMD()", "+formula", "-formula", "@SUM()", "  =formula"])
def test_csv_formula_cells_are_escaped(text):
    assert csv_safe(text).startswith("'")
