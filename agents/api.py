"""
FastAPI REST API Server for Effect Size Hedges G Glass Delta.
"""
from typing import Dict, Any, List
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from effect_sizes import calculate_metrics
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")
WEB_DIR = Path(__file__).resolve().parents[1] / 'web'

app = FastAPI(
    title="Effect Size Hedges G Glass Delta API",
    description="Effect-size calculations and a demonstration audit endpoint",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    query: str


class EffectSizeRequest(BaseModel):
    mean1: float
    mean2: float
    std1: float
    std2: float
    n1: int
    n2: int


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/app.js", include_in_schema=False)
def calculator_script():
    return FileResponse(WEB_DIR / "app.js", media_type="text/javascript")


@app.get("/audit-console", include_in_schema=False)
def audit_console():
    return FileResponse(WEB_DIR / "audit.html")


@app.post("/api/effect-size")
def api_effect_size(payload: EffectSizeRequest):
    try:
        return calculate_metrics(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "effect-size-hedges-g-glass-delta", "domain": "Clinical & Biomedical AI", "version": "1.0.0"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "ACTIVE"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
