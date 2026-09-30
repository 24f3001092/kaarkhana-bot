# KaarkhanaBot — Sarvam AI Work Agent

This is an incremental upgrade of the existing KaarkhanaBot project. It keeps the existing frontend identity, GST notice workflow and PDF output, while replacing the static demo execution path with a real backend agent pipeline.

## Core pipeline

**USER → INPUT PREPROCESSOR → INPUT ANALYZER → CONTEXT → REQUIREMENTS → CLASSIFIER → MISSING-INFO CHECK → PLANNER → TOOL ROUTER → EXECUTION → VERIFICATION → FINAL RESPONSE**

The browser never receives the Sarvam API key.

## What is implemented

- Sarvam AI as a backend provider abstraction
- Current Sarvam V1 Chat Completions integration using `POST /v1/chat/completions`
- `api-subscription-key` authentication
- `sarvam-105b` configurable through environment variables
- timeout and retry handling for transient provider failures
- strict Pydantic validation of structured input analysis
- user goal / intent / sub-intents / entities / constraints / expected output
- language detection guidance for English, Hindi and Hinglish
- conversation context stored in SQLite
- file-aware metadata and extraction for PDF, DOCX, PPTX, XLSX, CSV, TXT, MD and JSON
- image metadata routing (vision execution is intentionally not faked)
- multi-intent planning
- clarification when essential information is missing
- tool routing based on the structured analysis
- concise activity summaries instead of private chain-of-thought
- source-grounded document responses
- PDF artifact generation
- honest handling of unavailable web search / sandboxed code execution
- file size/type validation
- safe filenames
- server-side secret handling
- SQLite task/message records
- automated analyzer/planner tests

## GST notice workflow

The previous GST ASMT-10 frontend result is preserved. With a real backend, the uploaded notice is extracted and passed as untrusted source content to the analyzer and finalizer. The system should summarize what the notice actually says rather than inventing tax conclusions.

## Setup

### 1. Create a virtual environment (recommended)

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS/WSL:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Configure Sarvam

Copy:

```text
backend/.env.example
```

to:

```text
.env
```

Then set:

```env
SARVAM_API_KEY=your_real_key
SARVAM_MODEL=sarvam-105b
SARVAM_BASE_URL=https://api.sarvam.ai
SARVAM_TIMEOUT_SECONDS=45
SARVAM_MAX_RETRIES=2
MAX_FILE_MB=20
DAILY_LIMIT=20
```

**Never put the key in `index.html`, `app.js`, GitHub, or any public frontend file.**

### 4. Run

From the project root:

```bash
uvicorn backend.main:app --reload --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

When configured, it should report `sarvam_configured: true`.

## Testing

Run:

```bash
pytest -q
```

The test suite covers the required intent-analysis examples, multi-intent requests, context references, clarification behavior and plan generation.

## Important tool limitations

The current upgrade does not pretend that tools are available when they are not connected.

- PDF/DOCX/PPTX/XLSX/CSV/TXT/JSON extraction: implemented
- PDF artifact generation: implemented
- Sarvam AI analysis/finalization: implemented when a key is configured
- Web research: routed and explicitly reported as unavailable until a search provider is connected
- Sandboxed code execution: routed and explicitly reported as unavailable until a secure executor is connected
- Image vision execution: image metadata is captured; a vision provider/tool must be connected before claiming visual analysis
- External actions such as sending email/publishing/purchases: not performed

## Security notes

Uploaded files are treated as untrusted data. Text inside a PDF or other external content cannot override the analyzer/system instructions.

For public production deployment, add:

- authentication and authorization
- per-user rate limits and quotas
- malware scanning
- sandboxed code execution
- object storage with access control
- CSRF/session protection where applicable
- audit logs
- abuse detection
- human confirmation for consequential actions
- production database and secret manager

## Sarvam integration

The implementation follows Sarvam's current Chat Completion API pattern: V1 uses `/v1/chat/completions`, supports `sarvam-105b`, and authenticates with the `api-subscription-key` header. Structured outputs are requested with `response_format` and then validated again with Pydantic.

See the official Sarvam API documentation for current model/API availability before deployment.
