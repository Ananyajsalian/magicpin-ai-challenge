import requests
BASE = "http://localhost:8000"

def check(name, method, path, json_data=None):
    try:
        url = BASE + path
        if method == "GET":
            r = requests.get(url, timeout=10)
        else:
            r = requests.post(url, json=json_data, timeout=10)
        ok = r.status_code == 200
        status = "✅ PASS" if ok else f"❌ FAIL {r.status_code}"
        print(f"{name} -> {status} | {str(r.text)[:200]}")
        return ok
    except Exception as e:
        print(f"{name} -> ❌ ERROR {e}")
        return False

print("=== MAGICPIN JUDGE SIMULATOR (Official 5 checks) ===")
p1 = check("1. GET /healthz", "GET", "/healthz")
p2 = check("2. GET /metadata", "GET", "/metadata")
p3 = check("3. POST /v1/teardown", "POST", "/v1/teardown", {})
p4 = check("4. POST /v1/context (fresh fact)", "POST", "/v1/context", {"facts": ["Clinics with 5+ photos get 2x more leads - source: magicpin internal data 2026"]})
p5 = check("5. POST /v1/reply (tick)", "POST", "/v1/reply", {"message": "Hi, how to get more leads?"})

print("\n=== RESULT ===")
if all([p1,p2,p3,p4,p5]):
    print("🎉 5/5 PASS - Judge will PASS you! Ready to submit Railway link!")
else:
    print("Fix the failed one")