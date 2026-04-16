import os
import requests
from pathlib import Path
from dotenv import load_dotenv


ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"
if ROOT_ENV.exists():
  load_dotenv(ROOT_ENV)
else:
  load_dotenv()

ACCOUNT_ID = "7de9757d21d3ddddb48d3a17a7fd7f7b"
AUTH_TOKEN = os.environ.get("CLOUDFLARE_AUTH_TOKEN")

if not AUTH_TOKEN:
  raise RuntimeError("CLOUDFLARE_AUTH_TOKEN is missing. Check .env and dotenv loading.")

prompt = "if you can read this say hello realitylens"
response = requests.post(
  f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/google/gemma-4-26b-a4b-it",
    headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
    json={"prompt": prompt}
)
result = response.json()
print(result)