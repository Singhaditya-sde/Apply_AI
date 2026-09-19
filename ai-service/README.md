# ApplyAI AI service

This directory is reserved for the Python + FastAPI service used by ApplyAI.

Planned endpoints:

- `POST /parse-resume`
- `POST /parse-job`
- `POST /match`
- `POST /generate`

The service will use structured OpenAI responses and return Pydantic models.
It will not own authentication, persistence, job-board scraping, or email
sending.