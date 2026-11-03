# CRISP4K Progress

## Environment
- Termux on Android 16, Node 24, npm 12, Python 3.14, Git
- Repo: github.com/bouncer-fx/Crisp4k (private), logged in via gh CLI
- Metro/Expo dev server is too heavy for this phone. Website is plain HTML in web/
- Preview site: cd web && python -m http.server 8080 --bind 127.0.0.1
- Tip: long pastes get scrambled in Termux. Paste in small pieces and verify with grep

## Done
- Phase 1: environment, Git, GitHub
- Website in web/: home page, upload validation, before/after slider (DEMO filter, not real AI)
- Expo app scaffolded in apps/mobile (never run)
- Supabase project created. Tables + RLS + signup trigger applied and verified
  (files in database/migrations/001 and 002)

## Next
- [x] Private storage bucket "photos" created
- [ ] Backend (FastAPI) with .env for keys (never commit .env)
- [x] Login/register pages with redirect (web/login.html, register.html)
- [ ] Real enhancement engine (Real-ESRGAN on cloud GPU)
- [ ] Paystack credits, deployment, APK via EAS

## Rules
- Never paste secret keys in chat. Keys live only in backend/.env

## Notes
- Backend runs on Starlette (not FastAPI): pydantic-core cannot compile on Termux. Switch to FastAPI when deployed to the cloud.
- Backend: cd backend && source .venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8000
- Confirm email is OFF in Supabase for testing. Turn on with a real email sender before launch.

## Fun touches (web/fun.js, loaded last in index.html)
- Confetti and vibration on finish, slider reveal sweep, changing status lines, Share button, drag and drop. Untested live.
