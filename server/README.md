# ApplyAI server

This directory represents the Node.js + Express API layer for ApplyAI.

In this workspace, the shared runnable API service is registered under
`artifacts/api-server/`. It will own authentication, profile CRUD, resume
upload and parsing proxy routes, job CRUD, application CRUD, and the thin
HTTP proxy to the FastAPI service.

The API contract will be added before implementing routes.