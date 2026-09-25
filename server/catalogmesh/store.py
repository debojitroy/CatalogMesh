import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from .fixtures import demo_catalog


def now():
    return datetime.now(UTC).isoformat()


def uid():
    return uuid.uuid4().hex[:16]


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS catalog (kind TEXT, id TEXT, body TEXT, PRIMARY KEY(kind,id));
                CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, body TEXT);
                CREATE TABLE IF NOT EXISTS mappings (id TEXT PRIMARY KEY, created_at TEXT, body TEXT);
            """)
            if not db.execute("SELECT 1 FROM catalog LIMIT 1").fetchone():
                suppliers, markets, _ = demo_catalog()
                for kind, objects in [("supplier", suppliers), ("marketplace", markets)]:
                    for obj in objects:
                        db.execute(
                            "INSERT INTO catalog VALUES(?,?,?)", (kind, obj["id"], json.dumps(obj))
                        )
            for job_id, body in db.execute("SELECT id,body FROM jobs").fetchall():
                job = json.loads(body)
                if job["status"] in ("queued", "running"):
                    job.update(
                        status="interrupted",
                        error="Server restarted. Completed mappings are preserved.",
                    )
                    db.execute("UPDATE jobs SET body=? WHERE id=?", (json.dumps(job), job_id))

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def catalog(self, kind):
        with self.connection() as db:
            return [
                json.loads(r[0])
                for r in db.execute("SELECT body FROM catalog WHERE kind=? ORDER BY rowid", (kind,))
            ]

    def save_catalog(self, kind, obj):
        with self.connection() as db:
            db.execute(
                "INSERT OR REPLACE INTO catalog VALUES(?,?,?)", (kind, obj["id"], json.dumps(obj))
            )

    def save_job(self, job):
        with self.connection() as db:
            db.execute("INSERT OR REPLACE INTO jobs VALUES(?,?)", (job["id"], json.dumps(job)))

    def jobs(self):
        with self.connection() as db:
            return [
                json.loads(r[0])
                for r in db.execute("SELECT body FROM jobs ORDER BY rowid DESC LIMIT 20")
            ]

    def save_mapping(self, mapping):
        with self.connection() as db:
            db.execute(
                "INSERT OR REPLACE INTO mappings VALUES(?,?,?)",
                (mapping["id"], mapping["created_at"], json.dumps(mapping)),
            )

    def mappings(self):
        with self.connection() as db:
            return [
                json.loads(r[0])
                for r in db.execute("SELECT body FROM mappings ORDER BY created_at DESC LIMIT 2000")
            ]

    def get_mapping(self, mapping_id):
        with self.connection() as db:
            row = db.execute("SELECT body FROM mappings WHERE id=?", (mapping_id,)).fetchone()
        return json.loads(row[0]) if row else None
