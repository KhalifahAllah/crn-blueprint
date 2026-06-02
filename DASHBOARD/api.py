"""
DASHBOARD/api.py
CRN Telemetry Ingestion API — v0.1-alpha

Ingests signed VRFP envelopes from edge nodes, verifies Ed25519 signatures,
stores payloads in memory (replace with SQLite/PostgreSQL for production),
and exposes read-only endpoints for the transparency dashboard.

Author: Wan Ahmad Masuwaradi bin Wan Abdul Wahab
AI-assisted: Claude (Anthropic)
"""

import hashlib
import json
from collections import deque
from datetime import datetime, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="CRN Transparency API",
    description="Community Resource Node — Verifiable Resource Flow Protocol.",
    version="0.1.0-alpha",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

MAX_PAYLOADS = 1000
payload_store: deque[dict] = deque(maxlen=MAX_PAYLOADS)
registered_nodes: dict[str, str] = {}

class NodeMetrics(BaseModel):
    power_density_mw_per_m2: float = Field(ge=50.0, le=200.0)
    module_power_mw: float = Field(ge=0.0)
    soil_orp_mv: float = Field(ge=-300.0, le=-100.0)
    water_yield_l: float = Field(ge=0.0)
    ambient_rh_pct: float = Field(ge=0.0, le=100.0)
    ambient_temp_c: float
    biome: str
    data_status: str

class VRFPEnvelope(BaseModel):
    node_id: str
    timestamp: str
    metrics: NodeMetrics
    vrfp_signature: str

class NodeRegistration(BaseModel):
    node_id: str
    public_key_hex: str

def verify_ed25519(public_key_hex: str, signature_hex: str, metrics: dict) -> bool:
    try:
        pub_bytes = bytes.fromhex(public_key_hex)
        public_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
        canonical = json.dumps(metrics, sort_keys=True, separators=(',', ':')).encode()
        sig = bytes.fromhex(signature_hex)
        public_key.verify(sig, canonical)
        return True
    except:
        return False

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "node": "CRN Transparency API - Claude Edition",
        "docs": "Go to /docs to see the endpoints!"
    }

@app.post("/nodes/register", tags=["Nodes"], status_code=status.HTTP_201_CREATED)
def register_node(reg: NodeRegistration):
    try:
        raw = bytes.fromhex(reg.public_key_hex)
        Ed25519PublicKey.from_public_bytes(raw)
    except:
        raise HTTPException(status_code=400, detail="Invalid public key")
    registered_nodes[reg.node_id] = reg.public_key_hex
    return {"registered": reg.node_id, "status": "accepted"}

@app.post("/telemetry/ingest", tags=["Telemetry"])
def ingest_payload(envelope: VRFPEnvelope):
    if envelope.node_id not in registered_nodes:
        raise HTTPException(status_code=403, detail="Node not registered.")
    
    metrics_dict = envelope.metrics.model_dump()
    pub_hex = registered_nodes[envelope.node_id]

    if not verify_ed25519(pub_hex, envelope.vrfp_signature, metrics_dict):
        raise HTTPException(status_code=422, detail="VRFP signature verification failed.")

    record = {
        "node_id": envelope.node_id,
        "timestamp": envelope.timestamp,
        "metrics": metrics_dict,
        "vrfp_signature": envelope.vrfp_signature,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }
    payload_store.append(record)
    return {"status": "accepted", "payload_count": len(payload_store)}

@app.get("/telemetry/latest", tags=["Telemetry"])
def get_latest():
    return {"payloads": list(payload_store)[-10:]}
