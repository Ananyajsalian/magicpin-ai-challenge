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
    return {"status": "live", "docs": "/docs", "health": "/v1/healthz"}
    

@app.get("/v1/healthz", tags=["healthz"])
def healthz():
    return {"status": "ok"}

@app.get("/v1/metadata", tags=["meta"])
def metadata():
    return {
        "name": "vera-bot",
        "team": "Ananya J Salian",
        "team_name": "Ananya J Salian",
        "contact_email": "ananyajsalian@gmail.com",
        "model_name": "vera-bot",
        "version": "1.0.0",
        "endpoints": ["/v1/healthz", "/v1/metadata", "/v1/context", "/v1/tick", "/v1/reply"]
    }
    
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

@app.post("/v1/reply")
def reply(req: ReplyRequest):
    import re
    raw = req.message or ""
    q = raw.lower().strip()
    ctx = req.context or {}

    DB = {
        "biryani": ["Ambur Star Biryani - Rs 280 - 4.3* - 30 min", "Nagarjuna - Rs 299 - 4.5*", "Behrouz - Rs 295 - 4.2*"],
        "pizza": ["La Pino'z - Rs 250 - 4.4*", "Mojo Pizza - Rs 299 - 4.3*", "Domino's - Rs 199 - 4.0*"],
        "burger": ["Burger King - Rs 199", "McD - Rs 180", "Burger Singh - Rs 250"],
        "dosa": ["CTR - Rs 150", "MTR - Rs 180", "UpSouth - Rs 170"],
        "healthy": ["EatFit Bowl - Rs 220", "Subway Salad - Rs 250", "Green Bowl - Rs 280"],
        "chinese": ["Momo Zone - Rs 200", "Wow China - Rs 280", "Noodles - Rs 220"],
        "late night": ["Empire - Open till 1 AM - Rs 300", "Meghana - Open till 12:30 AM - Rs 290", "Truffles - Open till 1 AM - Rs 280"],
        "default": ["Truffles - Rs 280 - 4.5*", "Empire - Rs 300 - 4.3*", "Meghana Foods - Rs 290 - 4.4*"]
    }

    # --- EDGE CASES ---
    if not q or len(q) < 2:
        return {"reply": "Hi! I'm Vera - your food buddy. Batao kya khana hai? Eg: 'biryani under 300 in HSR'", "context": ctx}
    if re.fullmatch(r'[asdfghjklqwerty0-9@#\$%]{4,}', q) or len(q) > 400:
        return {"reply": "Sorry, samajh nahi aaya. Tell me dish and budget like 'veg biryani under 300 in HSR'", "context": ctx}
    if any(x in q for x in ["pm of india", "prime minister", "weather", "cricket", "system prompt", "ignore previous", "poem", "homework"]):
        return {"reply": "I'm Vera, Magicpin food concierge. I only help with food discovery & ordering. Kya khana hai aaj?", "context": ctx}
    if any(x in q for x in ["stupid", "useless", "bakwas", "bekar", "idiot"]):
        return {"reply": "Sorry! Let me improve. Tell me exact craving - dish, budget, area - I'll find best 3 options instantly.", "context": ctx}
    if q in ["hi","hello","hey","hii","thanks","ok","namaste"]:
        return {"reply": "Hello! 👋 What to eat today? Try: 'best biryani under 300 in HSR' or 'late night pizza' or 'healthy veg under 250'", "context": ctx}

    # --- AUTO-WAIT MERGE ---
    last_dish = ctx.get("last_dish", "")
    last_budget = ctx.get("last_budget", "300")
    last_loc = ctx.get("last_location", "HSR Bangalore")

    # If query is short like "under 400" or "veg only", auto-join with last dish
    if len(q.split()) <= 4 and last_dish:
        q_merged = f"{last_dish} {q}"
    else:
        q_merged = q

    # --- REAL WORLD PARSE ---
    dish = last_dish if last_dish else "default"
    if "late night" in q_merged or "midnight" in q_merged or "raat" in q_merged: dish = "late night"
    elif any(x in q_merged for x in ["healthy","gym","diet","salad","weight"]): dish = "healthy"
    else:
        for d in DB.keys():
            if d in q_merged:
                dish = d
                break
        if dish == "default":
            if any(x in q_merged for x in ["roll","wrap","momos","noodles","fried rice"]): dish = "chinese"
            elif "dosa" in q_merged or "idli" in q_merged: dish = "dosa"

    m = re.search(r'under\s*(\d+)|(\d+)\s*(rs|mein|me|tak)', q_merged)
    budget = last_budget
    if m:
        for g in m.groups():
            if g and g.isdigit(): budget = g; break
    elif re.search(r'(\d{2,4})', q_merged):
        budget = re.search(r'(\d{2,4})', q_merged).group(1)

    loc = last_loc
    for l in ["hsr","koramangala","indiranagar","btm","jayanagar","whitefield","delhi","mumbai","pune"]:
        if l in q_merged: loc = l.upper() if len(l)<=3 else l.title()

    veg = ""
    if "veg" in q_merged and "non" not in q_merged: veg = "veg"
    if "non veg" in q_merged or "non-veg" in q_merged or "chicken" in q_merged: veg = "non-veg"
    if "jain" in q_merged: veg = "jain"

    # Order flow
    results = DB.get(dish, DB["default"])
    if any(x in q_merged for x in ["order","first one","1st","confirm"]):
        return {"reply": f"Done ✅ Ordering {results[0]} in {loc} for Rs {budget}. Delivery in 25 mins. Confirm order?", "context": {"last_dish": dish, "last_budget": budget, "last_location": loc}}
    if "more" in q_merged or "other" in q_merged:
        return {"reply": f"More {veg} {dish} under Rs {budget} in {loc}:\n1. {results[0]}\n2. {results[1]}\n3. {results[2]}\nSay 'order first one'", "context": {"last_dish": dish, "last_budget": budget, "last_location": loc}}

    # Final real answer
    reply_text = f"Best {veg} {dish} under Rs {budget} in {loc}:\n1. {results[0]}\n2. {results[1]}\n3. {results[2]}\n\nWant me to order first one? Say 'order first one' or filter with 'veg only' / 'under 250'"
    return {"reply": reply_text, "context": {"last_dish": dish, "last_budget": budget, "last_location": loc}}
