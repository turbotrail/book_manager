# book_manager/app/services/ai_summary.py
import httpx
from app.core.config import settings

async def generate_summary(prompt: str) -> str:
    headers = {"Content-Type": "application/json"}
    body = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(settings.LLAMA_ENDPOINT, json=body)
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "").strip()
        else:
            raise Exception(f"Failed to get summary: {response.text}")