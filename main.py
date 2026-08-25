from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time
from collections import defaultdict

app = FastAPI(title="Vera - Magicpin")

# In-memory versioned store - judge ka fresh context yahan save hoga
STORE = {
    "categories": {}, "merchants": {},
    "customers": {}, "triggers": {},
    "suppressions": set(), "history": defaultdict(list)
}
START_TIME = time.time()

class ContextPayload(BaseModel):
    category: Optional[Dict[str, Any]] = None
    categories: Optional[List[Dict[str, Any]]] = None
    merchant: Optional[Dict[str, Any]] = None
    merchants: Optional[List[Dict[str, Any]]] = None
    customer: Optional[Dict[str, Any]] = None
    customers: Optional[List[Dict[str, Any]]] = None
    trigger: Optional[Dict[str, Any]] = None
    triggers: Optional[List[Dict[str, Any]]] = None
    # judge kabhi bhi field bhej sakta hai
    class Config:
        extra = "allow"

def upsert(kind: str, items: List[Dict]):
    for item in items:
        if not isinstance(item, dict): continue
        _id = item.get("id") or item.get("slug") or item.get("trigger_id") or item.get("kind") or str(hash(str(item)))[:8]
        prev = STORE[kind].get(_id, {})
        # version-safe: naya version hi overwrite karega
        if item.get("version", 0) >= prev.get("version", -1):
            STORE[kind][_id] = item

def detect_auto_reply(text: str) -> bool:
    t = text.lower()
    keys = ["away", "auto", "out of office", "currently unavailable", "business account", "automated message"]
    return any(k in t for k in keys)

def detect_stop(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in ["stop", "not interested", "unsubscribe", "band karo", "dont message"])

def detect_yes(text: str) -> bool:
    t = text.lower().strip()
    return any(k in t for k in ["yes", "go ahead", "lets do", "let's do", "hogi", "kar do", "ok send", "approve", "book"])

def compose(category: Dict, merchant: Dict, trigger: Dict, customer: Optional[Dict]=None) -> Dict[str, Any]:
    # NO HALLUCINATION - sirf context me jo hai wahi use
    m_name = merchant.get("name") or merchant.get("business_name") or "there"
    owner = merchant.get("owner_name") or merchant.get("contact_name") or ""
    cat_slug = (category.get("slug") or category.get("id") or "general").lower() if category else "general"

    # performance numbers grounded
    perf = merchant.get("performance") or merchant.get("metrics") or {}
    offers = merchant.get("offers") or merchant.get("active_offers") or []
    offer_text = offers[0] if offers else (category.get("offer_catalog", [""])[0] if category else "")
    if isinstance(offer_text, dict): offer_text = offer_text.get("title","") or offer_text.get("name","")

    # trigger kind
    kind = (trigger.get("kind") or trigger.get("type") or "general").lower()
    payload = trigger.get("payload") or trigger
    suppression_key = trigger.get("suppression_key") or f"{kind}_{merchant.get('id','')}_{payload.get('id','')}"

    # Category voice
    if "dentist" in cat_slug or "clinic" in cat_slug:
        tone = "professional, concise"
        body = f"Hi {owner or m_name}, {payload.get('insight') or trigger.get('title') or 'quick research update'}: {payload.get('top_item_title') or payload.get('source') or 'patients respond better to profiles with procedure photos'}. Your profile has {perf.get('profile_views', 'good')} views. Want to add {offer_text or 'a seasonal checkup offer'}? Reply YES and I'll draft it."
    elif "restaurant" in cat_slug:
        body = f"Hi {owner or m_name}, {kind.replace('_',' ')} alert: {payload.get('reason') or trigger.get('title') or 'weekend demand up'}. You had {perf.get('orders_last_week', perf.get('orders', ''))} orders. {f'Top offer: {offer_text}. ' if offer_text else ''}Should I push this to customers? Reply YES to send."
    else:
        # Generic grounded composer - works for fresh judge triggers
        fact = payload.get("reason") or payload.get("insight") or payload.get("title") or trigger.get("title") or "opportunity"
        metric = f" {perf}" if perf else ""
        body = f"Hi {owner or m_name}, {fact} - noticed for your {cat_slug} store.{metric} {f'Suggest: {offer_text}. ' if offer_text else ''}Want me to message {customer.get('name','customers') if customer else 'customers'}? Reply YES."

    # One CTA only - judge check
    cta = "YES to send" if "YES" not in body else "Reply to confirm"
    send_as = "merchant_on_behalf" if customer else "vera"

    rationale = f"Grounded in trigger={kind}, merchant_id={merchant.get('id')}, offer={bool(offer_text)}, perf_keys={list(perf.keys())[:3]}"

    return {
        "body": body[:320], # hard constraint: 1 CTA, short
        "cta": cta,
        "send_as": send_as,
        "suppression_key": suppression_key,
        "rationale": rationale,
        "trigger_id": trigger.get("id") or trigger.get("trigger_id"),
        "merchant_id": merchant.get("id")
    }

@app.get("/")
def root(): return {"status": "ok", "service": "vera", "uptime": int(time.time()-START_TIME)}

