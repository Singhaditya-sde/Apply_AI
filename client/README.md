# ApplyAI client

This directory represents the React + TypeScript client layer for ApplyAI.

In this workspace, the runnable client is registered as the `ApplyAI` web
artifact under `artifacts/applyai/`. Keeping the client as its own product
boundary lets the frontend be previewed independently while the requested
`client/` structure remains explicit.

Planned pages:

- Login and Register
- Profile
- Resume Upload
- Job Analyzer
- Applications Dashboard