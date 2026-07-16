import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "https://api.siliconflow.cn/v1/chat/completions")
API_KEY = os.getenv("API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "meituan-longcat/LongCat-2.0")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}