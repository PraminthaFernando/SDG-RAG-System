import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

JUDGE_MODELS = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "qwen/qwen3-32b"
]

MAX_ROUNDS = 3
TEMPERATURES = [0.0, 0.2, 0.4]