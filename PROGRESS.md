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
- [ ] Private storage bucket in Supabase
- [ ] Backend (FastAPI) with .env for keys (never commit .env)
- [ ] Login/register on the website
- [ ] Real enhancement engine (Real-ESRGAN on cloud GPU)
- [ ] Paystack credits, deployment, APK via EAS

## Rules
- Never paste secret keys in chat. Keys live only in backend/.env
