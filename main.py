from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict

app = FastAPI(
    title="MagicPin AI Challenge",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

class TickRequest(BaseModel):
    trigger_id: str
    merchant: Dict[str, Any] = {}
    trigger: Dict[str, Any] = {}
    context: Dict[str, Any] = {}

@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}

@app.get("/v1/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/v1/metadata")
def metadata():
  "name": "vera-bot",
        "team": "Ananya J Salian",
        "team_name": "Ananya J Salian",  # for judge
        "contact_email": "ananyajsalian@gmail.com",
        "model_name": "vera-bot",
        "version": "1.0.0",
        "endpoints": ["/v1/healthz", "/v1/metadata", "/v1/context", "/v1/tick", "/v1/reply"]

@app.get("/v1/context")
def get_context():
    return {"context": {}}

@app.post("/v1/tick")
def tick(req: TickRequest):
    # tumhara purana logic yahi aayega
    merchant_name = req.merchant.get("identity", {}).get("name", "there") if isinstance(req.merchant.get("identity"), dict) else "there"
    body = f"Hi {merchant_name}! Check our latest offer."
    return {
        "body": body,
        "cta": "YES",
        "send_as": "whatsapp",
        "suppression_key": req.trigger.get("suppression_key", req.trigger_id),
        "rationale": "composed"
    }

@app.post("/v1/reply")
def reply(payload: Dict[str, Any]):
    return {"reply": "Thanks for your message!"}
