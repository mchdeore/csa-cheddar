from fastapi import APIRouter
from HOME import client
import os

router = APIRouter()

@router.post("/send-message")
async def send_message(session_id: str, message: str):
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[{"role": "user", "content": message}],
        stream=True
    )
    return response
