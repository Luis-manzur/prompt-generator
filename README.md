# Prompt Improver

Self-hosted Django service that uses a local Ollama model to rewrite prompts into
clearer, more token-efficient versions, grounded in stored per-project context.

## Features

- **Project context store** — create projects, upload `.md` files (instructions,
  domain context, constraints, style); files are versioned and stored in Postgres.
- **Prompt improvement** — POST a raw prompt and an optional project; the service
  assembles the relevant context, calls Ollama, and returns the improved prompt plus
  a before/after token delta.
- **Job history** — every improvement attempt is recorded (including failures) and
  retrievable by ID.

## Requirements

- Docker + Docker Compose (home server or any Linux/Mac machine)
- [Ollama](https://ollama.ai) running locally with at least one model pulled

## Quick start

```bash
# 1. Clone / copy the project
cd prompt-generator

# 2. Create your .env from the example
cp env.example .env
# Edit .env — set SECRET_KEY, DB_PASSWORD, OLLAMA_HOST, OLLAMA_MODEL

# 3. Start
docker compose up --build -d
```

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | yes | — | Django secret key (generate with `openssl rand -hex 32`) |
| `DB_NAME` | no | `promptdb` | Postgres database name |
| `DB_USER` | no | `promptuser` | Postgres user |
| `DB_PASSWORD` | yes | — | Postgres password |
| `DB_HOST` | no | `db` | Postgres host (use `db` inside docker-compose) |
| `DB_PORT` | no | `5432` | Postgres port |
| `OLLAMA_HOST` | yes | — | Ollama base URL, e.g. `http://host.docker.internal:11434` |
| `OLLAMA_MODEL` | yes | — | Model name, e.g. `llama3`, `mistral`, `gemma2` |
| `OLLAMA_TIMEOUT_SECONDS` | no | `60` | Request timeout before returning 503 |
| `OLLAMA_CONTEXT_LIMIT_CHARS` | no | `8000` | Max chars of project context sent per request |
| `DEBUG` | no | `false` | |
| `ALLOWED_HOSTS` | no | `*` | Comma-separated allowed hosts |

## Connecting Ollama on a home server

If Ollama runs on the **same machine as Docker**:
```
OLLAMA_HOST=http://host.docker.internal:11434
```

If Ollama runs on a **separate machine** on the LAN:
```
OLLAMA_HOST=http://192.168.1.x:11434
```

Make sure Ollama listens on all interfaces by setting `OLLAMA_HOST=0.0.0.0` in Ollama's
own environment.

## API reference

### Projects

| Method | Path | Description |
|---|---|---|
| POST | `/api/projects/` | Create project |
| GET | `/api/projects/` | List projects |
| GET | `/api/projects/{id}/` | Get project + file list |
| DELETE | `/api/projects/{id}/` | Delete project (cascades files) |
| POST | `/api/projects/{id}/files/` | Upload / upsert a `.md` file |
| GET | `/api/projects/{id}/files/` | List files |
| GET | `/api/projects/{id}/files/{fid}/` | Get file detail |
| DELETE | `/api/projects/{id}/files/{fid}/` | Delete file |

**Create project** — `POST /api/projects/`

Request: `{"name": "my-service", "description": "Backend API context"}`

Response (201): `{"id": 1, "name": "my-service", "description": "...", "files": [], ...}`

**Upload a context file** — `POST /api/projects/1/files/`

JSON body: `{"filename": "instructions.md", "content": "# Rules\n\nBe concise."}`

Or multipart: `file=@instructions.md`

Response (201 new / 200 upsert): `{"id": 1, "filename": "instructions.md", "version": 1, ...}`

Re-uploading the same filename for the same project updates content and increments `version`.

### Prompt improvement

| Method | Path | Description |
|---|---|---|
| POST | `/api/improve/` | Improve a prompt |
| GET | `/api/improve/{job_id}/` | Retrieve a past job |

**Improve a prompt** — `POST /api/improve/`

Request:
```json
{
  "prompt": "can you please explain to me how the authentication system works",
  "project_id": 1
}
```
`project_id` is optional. Omit it to improve without project context.

Response (200):
```json
{
  "job_id": 42,
  "improved_prompt": "Explain the authentication system: mechanism, token lifecycle, and failure modes.",
  "raw_tokens": 15,
  "improved_tokens": 12,
  "token_delta": -3,
  "model_used": "llama3"
}
```

`token_delta` is negative when the improved prompt is shorter (token savings).

**Ollama unavailable** — returns 503:
```json
{"error": "Ollama unavailable", "detail": "Cannot connect to Ollama at http://..."}
```

**Retrieve a past job** — `GET /api/improve/42/`

Returns the full `PromptJob` record including `raw_prompt`, `status`, `error` (on failure).

## Running tests locally

No Postgres or Ollama required — tests use SQLite in-memory and mock all Ollama calls.

```bash
pip install django djangorestframework python-decouple requests tiktoken pytest pytest-django
python3 -m pytest tests/ -v
```

Expected output: `32 passed`.

## Architecture notes

- `.md` file content stored as `TextField` in Postgres — single `pg_dump` covers everything, no volume management.
- Ollama calls are synchronous with a configurable timeout (default 60 s). Returns 503 on timeout or connection failure, 502 on malformed response.
- Token counts use `tiktoken cl100k_base` (approximate; field semantics are `approximate_tokens`).
- If a project's total context exceeds `OLLAMA_CONTEXT_LIMIT_CHARS`, oldest-updated files are dropped first with a logged warning — remaining context is still sent.
