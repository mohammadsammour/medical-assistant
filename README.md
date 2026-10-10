# 🩺 MedicZero — AI First-Aid Triage Assistant

**MedicZero** is a bilingual (Arabic / English) web app that gives people an instant, preliminary first-aid assessment. A user describes a symptom in plain language — or uploads a photo of an injury — and the app asks a few smart follow-up questions, then returns an **urgency level**, **probable causes**, **specific step-by-step first-aid instructions**, **red-flag warning signs**, and **web-sourced medical references**. It is powered by Google **Gemini** with built-in Google Search grounding.

> ⚠️ **Medical disclaimer:** This is a hackathon proof-of-concept for demonstration only. It is **not** a validated medical device and **not** a substitute for professional care. In a real emergency, call **911** (or your local emergency number).

---

## ✨ Why it stands out

- 🗣️ **Conversational triage** — natural back-and-forth in Arabic *or* English (auto-detected), with full session memory so it never re-asks what you already answered.
- 📸 **Image understanding** — upload a photo of a wound/rash and the model factors visual observations into its assessment.
- 🧬 **Personalized to the patient** — chronic conditions, medications, and allergies from the medical profile shape the questions and the advice (e.g. blood thinners affect bleeding guidance).
- 🚑 **Instant emergency path** — life-threatening descriptions immediately trigger an emergency screen instead of continuing routine questions.
- 🧠 **Guidance for *any* injury** — beyond a small set of built-in rules, the backend generates tailored probable causes + first-aid steps for conditions it hasn't seen before.
- 🔎 **Grounded, cited information** — pulls general medical info from trusted sources (NHS, MedlinePlus, WHO) via Gemini's Google Search tool, with clickable citations.
- 🎯 **Five escalating urgency levels** — from `potentially_self_care` all the way to `emergency`.

---

## 🧭 How it works

```
 User (React / Vite, RTL Arabic UI)
   │   POST /ai/chat  { session_id, message, medical_profile?, image? }
   ▼
 remoteAi.js  ──────────── translation layer (frontend format ⇄ backend format)
   │
   ▼
 FastAPI backend (backend/main.py)
   ├─ Per-session conversation memory
   ├─ Gemini: up to 5 follow-up questions, then a structured assessment
   ├─ Optional injury-photo analysis
   ├─ Google Search grounding → medical info + cited sources
   ├─ Built-in demo rules + immediate emergency path
   └─ AI-generated probable causes + first-aid steps for anything else
   │   ← { urgency, assessment, sources, medical_information }
   ▼
 Result screen: risk meter, care direction, first-aid steps,
                warning signs, and sources.
```

**Urgency scale:** `emergency` → `urgent_medical_attention` → `routine_consultation` → `potentially_self_care` → `unable_to_determine`

---

## 🛠️ Tech stack

| Layer | Technologies |
|-------|--------------|
| **Frontend** | React 19, Vite 8, React Router 7, Tailwind CSS 4|
| **Backend** | Python, FastAPI, Google `google-genai` SDK (Gemini), Pydantic |
| **AI** | Google Gemini with Google Search grounding |

---

## 🚀 Download & run it on your machine

The project has **two parts that must run at the same time**: the **backend** (API, port `8000`) and the **frontend** (web UI, port `5173`). Open **two terminal windows** — one for each.

### 0) Install the prerequisites

Before anything, install these on your computer:

| Tool | Version | Download |
|------|---------|----------|
| **Git** | any recent | <https://git-scm.com/downloads> |
| **Python** | 3.11 or newer | <https://www.python.org/downloads/> (on Windows, tick **“Add Python to PATH”** in the installer) |
| **Node.js + npm** | 18 or newer | <https://nodejs.org/> (LTS) |
| **Gemini API key** | free | Create one at <https://aistudio.google.com/apikey> |

Verify the tools are installed (any terminal / PowerShell):

```bash
git --version
python --version
node --version
npm --version
```

### 1) Clone the repository

```bash
git clone https://github.com/mohammadsammour/medical-assistant.git
cd medical-assistant
```

### 2) Start the backend (Terminal #1)

```bash
cd backend

# Install the Python dependencies
python -m pip install -r requirements.txt

# Create your environment file from the template
#   Windows (PowerShell):
copy .env.example .env
#   macOS / Linux:
#   cp .env.example .env
```

Open `backend/.env` in a text editor and paste your Gemini key:

```env
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-3.8-flash
```

