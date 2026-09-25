import asyncio
import csv
import io
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from .mapping import prepare, validate_prediction
from .models import MappingRequest, Marketplace, ReviewRequest, Supplier
from .store import Store, now, uid

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
logger = logging.getLogger(__name__)


def read_recording(path):
    return json.loads(path.read_text()) if path.exists() else {"rows": []}


def csv_safe(value):
    text = str(value or "")
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text


def create_app(db_path=None, live=None, recording_path=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.store = Store(
            db_path or ROOT / os.getenv("CATALOGMESH_DB", "data/catalogmesh.db")
        )
        app.state.live = (
            live if live is not None else os.getenv("CATALOGMESH_ENABLE_LIVE") == "true"
        )
        app.state.laya_url = os.getenv("CATALOGMESH_LAYA_URL", "http://127.0.0.1:8120")
        app.state.recording = read_recording(recording_path or ROOT / "recordings/showcase.json")
        app.state.recorded = {r["fingerprint"]: r for r in app.state.recording["rows"]}
        app.state.tasks = set()
        yield
        tasks = list(app.state.tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    app = FastAPI(title="CatalogMesh", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def limit_body(request, call_next):
        if request.method in ("POST", "PUT"):
            body = await request.body()
            if len(body) > 3_000_000:
                return Response("Import exceeds 3 MB", status_code=413)
        return await call_next(request)

    @app.get("/api/state")
    async def state():
        store = app.state.store
        return {
            "suppliers": store.catalog("supplier"),
            "marketplaces": store.catalog("marketplace"),
            "jobs": store.jobs(),
            "mappings": store.mappings(),
            "live_enabled": app.state.live,
            "recording": {k: v for k, v in app.state.recording.items() if k != "rows"},
        }

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "live_enabled": app.state.live}

    @app.get("/api/evaluation")
    async def evaluation():
        report = read_recording(ROOT / "evals/baseline.json")
        return report

    @app.post("/api/suppliers", status_code=201)
    async def supplier(body: Supplier):
        app.state.store.save_catalog("supplier", body.model_dump())
        return body

    @app.post("/api/marketplaces", status_code=201)
    async def marketplace(body: Marketplace):
        current = next(
            (m for m in app.state.store.catalog("marketplace") if m["id"] == body.id), None
        )
        if current and current["version"] == body.version and current != body.model_dump():
            raise HTTPException(409, "Change the taxonomy version when editing its definition")
        app.state.store.save_catalog("marketplace", body.model_dump())
        return body

    async def execute(job, work):
        store = app.state.store
        job["status"] = "running"
        store.save_job(job)
        try:
            async with httpx.AsyncClient(timeout=120, follow_redirects=False) as client:
                for supplier, product, market, prepared in work:
                    row = {
                        "id": uid(),
                        "created_at": now(),
                        "job_id": job["id"],
                        "supplier_id": supplier["id"],
                        "supplier_name": supplier["name"],
                        "marketplace_id": market["id"],
                        "marketplace_name": market["name"],
                        "product": product,
                        "taxonomy": market,
                        **prepared,
                        "mode": job["mode"],
                        "review": None,
                    }
                    try:
                        if job["mode"] == "recorded":
                            recorded = app.state.recorded[prepared["fingerprint"]]
                            result = validate_prediction(recorded["raw_response"], prepared)
                            row.update(
                                result,
                                model_ms=recorded["model_ms"],
                                metadata=app.state.recording["metadata"],
                            )
                        else:
                            response = await client.post(
                                app.state.laya_url.rstrip("/") + "/predict",
                                json={
                                    "state": prepared["state"],
                                    "questions": prepared["questions"],
                                },
                            )
                            response.raise_for_status()
                            data = response.json()
                            row.update(validate_prediction(data["result"], prepared))
                            row.update(model_ms=data["model_ms"], metadata=data["metadata"])
                        row["status"] = (
                            "unresolved" if row["category_id"] == "unmatched" else "proposed"
                        )
                    except (httpx.HTTPError, ValueError, KeyError, TypeError):
                        row.update(
                            status="error",
                            error="Laya inference failed or returned an invalid response. No mapping was substituted.",
                        )
                        job["errors"] += 1
                    store.save_mapping(row)
                    job["completed"] += 1
                    store.save_job(job)
                    await asyncio.sleep(0)
            job["status"] = "completed" if job["errors"] == 0 else "completed_with_errors"
        except asyncio.CancelledError:
            job.update(
                status="interrupted", error="Server stopped; completed mappings were preserved."
            )
            raise
        except Exception:
            logger.exception("Mapping job failed")
            job.update(
                status="error", error="Job failed unexpectedly; completed mappings were preserved."
            )
        finally:
            store.save_job(job)

    @app.post("/api/jobs", status_code=201)
    async def start_job(body: MappingRequest):
        if app.state.tasks:
            raise HTTPException(409, "A mapping batch is already running")
        if body.mode == "live" and not app.state.live:
            raise HTTPException(
                400, "Live inference is disabled. Start the Laya worker and enable live mode."
            )
        suppliers = {s["id"]: s for s in app.state.store.catalog("supplier")}
        markets = {m["id"]: m for m in app.state.store.catalog("marketplace")}
        if (
            not set(body.supplier_ids) <= suppliers.keys()
            or not set(body.marketplace_ids) <= markets.keys()
        ):
            raise HTTPException(400, "Unknown supplier or marketplace")
        count = sum(len(suppliers[s]["products"]) for s in set(body.supplier_ids)) * len(
            set(body.marketplace_ids)
        )
        if count > 300:
            raise HTTPException(400, "This demo supports up to 300 decisions per batch")
        work = []
        for sid in dict.fromkeys(body.supplier_ids):
            for product in suppliers[sid]["products"]:
                for mid in dict.fromkeys(body.marketplace_ids):
                    market = markets[mid]
                    prepared = prepare(product, market)
                    if (
                        body.mode == "recorded"
                        and prepared["fingerprint"] not in app.state.recorded
                    ):
                        raise HTTPException(
                            400,
                            "Recorded results cover the unchanged sample catalogs only. Use live Laya for imported or edited data.",
                        )
                    work.append((suppliers[sid], product, market, prepared))
        job = {
            "id": uid(),
            "created_at": now(),
            "mode": body.mode,
            "status": "queued",
            "total": count,
            "completed": 0,
            "errors": 0,
        }
        app.state.store.save_job(job)
        task = asyncio.create_task(execute(job, work))
        app.state.tasks.add(task)
        task.add_done_callback(app.state.tasks.discard)
        return job

    @app.post("/api/mappings/{mapping_id}/review")
    async def review(mapping_id: str, body: ReviewRequest):
        row = app.state.store.get_mapping(mapping_id)
        if not row:
            raise HTTPException(404, "Mapping not found")
        allowed = {c["id"] for c in row["taxonomy"]["categories"]} | {"unmatched"}
        if body.category_id not in allowed or row["status"] == "error":
            raise HTTPException(400, "Choose a category from this decision's taxonomy")
        row["review"] = {**body.model_dump(), "created_at": now()}
        app.state.store.save_mapping(row)
        return row

    @app.get("/api/export")
    async def export():
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "mapping_id",
                "supplier",
                "product_id",
                "product_title",
                "marketplace",
                "taxonomy_version",
                "model_category",
                "review_category",
                "review_note",
                "source",
                "status",
            ]
        )
        for row in app.state.store.mappings():
            review = row.get("review") or {}
            writer.writerow(
                [
                    csv_safe(v)
                    for v in [
                        row["id"],
                        row["supplier_name"],
                        row["product"]["id"],
                        row["product"]["title"],
                        row["marketplace_name"],
                        row["taxonomy"]["version"],
                        row.get("category_id"),
                        review.get("category_id"),
                        review.get("note"),
                        row["mode"],
                        row["status"],
                    ]
                ]
            )
        return Response(
            buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="catalogmesh-mappings.csv"'},
        )

    @app.get("/api/mappings/{mapping_id}/export")
    async def export_decision(mapping_id: str):
        row = app.state.store.get_mapping(mapping_id)
        if not row:
            raise HTTPException(404, "Mapping not found")
        return Response(
            json.dumps(row, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="catalogmesh-{mapping_id}.json"'
            },
        )

    if (ROOT / "dist").exists():
        app.mount("/", StaticFiles(directory=ROOT / "dist", html=True), name="frontend")
    return app


app = create_app()