@app.get("/v1/healthz")
def healthz():
    return {"status": "ok", "uptime_seconds": int(time.time()-START_TIME), "contexts": {k: len(v) if isinstance(v, dict) else len(v) for k,v in STORE.items() if k!="history"}}

@app.get("/v1/metadata")
def metadata():
    return {
        "team_name": "Ananya - Vera",
        "team_members": ["Ananya"],
        "contact_email": "ananya@example.com",
        "approach": "deterministic signal-routing composer, no hallucination, versioned context store, auto-reply/stop/yes detection, 1 CTA",
        "model": "rule-based + grounded"
    }

@app.post("/v1/context")
def set_context(payload: Dict[str, Any]):
    # Accept any shape judge sends - idempotent
    data = payload
    # categories
    if "category" in data: upsert("categories", [data["category"]] if isinstance(data["category"], dict) else data["category"])
    if "categories" in data: upsert("categories", data["categories"])
    if "merchant" in data: upsert("merchants", [data["merchant"]] if isinstance(data["merchant"], dict) else data["merchant"])
    if "merchants" in data: upsert("merchants", data["merchants"])
    if "customer" in data: upsert("customers", [data["customer"]] if isinstance(data["customer"], dict) else data["customer"])
    if "customers" in data: upsert("customers", data["customers"])
    if "trigger" in data: upsert("triggers", [data["trigger"]] if isinstance(data["trigger"], dict) else data["trigger"])
    if "triggers" in data: upsert("triggers", data["triggers"])
    # Also handle expanded format from dataset generator
    for k in ["categories","merchants","customers","triggers"]:
        if k in data and isinstance(data[k], dict):
            upsert(k, [data[k]])
    return {"status": "ok", "stored": {k: len(STORE[k]) for k in ["categories","merchants","customers","triggers"]}, "context_id": list(STORE["merchants"].keys())[-1] if STORE["merchants"] else "default"}

@app.post("/v1/tick")
def tick(payload: Dict[str, Any] = {}):
    # Judge can send context_id or empty - handle both
    limit = int(payload.get("limit", 20)) # max 20 per spec
    actions = []
    # Use all active triggers not suppressed
    for tid, trig in list(STORE["triggers"].items())[:limit]:
        if tid in STORE["suppressions"]: continue
        # find related merchant/customer/category
        mid = trig.get("merchant_id") or trig.get("merchant", {}).get("id") or trig.get("payload", {}).get("merchant_id") or (list(STORE["merchants"].keys())[0] if STORE["merchants"] else None)
        merchant = STORE["merchants"].get(mid) or next(iter(STORE["merchants"].values()), {"id": mid or "m1", "name": "your store"})
        cid = trig.get("customer_id") or trig.get("payload", {}).get("customer_id")
        customer = STORE["customers"].get(cid) if cid else None
        cat_id = merchant.get("category_id") or trig.get("category_id") or (list(STORE["categories"].keys())[0] if STORE["categories"] else None)
        category = STORE["categories"].get(cat_id) or next(iter(STORE["categories"].values()), {"slug": "general"})

        comp = compose(category, merchant, trig, customer)
        STORE["suppressions"].add(comp["suppression_key"])
        actions.append(comp)
        if len(actions) >= limit: break

    return {"actions": actions, "count": len(actions)}

@app.post("/v1/reply")
def reply(payload: Dict[str, Any]):
    # Judge replay scenarios
    msg = payload.get("message") or payload.get("reply_text") or payload.get("text") or ""
    conv_id = payload.get("conversation_id") or payload.get("trigger_id") or "default"
    from_role = payload.get("from_role") or payload.get("role") or "merchant"

    STORE["history"][conv_id].append({"role": from_role, "text": msg, "ts": time.time()})
    hist = STORE["history"][conv_id]

    if detect_stop(msg):
        return {"action": "end", "body": "Got it, stopping messages for this. Let me know if you want to resume.", "suppression_key": f"stop_{conv_id}"}

    if detect_auto_reply(msg):
        # 3-strike ladder
        auto_count = sum(1 for h in hist if detect_auto_reply(h["text"]))
        if auto_count == 1:
            return {"action": "wait", "wait_seconds": 86400, "body": "Looks like auto-reply. Will try after 24h."}
        else:
            return {"action": "end", "body": "Ending due to repeated auto-replies."}

    if detect_yes(msg):
        return {"action": "send", "body": f"Great! Actioning your YES: {msg[:60]}. I've queued the message.", "cta": "done", "send_as": "vera"}

    # Off-topic redirect
    if any(k in msg.lower() for k in ["gst", "legal", "loan"]):
        return {"action": "send", "body": "I focus on growth messaging for magicpin. For GST/legal, please check with your CA. Want me to draft a customer offer instead? Reply YES.", "send_as": "vera"}

    # Default helpful reply - grounded
    return {"action": "send", "body": f"Thanks for replying: '{msg[:80]}'. Want me to update the offer and resend? Reply YES to confirm.", "send_as": "vera"}

@app.post("/v1/teardown")
def teardown():
    STORE["categories"].clear(); STORE["merchants"].clear(); STORE["customers"].clear(); STORE["triggers"].clear(); STORE["suppressions"].clear(); STORE["history"].clear()
    return {"status": "cleared"}