Then run the server:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

✅ **Check it works:** open <http://127.0.0.1:8000/health> — you should see `{"status":"ok"}`.
📖 Interactive API docs (Swagger): <http://127.0.0.1:8000/docs>.

> Keep this terminal open while using the app. Avoid `--reload` during a live demo — it can occasionally reload stale code.

### 3) Start the frontend (Terminal #2)

Open a **second** terminal in the project root:

```bash
cd frontend

# Install the Node dependencies
npm install

# Create the frontend environment file from the template
#   Windows (PowerShell):
copy .env.example .env
#   macOS / Linux:
#   cp .env.example .env

# Start the dev server
npm run dev
```

Open the URL it prints (usually <http://localhost:5173>) in your browser. Done — describe a symptom and try it out. 🎉

---

## 🔑 Environment variables

**`backend/.env`** (secret — never commit this):
```env
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-3.8-flash
```

**`frontend/.env`**:
```env
VITE_AI_MODE=remote
VITE_AI_SERVICE_URL=http://localhost:8000
```

> The API key stays on the server and is **never** sent to the browser. `.env` files are git-ignored; use the committed `.env.example` files as templates.

---

## 🔌 API reference

**`POST /ai/chat`** — send one message in an ongoing session.

Request:
```json
{
  "session_id": "demo123",
  "message": "I cut my hand with a knife and it's bleeding a little",
  "medical_profile": { "age": 25, "chronic_conditions": [], "medications": [], "allergies": [] },
  "image": { "mime_type": "image/jpeg", "base64_data": "..." }
}
```
`medical_profile` and `image` are optional and only needed on the first message of a session.

Response (shape; wording is model-generated):
```json
{
  "session_id": "demo123",
  "status": "question",
  "message": "Did the bleeding stop after applying gentle pressure?",
  "followup_count": 1,
  "max_followups": 5,
  "urgency": "unable_to_determine",
  "assessment": null,
  "sources": []
}
```
When `status` becomes `"assessment"`, the `assessment` object contains the summary, probable causes, first-aid actions, and warning signs.

---

## 🧪 Try these demo scenarios

| Type this | What happens |
|-----------|--------------|
| `I've had a headache since this morning` | Follow-up questions → self-care / routine assessment |
| `وقعت وجرحت ايدي بسكين وفي دم بسيط` | Identifies a minor laceration → concrete first-aid steps (clean, dress) + when to seek care |
| A description of chest pain / difficulty breathing | Immediately triggers the **emergency** screen |

---

## 🗂️ Project structure

```
medical-assistant/
├─ README.md             ← this file
├─ ARCHITECTURE.md       ← deeper architecture notes
├─ docs/AI_CONTRACT.md   ← request/response contract between UI and API
├─ backend/
│  ├─ main.py            ← all server logic (FastAPI + Gemini)
│  ├─ requirements.txt   ← Python dependencies
│  └─ .env.example       ← key template
└─ frontend/
   ├─ src/
   │  ├─ pages/          ← Home, NewAssessment, Assessment, …
   │  ├─ components/     ← RiskMeter, FirstAidSteps, EmergencyCard, …
   │  ├─ controllers/    ← useAssessment, useProfile, AuthContext
   │  ├─ services/ai/    ← remoteAi.js (API client / translation layer)
   │  └─ models/         ← data models & local storage
   └─ .env.example
```

---

## 🧯 Troubleshooting

| Symptom | Fix |
|---------|-----|
| Browser shows a **CORS** error | Make sure the backend is running on port `8000` and `VITE_AI_SERVICE_URL` matches. |
| Request stuck on **“pending / Provisional headers”** | Normal — an AI reply takes ~3–16s (the final assessment is the slowest). Wait for the loader. |
| **502 Bad Gateway** | A transient Gemini failure; just retry. Confirm your API key and quota are valid. |
| **422 Unprocessable Entity** | Invalid profile data; the frontend sanitizes it automatically — refresh and retry. |
| Server doesn’t pick up code changes | Restart it manually (without `--reload`). |
| `pip` / `python` not found | Reinstall Python and ensure it’s on your PATH. |

---

## ⚖️ Notes & limitations

- Demonstration only — use synthetic symptom data.
- Built-in rules are limited and **not** clinician-reviewed; the model interprets answers and can make mistakes.
- The absence of an emergency alert does **not** establish safety.
- For any real emergency, always call your local emergency number (**911**).
