# OBITO AI

Personal AI operating system by **FAKHIR AI**.

Tagline: **Your Voice. Your Commands. Your Intelligence.**

The app includes account authentication, hosted LLM chat, and the OBITO interface.

## How to run (two terminals)

### 1. Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```powershell
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Configure hosted AI

Set `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY` in `backend/.env`, then restart the backend.
The endpoint must support the OpenAI Chat Completions API format and use HTTPS. The default
settings target OpenAI; other compatible providers can use their own base URL and model name.
Never put the API key in frontend code or share it in chat.

## What works now

- Create account
- Sign in
- Forgot password (uses the recovery code shown once at sign up)
- Logout
- Profile update
- Dashboard status from the backend
- Activity logs
- Voice Center microphone permission test
- Saved chat conversations with context-aware responses from a hosted LLM
- Push-to-talk speech input in Chat (transcription is handled by the browser)
- All 12 navigation pages

## What is not built yet

Chat requires a configured hosted LLM API key. User messages and recent conversation context are
sent to that provider; the key remains on the backend, and conversation history is stored in the
local database. Voice recognition is activated only by button press and may be processed by the
browser's own speech service. The assistant has no tools to control your computer or perform
external actions. Coding studio, PC control, and Roblox Studio are not built yet.

## Folder layout

- `backend/` — FastAPI + SQLite
- `frontend/` — Next.js interface
