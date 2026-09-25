# Cheddar

Minimal FastAPI backend with session management and SSE-streamed messages.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in your Azure OpenAI values in .env
```

If `.env` is left unconfigured, `/send-message` falls back to echoing the input word by word.

## Run

```bash
uvicorn HOME:app --reload --host localhost --port 8000
```

## Endpoints

### `POST /initialize-session`

Creates a new session and a workspace directory at `./workspaces/<session_id>/`.

```bash
curl -X POST http://localhost:8000/initialize-session
```

Response:

```json
{ "session_id": "..." }
```

### `POST /send-message`

Streams a response back over SSE.

```bash
curl -N -X POST http://localhost:8000/send-message \
  -H "Content-Type: application/json" \
  -d '{"session_id": "...", "message": "hello"}'
```
