import os
import requests

ACCOUNT_ID = "7de9757d21d3ddddb48d3a17a7fd7f7b"
AUTH_TOKEN = os.environ.get("CLOUDFLARE_AUTH_TOKEN")

prompt = "If you can read this say hello realitylens"
response = requests.post(
  f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/google/gemma-4-26b-a4b-it",
    headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
    json={
      "messages": [
        {"role": "system", "content": "You are a friendly assistant"},
        {"role": "user", "content": prompt}
      ]
    }
)
result = response.json()
print(result)