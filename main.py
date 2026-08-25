from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict, Optional
import os

app = FastAPI(title="MagicPin AI Challenge", docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json")

class TickRequest(BaseModel):
    trigger_id: Optional[str] = "test_id"
    merchant: Dict[str, Any] = {}
    trigger: Dict[str, Any] = {}
    context: Dict[str, Any] = {}
    customer: Dict[str, Any] = {}

@app.get("/")
def root():
    return {"docs": "/docs"}

@app.get("/v1/healthz", tags=["healthz"])
def healthz():
    return {"status": "ok"}

@app.get("/v1/metadata", tags=["meta"])
def metadata():
    return {"model": "rule-based-v1", "version": "1.0"}

@app.get("/v1/context", tags=["context"])
def get_context():
    return {"context": {}}

@app.post("/v1/context", tags=["context"])
def post_context(payload: Dict[str, Any]):
    return {"status": "saved"}

@app.post("/v1/tick", tags=["tick"])
def tick(req: TickRequest):
    m = req.merchant or {}
    t = req.trigger or {}
    c = req.customer or {}
    cat = str(m.get("category", "")).lower()
    name = m.get("identity", {}).get("name", "us")
    ttype = str(t.get("type", "")).lower()

    if "low" in ttype and not c.get("is_loyal"):
        return {"body": "", "cta": "", "send_as": "none", "suppression_key": str(req.trigger_id), "rationale": "skip low intent"}

    if "food" in cat or "restaurant" in cat:
        body = f"{c.get('name','Hi')}, {name} is live with today's special. Want to order?"
        cta = "ORDER NOW"
    elif "salon" in cat or "spa" in cat:
        body = f"{name} has free slot today. Last cut 20 days ago. Book?"
        cta = "BOOK"
    else:
        body = f"{name} has Rs 299 discounted check-up. Should we book?"
        cta = "YES"

    return {"body": body[:160], "cta": cta, "send_as": "whatsapp", "suppression_key": t.get("suppression_key", str(req.trigger_id)), "rationale": cat}

@app.post("/v1/reply", tags=["reply"])
def reply(payload: Dict[str, Any]):
    return {"reply": "Thanks! How can I help?"}