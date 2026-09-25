"""Optional local model service. All model files are pinned to a Hub revision."""

import os
import re
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

MODEL_REPO = "convaiinnovations/laya"
MODEL_REVISION = "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: dict
    questions: dict


@asynccontextmanager
async def lifespan(app):
    import laya
    import torch
    import transformers
    from huggingface_hub import snapshot_download

    repo = os.getenv("CATALOGMESH_MODEL_REPO", MODEL_REPO)
    revision = os.getenv("CATALOGMESH_MODEL_REVISION", MODEL_REVISION)
    if ("CATALOGMESH_MODEL_REPO" in os.environ) != ("CATALOGMESH_MODEL_REVISION" in os.environ):
        raise ValueError("Set both CATALOGMESH_MODEL_REPO and CATALOGMESH_MODEL_REVISION")
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("Model revision must be an immutable 40-character commit SHA")
    path = snapshot_download(
        repo,
        revision=revision,
        allow_patterns=["rl_agent_config.json", "model.safetensors", "tokenizer/*", "encoder/*"],
    )
    device = os.getenv("CATALOGMESH_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
    app.state.agent = laya.load(path, device=device)
    app.state.metadata = {
        "model_repo": repo,
        "model_revision": revision,
        "laya_version": laya.__version__,
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "device": device,
        "hardware": torch.cuda.get_device_name(0) if device == "cuda" else "CPU",
        "max_len": min(1024, app.state.agent.cfg.get("max_len", 512)),
        "head_max_len": 384,
    }
    # Serialize use of one model worker, including concurrent HTTP requests.
    import threading

    app.state.lock = threading.Lock()
    yield


app = FastAPI(title="CatalogMesh Laya worker", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ready", **app.state.metadata}


@app.post("/predict")
def predict(body: PredictRequest):
    import json

    import torch
    from laya.common import render_options, serialize_state

    if len(json.dumps(body.model_dump())) > 16000 or len(body.questions) != 1:
        raise HTTPException(400, "One bounded category question is required")
    question = body.questions.get("category", {})
    if (
        not isinstance(question, dict)
        or question.get("type") != "choice"
        or not isinstance(question.get("criteria"), dict)
        or not 2 <= len(question["criteria"]) <= 6
        or not isinstance(question.get("instructions", ""), str)
        or any(not isinstance(k, str) or not isinstance(v, str) for k, v in question["criteria"].items())
    ):
        raise HTTPException(400, "Supply 2–6 category options")
    agent = app.state.agent
    # Leave space for the question and markers; reject long inputs rather than hide truncation.
    internal = {"t": "choice", "crit": question["criteria"]}
    option_lengths = [
        len(agent.tok.encode(" " + text, add_special_tokens=False))
        for text in render_options(internal)
    ]
    state_tokens = len(agent.tok.encode(serialize_state(body.state), add_special_tokens=False))
    head_tokens = (
        len(
            agent.tok.encode(
                "choice question: " + question.get("instructions", ""), add_special_tokens=False
            )
        )
        + sum(option_lengths)
        + len(option_lengths)
    )
    if (
        max(option_lengths) > 48
        or head_tokens > 384
        or state_tokens + head_tokens + 4 > app.state.metadata["max_len"]
    ):
        raise HTTPException(400, "Input exceeds this worker's token budget; shorten descriptions")
    with app.state.lock:
        start = time.perf_counter()
        result = agent.predict(
            body.state, body.questions, max_len=app.state.metadata["max_len"], head_max_len=384
        )
        if agent.device.type == "cuda":
            torch.cuda.synchronize()
        elapsed = (time.perf_counter() - start) * 1000
    return {
        "result": result,
        "model_ms": round(elapsed, 3),
        "metadata": {
            **app.state.metadata,
            "device": str(agent.device),
            "hardware": app.state.metadata["hardware"] if agent.device.type == "cuda" else "CPU",
        },
    }
