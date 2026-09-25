import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai import AzureOpenAI
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Cheddar")

WORKSPACES_DIR = Path(__file__).parent / "workspaces"
WORKSPACES_DIR.mkdir(exist_ok=True)

# session_id -> {"workspace_dir": Path}
sessions: dict[str, dict] = {}

AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21")
AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT")

client = None
if AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY:
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )


class InitializeSessionResponse(BaseModel):
    session_id: str


class SendMessageRequest(BaseModel):
    session_id: str
    message: str


def sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def stream_echo(message: str):
    for word in message.split():
        yield sse_event({"delta": word + " "})
    yield sse_event({"done": True})


def stream_openai(message: str):
    if client is None or not AZURE_OPENAI_DEPLOYMENT:
        yield sse_event({"error": "Azure OpenAI is not configured"})
        yield sse_event({"done": True})
        return

    stream = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[{"role": "user", "content": message}],
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield sse_event({"delta": delta})
    yield sse_event({"done": True})


@app.post("/initialize-session", response_model=InitializeSessionResponse)
def initialize_session():
    session_id = str(uuid.uuid4())
    workspace_dir = WORKSPACES_DIR / session_id
    workspace_dir.mkdir(parents=True, exist_ok=True)

    sessions[session_id] = {"workspace_dir": workspace_dir}

    return InitializeSessionResponse(session_id=session_id)


@app.post("/send-message")
def send_message(req: SendMessageRequest):
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Unknown session_id")

    generator = stream_openai(req.message) if client else stream_echo(req.message)

    return StreamingResponse(generator, media_type="text/event-stream")
