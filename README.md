# MedicZero — ميديك زيرو

MedicZero is an Arabic-first website with a React frontend and a Python
FastAPI backend. A user describes symptoms or uploads a photo, answers follow-up
questions, and receives a preliminary urgency label, possible explanations,
first-aid steps, warning signs, and references when available. Google Gemini powers
the conversation, structured generation, and Google Search grounding.

The interface is primarily Arabic and uses a right-to-left layout. Backend replies
can be Arabic or English, depending on the conversation. Internal package names
and browser-storage keys use `medic-zero` and the `mz_` prefix.

> This is a demonstration, not a validated medical device or a substitute for
> professional care. Use synthetic examples when testing. Emergency detection and
> generated advice can be wrong; the absence of an alert does not establish safety.
> For a real emergency, contact your local emergency service. The interface displays
> a `911` button; adapt that number before using the interface elsewhere.

## Contents

- [What is implemented](#what-is-implemented)
- [Prerequisites](#prerequisites)
- [Run the website step by step](#run-the-website-step-by-step)
- [Start it again after the first setup](#start-it-again-after-the-first-setup)
- [Environment variables](#environment-variables)
- [Using the website](#using-the-website)
- [Architecture and assessment flow](#architecture-and-assessment-flow)
- [API reference](#api-reference)
- [Dependencies](#dependencies)
- [Checks and tests](#checks-and-tests)
- [Build and preview](#build-and-preview)
- [Project structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Known limitations](#known-limitations)
- [Updating your local copy](#updating-your-local-copy)

## What is implemented

| Area | Current behavior |
| --- | --- |
| Accounts | Demo sign-up and login stored in the browser, without server authentication. |
| Profile | Manually entered age, conditions, medications, allergies, and other UI fields. Only a subset is forwarded to the backend. |
| Assessments | Symptom text, optional photo, backend follow-up questions, and a preliminary result. |
| Urgency | Five backend labels mapped to the risk meter and care direction. |
| Images | Browser compression and observations of visible external findings. Only the first selected photo is currently sent to the API. |
| References | Search-supported general information when available, plus predefined references for built-in demo rules. |
| History | Assessment records saved in that browser's `localStorage`. |
| Profile-file upload | Remote extraction is not implemented. The mock extractor returns sample data rather than reading the file. |

### Technology stack

| Layer | Technologies |
| --- | --- |
| Frontend | React 19, Vite 8, React Router 7, Tailwind CSS 4 |
| Backend | Python, FastAPI, Google `google-genai` SDK (Gemini), Pydantic |
| AI | Google Gemini with Google Search grounding |

There is no database, Docker requirement, or separate authentication server to
install. You need **two running processes**: the backend API and the frontend
website. The AI also requires internet access and a configured Gemini API project.

## Prerequisites

| Requirement | Version or condition | Purpose |
| --- | --- | --- |
| Git | A recent version | Download and update the repository. |
| Python | Python 3.13 is the tested setup | Create an environment and run the backend. |
| Node.js | Node 24.12.0 was tested; supported range: `^20.19.0 \|\| >=22.12.0` | Run npm and Vite. Node 18 and Node 21 do not satisfy this range. |
| npm | Included with Node.js; npm 11.6.2 was tested | Install the frontend dependency tree. |
| Browser | A modern browser with JavaScript and local storage enabled | Use the website. |
| Gemini API key | A valid key with access and quota for the configured model | Run real symptom assessments. |

The pinned Python packages declare Python 3.10 or newer, but the clean-install
checks for this repository use Python 3.13. Other Python versions and operating
systems have not been validated by those checks.

Download [Git](https://git-scm.com/downloads), [Python](https://www.python.org/downloads/),
and [Node.js](https://nodejs.org/en/download). On Windows, enable Python's **Add
Python to PATH** installer option. Open a new terminal after installing tools.
The Node requirement matches the locked dependencies and the
[Vite setup guide](https://vite.dev/guide/).

Verify installations in PowerShell:

```powershell
git --version
python --version
node --version
npm.cmd --version
```

On macOS/Linux, use `python3 --version` and `npm --version`. In Windows PowerShell,
this guide uses `npm.cmd` to avoid an execution-policy error with the `npm.ps1`
wrapper. You do not need to change that policy.

## Run the website step by step

Follow these steps in order for the first installation. Each command block states
which folder to use. Keep both server terminals open once the website is running.

### Step 1: Download the project

Open a terminal in the directory where you want to store the project:

```powershell
git clone https://github.com/mohammadsammour/medical-assistant.git
cd medical-assistant
```

If you already downloaded or opened it in your IDE, use that existing folder; do
not clone it again. Its local name may be `Medical-Python`. The **project root**
is the folder containing this README and the `backend` and `frontend` directories.

### Step 2: Create the backend environment — Terminal 1

From the project root, on Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS/Linux:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

`.venv` contains this project's Python interpreter and installed packages. The
commands call it directly, so environment activation is optional. Do not install
the packages into an unrelated project's environment.

pip installs the six direct dependencies and their transitive dependencies.
Do not separately install `google-generativeai`: the code uses `google-genai`.
Pillow, a database driver, and `python-multipart` are not required by the current
backend; images are received as base64 inside JSON.

### Step 3: Configure Gemini — Terminal 1

Still in `backend`, create `.env` only if it does not exist. On PowerShell:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

On macOS/Linux:

```bash
[ -f .env ] || cp .env.example .env
```

Create or obtain a key in [Google AI Studio](https://aistudio.google.com/apikey).
Open `backend/.env` and replace the placeholder with your own key:

```env
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_MODEL=gemini-3.8-flash
```

Do not leave `your_actual_gemini_api_key` as the value. Keep the key in
`backend/.env`; never put it in a frontend file or a `VITE_` variable. Real `.env`
files are Git-ignored, while `.env.example` templates are committed.

The template model is listed in Google's [model documentation](https://ai.google.dev/gemini-api/docs/models).
Access, quota, billing, and availability depend on your API project. The code uses
structured JSON, images, Google Search, and `thinking_level="low"`. If you change
models, check support for the options in `backend/main.py`. A successful package
installation does not prove that the configured key can access the model.

### Step 4: Start the backend — Terminal 1

From `backend`, on PowerShell:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

On macOS/Linux:

```bash
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Wait for the startup message, leave the terminal open, and check:

- [Health](http://127.0.0.1:8000/health): returns `{"status":"ok"}`.
- [Swagger UI](http://127.0.0.1:8000/docs): interactive API documentation.
- [OpenAPI schema](http://127.0.0.1:8000/openapi.json): request and response models.

**Health checks the web server only.** It does not validate Gemini credentials,
model access, quota, or connectivity. Step 8 tests the AI connection.

For development, append `--reload` to the server command if desired. Reloading
restarts the backend and clears conversation memory. Use one worker and omit
`--reload` for a stable demo.

### Step 5: Install the frontend — Terminal 2

Open a **second terminal at the project root**, not inside `backend`. On PowerShell:

```powershell
cd frontend
npm.cmd ci
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

On macOS/Linux:

```bash
cd frontend
npm ci
[ -f .env ] || cp .env.example .env
```

`npm ci` installs the versions in `package-lock.json` and recreates `node_modules`.
The manifest and lockfile must match. Use `npm ci` for a fresh installation or a
changed lockfile; use `npm install` when intentionally adding/updating packages.

### Step 6: Configure the frontend — Terminal 2

Open `frontend/.env` and check:

```env
VITE_AI_MODE=remote
VITE_AI_SERVICE_URL=http://127.0.0.1:8000
```

The URL points to the backend, not the frontend port. If an existing `.env` uses
`localhost`, update it to match the addresses above. The guarded copy commands
preserve existing files and do not automatically update old values.

Symptom assessments **always use the backend**, including when `VITE_AI_MODE=mock`.
That variable currently controls profile-file extraction only; it does not enable
a complete offline assessment mode.

### Step 7: Start the frontend — Terminal 2

From `frontend`, on PowerShell:

```powershell
npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

On macOS/Linux:

```bash
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). Keep both terminals running.
`--strictPort` reports a busy port explicitly rather than silently selecting another.

### Step 8: Test the complete website

1. Open the website and go to login.
2. On a fresh browser origin, the app seeds a demo account if there are no saved
   users. Use phone **`0790000000`**, password **`123456`**, or create a demo account.
3. Review the medical profile. The seeded account has synthetic conditions and
   medications that can influence the response. Enter suitable synthetic data
   for your test.
4. Start an assessment with a synthetic description, for example:
   `I have had a mild headache since this morning.`
5. Wait for a question, answer the actual question shown, and continue until a
   result or emergency alert appears. Do not assume fixed wording or a fixed label.
6. Open history to confirm that the assessment was saved in your browser.

A successful question or result confirms the main Gemini request succeeded and
the browser reached the backend. Search references may still be unavailable
independently. This is a connection test, not a clinical accuracy test.

If it fails, inspect `/ai/chat` in the browser's **Network** tab, including its
HTTP status and JSON `detail`, and check Terminal 1. See [Troubleshooting](#troubleshooting).

### Step 9: Stop the servers

Press **Ctrl+C** in each terminal. Packages and configuration stay on disk, and
history stays in local storage. Backend conversation memory is cleared when the
process stops; start a new assessment after restarting it.

## Start it again after the first setup

Do not recreate environments, reinstall packages, or copy `.env` files every time.
Open two terminals at the project root.

**Terminal 1**, PowerShell:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

**Terminal 2**, PowerShell:

```powershell
cd frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

On macOS/Linux, use `.venv/bin/python` and `npm`. Open
[http://127.0.0.1:5173](http://127.0.0.1:5173) and start a fresh conversation.

## Environment variables

| File | Variable | Example/default | Meaning |
| --- | --- | --- | --- |
| `backend/.env` | `GEMINI_API_KEY` | Your own key | Required for AI requests; the repository supplies no key. |
| `backend/.env` | `GEMINI_MODEL` | `gemini-3.8-flash` | Used for conversation, search, classification, and open guidance. |
| `frontend/.env` | `VITE_AI_SERVICE_URL` | Template: `http://127.0.0.1:8000` | API base URL; if unset, the adapter code defaults to `http://localhost:8000`. |
| `frontend/.env` | `VITE_AI_MODE` | `remote` | Controls profile extraction only: remote returns no extraction; other values use a sample-data mock. |

The backend loads `.env` using `python-dotenv`; variables already set in the shell
take precedence. Run from `backend` and restart after configuration changes.

Vite reads frontend variables at startup and embeds `VITE_` values in the browser
bundle. Restart Vite after changes, or rebuild if using `dist`. All `VITE_` values
are browser-visible and must not contain secrets.

## Using the website

| Route | Purpose | Login required? |
| --- | --- | --- |
| `/` | Home and entry points | No |
| `/login` | Browser-local demo login | No |
| `/signup` | Multi-step account and profile form | No |
| `/assess/new` | Start with text, a photo, or image-only input | Yes |
| `/assess/:id` | Questions and saved result | Yes |
| `/profile` | Edit the local medical profile | Yes |
| `/history` | Saved assessments for the current user | Yes |
| `/emergency` | Static emergency information | No |

Signup steps are within `/signup`, not separate `/signup/health` or `/signup/review`
routes. Remote profile-file extraction is unimplemented; enter details manually.
Mock extraction supplies fixed sample data rather than interpreting the file.

The browser compresses selected photos to JPEG with a maximum longest side of
1024 pixels and quality `0.7`. The UI accepts up to three selections, but the
adapter sends **only the first** with the first message. Do not assume the others
were analyzed. Ordinary photos of visible external findings are the intended
input, rather than X-rays, scans, laboratory reports, or unrelated images.

## Architecture and assessment flow

```text
React views --> controllers --> models --> browser localStorage
                    |
                    v
               remoteAi.js
                    | POST /ai/chat (JSON)
                    v
             FastAPI: main.py
                    +-- In-memory conversation sessions
                    +-- Gemini conversation and photo observations
                    +-- Optional Google Search grounding
                    +-- Demo-rule classification / generated open guidance
                    |
                    v
             Urgency + assessment + sources
                    |
                    v
             UI question, result, or emergency screen
```

### Frontend layers

- `pages/` and `components/` render the interface.
- `controllers/` manages login state, profiles, and assessment actions.
- `models/` reads/writes local accounts, profiles, and assessment records.
- `remoteAi.js` maps UI inputs to the backend schema and backend output to UI shapes.
- `services/ai/index.js` always selects remote symptom assessment. The old mock
  assessment code remains in the repo but is not selected by that adapter.

### Conversation stages

1. The adapter creates an in-memory backend session ID for a new UI assessment.
2. The first message sends text, mapped profile data, and the first photo when
   present. Image-only input uses a short default message.
3. The backend passes stored history and the current profile to Gemini. Replies
   marked as follow-up questions increase the backend counter.
4. The maximum is five follow-up questions. After the fifth is answered, the
   backend requests a summary. A model emergency alert can end questioning early.
5. Search is attempted during later follow-ups and at summaries, except the early
   emergency path. Search failure can leave references unavailable without
   preventing the main conversation from succeeding.
6. At a summary, limited demo rules cover headache, cold-like symptoms, and itchy
   skin. The backend checks evidence quotes and additional conditions for labels.
7. Non-emergency rule results may use generated first-aid steps. Missing/incomplete
   steps fall back to predefined actions. Emergency actions stay predefined.
8. Unknown or rejected decisions can use a separate open-guidance model call with
   its own urgency and generated steps. If it fails, generic
   `unable_to_determine` guidance is returned.
9. The adapter maps the response to the UI and the controller saves it locally.

The separate open-guidance path does not inherit every rule-classifier check.
Generated wording has empty `source_ids`: individual claims were not verified
against linked sources. Search-supported educational information is separate.
NHS, MedlinePlus, and WHO are preferences, not an enforced search-domain allowlist.

### Urgency mapping

| Backend label | UI risk | UI care direction |
| --- | --- | --- |
| `emergency` | `EMERGENCY` | `EMERGENCY` |
| `urgent_medical_attention` | `HIGH` | `URGENT_CARE_NOW` |
| `routine_consultation` | `MEDIUM` | `SEE_DOCTOR_24H` |
| `potentially_self_care` | `LOW` | `SELF_CARE` |
| `unable_to_determine` | `MEDIUM` | `SEE_DOCTOR_24H` |

`SEE_DOCTOR_24H` is an existing UI enum, not an independently validated 24-hour
recommendation. `unable_to_determine` expresses uncertainty. Adapter confidence
values are placeholders, not calibrated clinical probabilities.

### Data storage and session behavior

| Location | Content | Lifetime |
| --- | --- | --- |
| Browser `mz_users` | Demo accounts, including plain-text passwords | Browser-local until removed. |
| Browser `mz_session` | Local signed-in user ID | Until logout/reset. |
| Browser `mz_profiles` | Profiles | Browser-local until removed. |
| Browser `mz_assessments` | Questions, answers, images, results | Browser-local; the controller removes images when an assessment completes. |
| Adapter memory | Assessment ID to backend session ID mapping | Lost on page reload. |
| Backend memory | History, profile, question count, image bytes, session lock | Lost on restart; not shared across workers. |

The adapter sends age, condition labels, medication names, allergies, and an empty
`medical_history` list. Gender, weight, blood type, pregnancy, emergency contact,
and medication doses are not forwarded as dedicated profile fields.

Use one backend worker. Refreshing a page or restarting the backend can disconnect
an in-progress assessment from its conversation; previous turns are not replayed.
The UI Back action changes locally saved assessment turns but does not undo messages already
stored in the backend. Start a fresh assessment when you need a clean conversation.

## API reference

[Swagger](http://127.0.0.1:8000/docs) and
[OpenAPI](http://127.0.0.1:8000/openapi.json) describe the running code's schemas.
[backend/README.md](backend/README.md) contains additional examples.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Returns `{"status":"ok"}` without calling Gemini. |
| `POST` | `/ai/chat` | Submit one message in a conversation. |
| `GET` | `/docs` | Interactive API documentation. |
| `GET` | `/redoc` | Alternate generated documentation. |
| `GET` | `/openapi.json` | Machine-readable schema. |

`/v1/assess/step` and `/v1/profile/extract` are not current backend endpoints.

### Chat request

```json
{
  "session_id": "readme-demo-1",
  "message": "I have had a mild headache since this morning.",
  "medical_profile": {
    "age": 25,
    "chronic_conditions": [],
    "medications": [],
    "allergies": [],
    "medical_history": []
  }
}
```

| Field | Validation/behavior |
| --- | --- |
| `session_id` | Required non-empty string, at most 128 characters. Reuse per conversation; change it for a new conversation. |
| `message` | Required non-empty trimmed string, at most 6000 characters. |
| `medical_profile` | Optional object. Omitted/null remembers the existing profile; a supplied object replaces it. |
| `medical_profile.age` | Optional strict integer from 0 to 130, or null. |
| Profile lists | `chronic_conditions`, `medications`, `allergies`, `medical_history`: lists of non-empty strings or null. Extra profile fields are rejected. |
| `image` | Optional `mime_type` (`image/jpeg` or `image/png`) plus `base64_data`: raw base64 without a `data:` prefix. |

An omitted/null field within a new profile means unknown; `[]` reports no entries.
Direct API clients can supply new profiles or images on later messages too.
Images must be non-empty, have a matching JPEG/PNG signature, and decode to at
most 2 MiB each. Stored images have an 8 MiB per-session limit. Signature checking
is not full image decoding.

### Question response

Illustrative shape; the model's actual wording varies:

```json
{
  "session_id": "readme-demo-1",
  "status": "question",
  "message": "Did the headache start suddenly or gradually?",
  "followup_count": 1,
  "max_followups": 5,
  "urgency": "unable_to_determine",
  "assessment": null,
  "sources": [],
  "medical_information": [],
  "search_status": "not_requested",
  "search_suggestions_html": null,
  "image_observations": null
}
```

When `status` is `assessment`, the assessment object includes:

| Field | Content |
| --- | --- |
| `symptom_summary` | Reported symptom summary or open-guidance condition summary. |
| `recommended_action` | Overall next-step text. |
| `classification_reason`, `rule_id` | Explanation and classification/guidance identifier. |
| `actions_now` | Objects with `instruction` and `source_ids`. |
| `seek_help_if` | Objects with `warning_sign` and `source_ids`. |
| `possible_explanations` | Unconfirmed explanations with `text` and `source_ids`. |
| `possible_causes`, `warning_signs` | Plain-text lists for client compatibility. |
| `medical_information` | Search-supported text with source IDs. |
| `limitations` | Assessment and generation caveats. |

Top-level source entries have `id`, `title`, and `url`. `search_status` is
`not_requested`, `grounded`, or `unavailable`. Photo observations contain a status
(`observed`, `unclear`, `unsupported`), observations, and a limitation.
`search_suggestions_html` contains provider search-display content when available;
the current frontend does not render that field.

### Call the API directly

In a separate PowerShell terminal while the backend is running:

```powershell
$chatBody = @{
    session_id = 'readme-demo-1'
    message = 'I have had a mild headache since this morning.'
} | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/ai/chat -Method Post -ContentType 'application/json' -Body $chatBody
```

On macOS/Linux:

```bash
curl -X POST http://127.0.0.1:8000/ai/chat \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"readme-demo-1","message":"I have had a mild headache since this morning."}'
```

Continue with the same ID and an answer to the actual question. Use a new ID to
restart the example. These requests use your Gemini project's quota.

## Dependencies

Python and JavaScript dependencies are installed separately. `requirements.txt`
does not install frontend libraries, and npm does not install Python libraries.

### Backend: `backend/requirements.txt`

| Package | Pinned version | Purpose |
| --- | --- | --- |
| `fastapi` | `0.143.0` | API routes, schema validation integration, docs, CORS. |
| `uvicorn` | `0.54.0` | Serve the FastAPI app. |
| `python-dotenv` | `1.2.4` | Load backend configuration. |
| `httpx` | `0.28.1` | Provider HTTP errors/client dependency and mocked API tests. |
| `google-genai` | `2.29.0` | Gemini client, schemas, images, search, thinking/retry options. |
| `pydantic` | `2.14.0` | Request, provider-response, and result validation. |

The direct versions are pinned to the tested environment instead of the old broad
lower bounds. This avoids silently selecting new major SDK versions or accepting
very old releases that may lack configuration fields used here. Google's
[SDK repository](https://github.com/googleapis/python-genai) documents upcoming
breaking changes and recommends constraining its major version. Transitive
dependencies are resolved by pip; this is not a full transitive lockfile.

`base64`, `json`, `threading`, `time`, and `unittest` are part of Python's standard
library and do not need separate installation.

### Frontend: `package.json` and `package-lock.json`

| Packages | Purpose |
| --- | --- |
| `react`, `react-dom` | Components and browser rendering. |
| `react-router-dom` | Navigation and local route guards. |
| `lucide-react` | Icons. |
| `vite`, `@vitejs/plugin-react` | Development server and build pipeline. |
| `tailwindcss`, `@tailwindcss/vite` | Styling and build integration. |
| `@types/react`, `@types/react-dom` | Editor/tooling type metadata. |
| `oxlint` | Lint checks. |

The existing package versions support the build and have been retained. The
manifest and lockfile declare Node `^20.19.0 || >=22.12.0`. npm generally warns
about an unsupported engine; the declaration does not mean every future Node
version has been tested. Use the supported range and committed lockfile.

## Checks and tests

### Backend

From `backend`, on PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "import main; print('Backend imports successfully')"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On macOS/Linux, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.
`pip check` verifies installed dependency compatibility; importing `main` verifies
module loading without calling Gemini.

The current suite has 11 tests in `tests/test_generated_first_aid.py`, using mocked
provider calls. It checks generated steps, language prompts, trimming/duplicates,
fallbacks, emergency paths, rejected decisions, profile guards, and the API shape.
It requires no live key and does not establish clinical accuracy or provider access.

### Frontend

From `frontend`, on PowerShell:

```powershell
npm.cmd run lint
npm.cmd run build
```

On macOS/Linux, use `npm`. There is no `npm test` script. Oxlint currently reports
existing source warnings, even when it exits successfully. The build creates `dist`.

## Build and preview

From `frontend`, on PowerShell:

```powershell
npm.cmd run build
npm.cmd run preview -- --host 127.0.0.1 --port 4173 --strictPort
```

On macOS/Linux, use `npm`. Open [http://127.0.0.1:4173](http://127.0.0.1:4173) and
keep the backend running on port 8000. This previews the built frontend locally;
it does not package Python or the API key, and is not a production hosting setup.

The API URL is embedded at build time. Set it before building for a new environment.
A hosted frontend needs a reachable backend URL: a visitor's `127.0.0.1` refers to
their own computer. A static host must rewrite application routes to `index.html`.
A real deployment also needs HTTPS, server authentication, proper data storage,
restricted CORS, request controls, and review of the limitations below. There is
no complete production deployment configuration in this repository.

## Project structure

```text
medical-assistant/
├── README.md                         # Current behavior and full setup
├── ARCHITECTURE.md                   # Historical frontend/mock design
├── docs/AI_CONTRACT.md               # Historical proposed service contract
├── backend/
│   ├── main.py                       # FastAPI, Gemini, rules, sessions
│   ├── requirements.txt              # Pinned direct dependencies
│   ├── .env.example                  # Backend configuration template
│   ├── README.md                     # More backend examples
│   └── tests/test_generated_first_aid.py
└── frontend/
    ├── package.json                  # Packages, engines, npm scripts
    ├── package-lock.json             # npm dependency lockfile
    ├── .env.example                  # Public frontend configuration
    ├── index.html                    # HTML entry point
    ├── vite.config.js                # React and Tailwind plugins
    ├── public/                       # Static assets
    └── src/
        ├── App.jsx                   # Routes and layout
        ├── main.jsx                  # Render and seed local demo data
        ├── index.css                 # Styling
        ├── pages/                    # Home, login, profile, assessment, history
        ├── components/               # Reusable controls and results
        ├── controllers/              # Hooks and auth context
        ├── models/                   # localStorage access
        ├── data/                     # Demo/fallback content
        └── services/
            ├── imageUtils.js         # Photo compression
            ├── safetyNet.js          # Legacy helper; unused by current assessments
            └── ai/
                ├── index.js          # Remote assessment/extraction selection
                ├── remoteAi.js       # /ai/chat client and mapping
                ├── mockAi.js         # Old mock assessment/sample extraction
                └── mockData.js       # Sample responses
```

`.venv`, `node_modules`, `dist`, Python caches, and real `.env` files are Git-ignored.
[ARCHITECTURE.md](ARCHITECTURE.md) and [docs/AI_CONTRACT.md](docs/AI_CONTRACT.md)
describe the original mock design and contain planned behavior that differs from
the current code. Their notices point to the current documentation.

## Troubleshooting

| Problem | Check or fix |
| --- | --- |
| `python` not found or Microsoft Store opens | Install Python, enable PATH, reopen the terminal. On Windows try `py -3.13 -m venv .venv`; on macOS/Linux use `python3`. |
| `No module named ...` | Install requirements and launch Uvicorn using the same `.venv` interpreter. |
| `Could not import module "main"` | Run the server command from `backend`, where `main.py` lives. |
| pip cannot find a pinned package or cannot connect | Check internet, custom package indexes/proxies, and Python version. Use the tested Python 3.13 setup and current pip before changing package pins. |
| `uv sync` says no project exists | This repo has no `pyproject.toml`; use the documented venv/pip steps. |
| `npm` not found | Install Node.js and reopen the terminal. |
| PowerShell blocks `npm.ps1` | Use `npm.cmd`. |
| `EBADENGINE` or Vite rejects Node | Use a version satisfying `^20.19.0 \|\| >=22.12.0`; Node 24.12.0 was tested. |
| `npm ci` says the lockfile does not match | Restore matching files from the same commit. For intentional package changes run `npm install` and review the changed lockfile. |
| Port already in use | Stop the earlier server with Ctrl+C or choose another port and update URLs. Identify a process before stopping it. |
| Website opens but API calls fail to connect | Check `/health`, both terminals, and the service URL. Restart Vite after changing `.env`. |
| Health works but chat returns `503` | Read JSON `detail`: missing/invalid key, bad configuration/model access, and quota/rate-limit errors can return 503. Health does not test Gemini. |
| Chat returns `502` | Provider failure or incomplete/invalid structured output. Check response detail and provider access, then retry. |
| Chat returns `504` | Provider request timed out; check connectivity and provider availability. |
| Chat returns `422` | Read validation details. Check strings, integer age, profile lists, and raw base64 with a matching JPEG/PNG MIME type. |
| Chat returns `413` | Stored session photos exceed 8 MiB; start a new session. Individual photos over 2 MiB fail validation with 422. |
| Long pending request or failure after waiting | Browser attempts have a 30-second timeout and up to three retries. Backend retries plus search/classification can exceed that window. Inspect Network/logs; a browser timeout does not necessarily cancel backend work. |
| Config/code changes not visible | Restart the relevant server; rebuild the frontend preview. Backend restart clears active conversations. |
| Login/profile/history disappeared | `localhost`, `127.0.0.1`, and different ports have separate browser storage. Use the same origin consistently. |
| Demo account unavailable | It is seeded only when there are no saved users. Create an account or reset the local demo data if you accept losing it. |
| Refresh breaks an active assessment | Adapter session mapping is memory-only and old turns are not replayed. Start a new assessment. |
| Storage quota/JSON parsing error | Large unfinished/emergency records can retain images; corrupted local data can also break parsing. Preserve needed data before resetting the project's storage. |
| Profile upload produces no extracted data | Remote extraction is not implemented. Enter fields manually; mock mode supplies fixed sample data. |
| Search references are empty | Search can fail or yield no citation-supported passages. Missing references do not establish safety or verify generated advice. |

### Reset browser-local demo data

This removes local users, profiles, sessions, and history **for the current browser
origin**. Preserve any records you need first. Run in the browser developer console:

```javascript
['mz_users', 'mz_session', 'mz_profiles', 'mz_assessments'].forEach((key) => {
  localStorage.removeItem(key);
});
location.reload();
```

The app then seeds a fresh demo account. This does not clear backend sessions;
restarting the backend clears those.

## Known limitations

- Emergency detection, classifications, and generated advice are not clinically
  validated. The current controller does not run the legacy keyword safety net.
- Five questions are a demo limit, not evidence of a complete assessment. Prompts
  request non-repetition but there is no semantic duplicate-question checker.
- Generated actions/open guidance are not individually source-verified. Search
  results do not validate a patient diagnosis, and domain preferences are not strict.
- Confidence numbers, risk mappings, and profile-factor text are adapter output,
  not independently validated clinical measurements.
- Demo passwords are plain text in local storage. Route guards do not authenticate
  API calls. The backend has no user authentication, ownership checks, persistent
  storage, session expiry, or rate limits, and currently allows all CORS origins.
  Use synthetic data, not real credentials or patient records.
- Browser-origin changes, reloads, the UI Back action, backend restarts, and multiple
  workers can disrupt conversation state.
- Completed assessments remove their local photos; failed/emergency records can
  retain them. The backend session dictionary has no cleanup policy.
- Only the first selected photo is forwarded. Some profile fields are omitted,
  and remote document extraction is not implemented.
- Retries can repeat a request that was still executing after a browser timeout.
  There is no request idempotency mechanism.
- Mocked tests and build checks establish software wiring, not live Gemini access,
  medical correctness, or production readiness.

## Updating your local copy

Preserve your local edits before pulling changes:

```powershell
git status
git pull --ff-only
```

If Python requirements changed, from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

If the frontend manifest/lockfile changed, from `frontend`:

```powershell
npm.cmd ci
```

On macOS/Linux use `.venv/bin/python` and `npm`. Review updated templates and edit
your `.env` files manually instead of overwriting the key with a template. Restart
both servers and start a new assessment.
