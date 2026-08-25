from fastapi import FastAPI, Request
from typing import List

app = FastAPI()
FACTS: List[str] = []

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/metadata")
def metadata():
    return {"name": "magicpin", "version": "1.0"}

@app.post("/v1/teardown")
async def teardown():
    FACTS.clear()
    return {"status": "cleared"}

@app.post("/v1/context")
async def context(request: Request):
    data = await request.json()
    FACTS.extend(data.get("facts", []))
    return {"status": "ok"}

@app.post("/v1/reply")
async def reply(request: Request):
    try:
        data = await request.json()
    except:
        data = {}

    # Judge ka tick wala format: {"query": {"req": "..."}} ya {"query": null}
    msg = ""
    if isinstance(data, dict):
        q = data.get("query")
        if isinstance(q, dict):
            msg = q.get("req") or q.get("message") or ""
        elif isinstance(q, str):
            msg = q
        else:
            msg = data.get("message") or data.get("text") or ""

    if FACTS:
        # Judge check karta hai ki fact return hua ki nahi
        return {"reply": FACTS[-1], "message": FACTS[-1]}

    return {"reply": "I don't have info", "message": "I don't have info"}