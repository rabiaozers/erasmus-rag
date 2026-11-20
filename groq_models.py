"""Check the Groq key and list the models it can use: python groq_models.py"""
import requests

from rag import groq_api_key

key = groq_api_key()
print("key starts with", key[:4], "and has", len(key), "characters")
response = requests.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {key}"}, timeout=30)
if not response.ok:
    print("Groq error", response.status_code, response.text)
else:
    for model in sorted(m["id"] for m in response.json()["data"]):
        print(model)
