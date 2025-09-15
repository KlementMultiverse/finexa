import os
from dotenv import load_dotenv  # ← NEW: Load .env file
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()  # ← NEW: This loads DASHSCOPE_API_KEY into os.environ

# Get API key
api_key = os.getenv("DASHSCOPE_API_KEY")

if not api_key:
    raise ValueError("API key not found in .env — check file and key name")

# Initialize client
client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

# Test call
response = client.chat.completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "Hello, Qwen. Respond with only: 'FINEXA ONLINE'"}]
)

print(response.choices[0].message.content)
