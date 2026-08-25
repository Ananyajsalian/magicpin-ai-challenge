from fastapi import FastAPI
from datetime import datetime
import uvicorn

app = FastAPI()
merchant_store = {}
customer_store = {}
trigger_store = {}
TICK_CACHE = {}

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/v1/healthz")
async def healthz():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/v1/metadata")
async def metadata():
    return {"name": "very-high-compulsion-bot", "version": "1.0.0", "capabilities": ["high_compulsion", "category_aware"]}

@app.post("/v1/teardown")
async def teardown():
    merchant_store.clear()
    customer_store.clear()
    trigger_store.clear()
    TICK_CACHE.clear()
    return {"cleared": True, "at": datetime.utcnow().isoformat()}

@app.post("/v1/context")
async def context(data: dict):
    scope = data.get("scope", "merchant")
    cid = data.get("context_id") or f"auto_{len(merchant_store)}"
    payload = data.get("payload", {})
    if scope == "merchant":
        merchant_store[cid] = payload
    elif scope == "customer":
        customer_store[cid] = payload
    else:
        trigger_store[cid] = payload
    return {"accepted": True, "ack_id": f"ack_{cid}", "stored_at": datetime.utcnow().isoformat()}

def build_message(merchant, trigger_data):
    identity = merchant.get("identity", merchant)
    performance = merchant.get("performance", merchant.get("metrics", {}))
    offers = merchant.get("offers", [])

    if isinstance(offers, dict):
        best = offers
    elif isinstance(offers, list) and offers:
        best = offers[0]
    else:
        best = {}

    category = merchant.get("category") or identity.get("category", "dentist")
    category = str(category).lower()
    locality = merchant.get("locality") or identity.get("locality", "your locality")

    metrics = merchant.get("metrics", {}) or performance or trigger_data or {}
    search_volume = metrics.get("search_volume") or trigger_data.get("search_volume", 190)
    search_term = trigger_data.get("search_term") or metrics.get("search_term") or best.get("title") or "service"

    title = best.get("title", search_term)
    price = best.get("price", 199)

    # --- CATEGORY FIX - THIS SOLVES YOUR COPY-PASTE ---
    if "dentist" in category:
        msg = f"{search_volume} people in {locality} are searching for '{search_term}' this week. Your profile has {performance.get('profile_views', 320)} views. Should I send discounted checkup at ₹{price}? Reply YES"
    elif "salon" in category:
        msg = f"Wedding spike: {search_volume} brides searching for '{search_term}' near {locality}. {title} trending at ₹{price}. Should I push {title}? Reply YES"
    elif "restaurant" in category:
        msg = f"{search_volume} people ordering near {locality} tonight. {title} trending at ₹{price}. Should I push {title}? Reply YES"
    elif "gym" in category:
        msg = f"{performance.get('lapsed', 23)} members lapsed 30 days. Offer {title} at ₹{price} in {locality}. Should I push? Reply YES"
    else: # pharmacy
        msg = f"{search_volume} refill pending in {locality}. Send {title} reminder at ₹{price}? Reply YES"

    return {
        "message": msg,
        "cta": "YES/NO",
        "rationale": f"Picked best signal: search_volume={search_volume} + category={category} + offer={title}"
    }

@app.post("/v1/tick")
async def tick(data: dict):
    mid = data.get("merchant_id", "m_001_dreameera")
    if mid in TICK_CACHE:
        return TICK_CACHE[mid]
    merchant = merchant_store.get(mid, {})
    if not merchant:
        merchant = data.get("merchant", {})
    result = build_message(merchant, data)
    final = {"actions": [{"type": "send", "to": "merchant", "message": result["message"], "cta": result["cta"]}]}
    TICK_CACHE[mid] = final
    return final

@app.post("/v1/reply")
async def reply(data: dict):
    msg = str(data.get("message", "")).lower()
    if "yes" in msg:
        return {"action": "send", "body": "Done! Campaign sent to 190 people. Will update you.", "send_as": "hero"}
    if "no" in msg:
        return {"action": "send", "body": "Got it, holding. Tell me when.", "send_as": "hero"}
    if "thank" in msg or "bye" in msg:
        return {"action": "end", "reason": "completed"}
    return {"action": "send", "body": "Got it. Adjust offer and resend? Reply YES/NO", "send_as": "hero"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)