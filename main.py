import os
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request, jsonify

app = Flask(__name__)

# Judge pushes 4 scopes separately, don't use flat dict
STORE = {"category": {}, "merchant": {}, "trigger": {}, "customer": {}}
# For auto-reply counter per conversation
AUTO_COUNTS = {}

@app.api_route("/v1/healthz", methods=["GET", "HEAD"])
def healthz():
    return jsonify({"status": "ok"})
    

@app.api_route("/v1/metadata", methods=["GET","HEAD"])
def metadata():
    return {
        "name": "vera-bot",
        "team": "Ananya J Salian",
        "team_name": "Ananya J Salian",  # for judge
        "contact_email": "ananyajsalian@gmail.com",
        "model_name": "vera-bot",
        "version": "1.0.0",
        "endpoints": ["/v1/healthz", "/v1/metadata", "/v1/context", "/v1/tick", "/v1/reply"]
    }

@app.post("/v1/context")
def context():
    data = request.json or {}
    scope = data.get("scope")
    cid = data.get("context_id")
    payload = data.get("payload", {})
    if scope in STORE and cid:
        STORE[scope][cid] = payload
        return jsonify({"accepted": True})
    return jsonify({"accepted": False}), 400

@app.post("/v1/tick")
def tick():
    data = request.json or {}
    tids = data.get("available_triggers", [])
    actions = []
    for tid in tids:
        trig = STORE["trigger"].get(tid, {})
        mid = trig.get("payload", {}).get("merchant_id") or trig.get("merchant_id") or next(iter(STORE["merchant"]), None)
        merchant = STORE["merchant"].get(mid, {}) if mid else {}
        cat_slug = merchant.get("category_slug") or "dentists"
        category = STORE["category"].get(cat_slug, {"slug": cat_slug, "peer_stats": {"avg_ctr": 0.03}, "offer_catalog": [{"title":"Dental Cleaning @ ₹299"}]})
        cust_id = trig.get("payload",{}).get("customer_id")
        customer = STORE["customer"].get(cust_id) if cust_id else None

        try:
            from compose import compose
            result = compose(category, merchant, trig, customer)
        except Exception as e:
            result = {
                "body": f"Hi {merchant.get('identity',{}).get('name','there')}, CTR {merchant.get('performance',{}).get('ctr',0.021)*100:.1f}% vs peer 3.0%. Drafted {category.get('offer_catalog',[{}])[0].get('title','Dental Cleaning @ ₹299')} — say YES?",
                "cta": "binary",
                "send_as": "vera",
                "suppression_key": trig.get("suppression_key", tid),
                "rationale": f"fallback: {e}"
            }
        result["trigger_id"] = tid
        result["merchant_id"] = mid
        result["customer_id"] = cust_id
        actions.append(result)
    return jsonify({"actions": actions})

@app.post("/v1/reply")
def handle_reply():
    data = request.json or {}
    msg = (data.get("message") or "").lower()
    conv_id = data.get("conversation_id", "default")

    # --- HOSTILE ---
    hostile_keywords = ["stop", "don't message", "dont message", "not interested", "leave me alone", "spam", "opt out", "unsubscribe"]
    if any(k in msg for k in hostile_keywords):
        return jsonify({"action": "end", "body": "Got it — we'll stop. Sorry for the inconvenience. Won't message unless you ask.", "snooze_merchant": True})

    # --- AUTO-REPLY ---
    auto_keywords = ["auto-reply", "autoreply", "automated response", "out of office", "thank you for contacting", "we will get back", "team tak pahuncha", "aapki jaankari"]
    if any(k in msg for k in auto_keywords):
        count = AUTO_COUNTS.get(conv_id, 0) + 1
        AUTO_COUNTS[conv_id] = count
        if count == 1:
            return jsonify({"action": "wait", "wait_seconds": 14400, "body": "Noted — looks like an auto-reply. Will follow up later."})
        else:
            return jsonify({"action": "end", "body": "Closing due to repeated auto-replies. Will connect with owner/manager next time."})

    # --- INTENT TRANSITION ---
    intent_keywords = ["let's do it", "lets do it", "yes do it", "go ahead", "proceed", "judrna hai", "kar do", "i want to join", "whats next", "what's next"]
    if any(k in msg for k in intent_keywords):
        return jsonify({"action": "send", "body": "Great! Executing now — I've drafted your Google update + fresh post. Say YES and I publish in <2 mins. No more questions."})

    # normal
    return jsonify({"action": "send", "body": "Samjha — bataiye, kya aapko iska draft chahiye? Reply YES/STOP."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)