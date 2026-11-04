# FirstWeek design

## API endpoints

| Method | Path | Purpose | Status |
|---|---|---|---|
| GET | `/` | Service name and links | live |
| GET | `/health` | Health check: status, app name, environment | live |
| POST | `/chat` | Question in, structured JSON answer out | live |
| POST | `/chat/stream` | Same as `/chat`, streamed as server-sent events | live |
| GET | `/usage` | Calls, tokens and cost per model | live |
| POST | `/ask` | Answer from retrieved FastAPI code with file and line citations | planned (Week 3) |

### POST /chat
Request: `{"question": "..."}`

Response:
```json
{
  "answer": "I don't know",
  "citations": [],
  "grounded": false,
  "model": "gemini/gemini-3.5-flash",
  "latency_ms": 3326
}
```
- `citations`: list of `{file, start_line, end_line}`. Empty until retrieval is added.
- `grounded`: false means the bot refuses with "I don't know".

### LLM reliability
Primary model first (timeout 20 s, 2 retries). If it still fails, the fallback model is tried. If both fail, the API returns 503.

## Tables

### usage_log (live)
| Column | Type | Meaning |
|---|---|---|
| id | serial, primary key | Row id |
| ts | timestamptz, default now() | When the call happened |
| model | text | Model that answered |
| input_tokens | int | Prompt tokens |
| output_tokens | int | Completion tokens |
| cost_usd | double precision | Cost of the call |
| latency_ms | int | Time taken |

Rows are also kept in memory, so `/usage` still works when no database is configured.

### documents and chunks (planned, Week 3)
- `documents`: one row per FastAPI source file (path, commit SHA).
- `chunks`: code pieces with file path, start and end line, text, and an embedding stored with pgvector. The vector size depends on the embedding model chosen in Week 3.

## Run and deploy
- Local: `uvicorn app.main:app --reload`
- Docker Compose: `api` (FastAPI) and `db` (Postgres with the pgvector image)
- CI: GitHub Actions runs tests and builds the Docker image on every push
- Hosting: free host (Render), settings come from environment variables
