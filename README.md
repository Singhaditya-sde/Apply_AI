# ApplyAI

ApplyAI is a focused portfolio MVP for students preparing job applications. It
stores a candidate profile, parses a PDF resume, analyzes pasted job
descriptions, calculates a rule-based match score, and prepares editable
application materials.

## Workspace map

- `artifacts/applyai/` — React + TypeScript client
- `artifacts/api-server/` — Node.js + Express API
- `ai-service/` — Python + FastAPI structured AI service
- `lib/api-spec/openapi.yaml` — API contract and code-generation source

## Setup

1. Add `OPENAI_API_KEY` to Replit Secrets.
2. Copy the service examples if running outside Replit:
   - `artifacts/api-server/.env.example`
   - `ai-service/.env.example`
3. Set `MONGODB_URI` for persistence. Without it, the app uses explicit
   in-memory development storage and data resets when the API restarts.
4. Start the workflows:

```bash
python ai-service/main.py
pnpm --filter @workspace/api-server run dev
pnpm --filter @workspace/applyai run dev
```

The API is served at `/api` and the React app at `/`.

## Scope intentionally left out

This is not a full SaaS. It intentionally does not include browser
autofill, email sending, job discovery or scraping, payments, subscriptions,
multi-user dashboards, embeddings, queues, Redis, or OAuth email access.