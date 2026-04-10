from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key)
models = client.models.list()

for model in models.data:
    print(model)