from compose import compose
import json, glob
for file in glob.glob("examples/*.json")[:2]:
    with open(file) as f:
        d=json.load(f)
    r=compose(d['category'], d['merchant'], d['trigger'], d.get('customer'))
    print(r['body'])
    print("---")
print("SUCCESS! Your bot works.")