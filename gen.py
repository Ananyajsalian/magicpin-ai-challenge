from bet import compose
import json, os, glob

# Try to find sample contexts from judge_simulator if exists
# If not, we create 30 dummy evals from brief patterns

def load_sample_contexts():
    # Fallback: make synthetic contexts matching brief Section 6
    categories = [
        {"id":"cat_dentists","name":"Dentists","peer_stats":{"benchmark":"23% more views"}},
        {"id":"cat_restaurants","name":"Restaurants","peer_stats":{"benchmark":"31% more orders"}},
    ]
    merchants = [
        {"id":"m1","name":"SmileCare","locality":"Indiranagar","city":"Bangalore","active_offers":["Free Checkup"],"business_name":"SmileCare"},
        {"id":"m2","name":"Spice Hub","locality":"Koramangala","city":"Bangalore","active_offers":["20% Off Today"],"business_name":"Spice Hub"},
    ]
    triggers = [
        {"id":"t1","type":"profile_incomplete","summary":"Missing photos","missing_fields":"photos, timings"},
        {"id":"t2","type":"review_negative","title":"Service was slow","summary":"Customer complained about wait time"},
        {"id":"t3","type":"festival_event","title":"Diwali Rush","summary":"Diwali search up 42% in your area"},
        {"id":"t4","type":"weather_heatwave","title":"Heatwave alert","summary":"Cold drinks demand up 38%"},
        {"id":"t5","type":"silent_14d","type":"lapsed_merchant","summary":"No posts in 14 days","days_silent":14},
    ]
    customers = [
        None,
        {"id":"c1","name":"Rahul"},
    ]
    return categories, merchants, triggers, customers

cats, merchs, trigs, custs = load_sample_contexts()

with open('submission.jsonl','w', encoding='utf-8') as f:
    count = 0
    for cat in cats:
        for merch in merchs:
            for trig in trigs:
                for cust in custs:
                    if count>=30: break
                    out = compose(cat, merch, trig, cust)
                    line = {
                        "category": cat,
                        "merchant": merch,
                        "trigger": trig,
                        "customer": cust,
                        "output": out
                    }
                    f.write(json.dumps(line, ensure_ascii=False)+"\n")
                    count+=1

print(f"Generated submission.jsonl with {count} lines")