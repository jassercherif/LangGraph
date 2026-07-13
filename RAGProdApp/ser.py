from openai import OpenAI
import os


BASE_URL = "http://localhost:12434/engines/llama.cpp/v1/"

client = OpenAI(base_url=BASE_URL, api_key="anything")

MODEL_NAME = "ai/llama3.2:latest"
PROMPT = "Explain how transformers work."

messages = [
    {"role": "system", "content": PROMPT}
]

response = client.chat.completions.create(
    model=MODEL_NAME,
    messages=messages
)

print(response.choices[0].message.content)