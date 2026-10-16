#!/usr/bin/env python3
"""One local AI smoke test; no publication or source data leaving runner."""
import json,urllib.request,time
start=time.monotonic()
schema={"type":"object","properties":{"heading":{"type":"string"},"summary":{"type":"string"},"tips":{"type":"array","items":{"type":"string"},"minItems":3,"maxItems":3}},"required":["heading","summary","tips"],"additionalProperties":False}
payload={"model":"qwen3:4b-instruct","messages":[{"role":"system","content":"You are a careful Bengali home-building educational editor. Respond only with requested JSON. Do not invent figures or project details."},{"role":"user","content":"বাংলায় বাড়িতে বৃষ্টির পানি জমা সম্পর্কে ছোট কিন্তু কার্যকর একটি শিরোনাম, সারাংশ এবং ৩টি সাধারণ নিরাপত্তা টিপস লেখো। কোনো পরিসংখ্যান বানিও না।"}],"format":schema,"stream":False,"options":{"num_predict":380,"temperature":0.25,"num_ctx":4096}}
req=urllib.request.Request("http://127.0.0.1:11434/api/chat",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req,timeout=360) as resp:
    raw=json.load(resp)
text=raw["message"]["content"]
data=json.loads(text)
assert set(data)=={"heading","summary","tips"} and len(data["tips"])==3
assert any("\u0980"<=ch<="\u09ff" for ch in data["heading"]),"No Bengali text"
print("OPEN_SOURCE_AI=OK; MODEL=qwen3:4b-instruct; SECONDS",round(time.monotonic()-start,1))
print("HEADING:",data["heading"][:160])
print("SUMMARY:",data["summary"][:220])
print("TIPS:",data["tips"])
