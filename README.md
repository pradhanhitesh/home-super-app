# H&M Home — Household Management App

A private, full-stack household management platform built for two people living together. Tracks shared finances, budgets, reminders, notes, and health data — all in one place.

> **Private application.** Not open for public registration or contribution. Built as a personal project and showcased here as a portfolio piece.

---

## Overview

H&M Home solves the everyday friction of managing a shared household — who paid what, who owes whom, what needs to get done, and how to stay on top of it together. Every feature is designed for a two-person household with shared and individual contexts.

The project was built with an **AI-first engineering workflow**, using [Claude (Anthropic)](https://claude.ai) as an active coding partner throughout — not just for boilerplate, but for architecture decisions, debugging the balance ledger algorithm, designing the debt matrix, and building features end-to-end.

---

## Features

### Finance Manager
- Log expenses with title, category, amount, date, payment method, and notes
- **Four split modes**: Equal (50/50), Custom ratio, Exact amount, No split (payer absorbs all)
- Monthly budget tracking per category with rollover support
- Visual spending breakdowns (doughnut + daily bar charts per user)
- Export expenses as CSV/JSON via the data export module

### Balance Ledger
- Chronological debt matrix tracking who owes whom across all time
- Running balance after every transaction — correct temporal settlement ordering (settlements only cancel debt that existed at their date, not future expenses)
- Month-filtered ledger view with `‹ Month ›` navigation
- **PDF export**: one-click A4 landscape PDF with full split breakdown, net effect, and running balance per entry

### Settlements
- Record payments between household members to reduce outstanding debt
- Settlement history with optional notes

### Reminders
- Create reminders with title, date, and optional recurrence
- **Firebase Cloud Messaging (FCM)** push notifications — works on web and as a PWA
- In-app foreground toast alerts for incoming notifications

### Notes
- Shared household notepad
- Pinned and categorised notes

### Health Tracking
- Per-user health metric logging
- Trend visualisation over time

### Data Export
- Download all household data (expenses, settlements, reminders, notes) as a ZIP containing CSV and JSON files

### Settings
- Create and manage expense categories with custom icons and colours
- Assign categories per user
- Set monthly budgets per category
- PWA install support

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend framework | Vue 3 (Composition API) |
| Build tool | Vite |
| State management | Pinia |
| UI | Bootstrap 5 + Bootstrap Icons |
| Charts | Chart.js via vue-chartjs |
| Auth | Firebase Authentication (Google OAuth) |
| Push notifications | Firebase Cloud Messaging (FCM) |
| PWA | vite-plugin-pwa |
| Backend | Python · Flask 3 |
| ORM | SQLAlchemy 2 + Flask-Migrate (Alembic) |
| Database | PostgreSQL |
| Rate limiting | Flask-Limiter + Redis |
| Background jobs | APScheduler |
| Deployment | Render (backend + static frontend + managed Postgres) |
| AI development partner | Claude (Anthropic) |

---

## Architecture

```
home-super-app/
├── src/
│   ├── frontend/               # Vue 3 SPA
│   │   └── src/
│   │       ├── views/          # Page components (Landing, Dashboard, Finance, …)
│   │       ├── components/     # NavBar, shared UI
│   │       ├── stores/         # Pinia stores (auth, finance)
│   │       └── router/         # Vue Router with auth guards
│   └── backend/                # Flask REST API
│       └── app/
│           └── blueprints/
│               ├── auth/       # Firebase token verification, session
│               ├── finance/    # Expenses, budgets, settlements, ledger, summary
│               ├── reminders/  # Reminders + FCM token registration
│               ├── notes/      # Shared notes
│               ├── health/     # Health metrics
│               └── export/     # CSV/JSON data export
└── render.yaml                 # Render deployment config
```

### Finance balance algorithm

The core balance logic uses a **debt matrix** (`debt[debtor_uid][creditor_uid] = float`) processed **chronologically** — expenses and settlements are interleaved by date before the matrix is walked. This ensures a settlement on date D only cancels debt that existed as of date D, not expenses added later. The running balance after each ledger entry reflects this exact cumulative state.

---

## AI-Assisted Development

This project was built using Claude as an active engineering partner across the full stack:

- **Backend API design** — route structure, SQLAlchemy models, auth middleware
- **Debt matrix algorithm** — designing and debugging the temporal settlement ordering fix
- **Balance ledger feature** — end-to-end: backend endpoint, Vue component, CSS, PDF export
- **Bug diagnosis** — identifying the root cause of the summary vs. ledger balance discrepancy
- **Frontend components** — Finance modal systems, chart data wiring, responsive CSS

The workflow was conversational and iterative — describing intent, reviewing code, catching bugs, and refining behaviour through dialogue rather than manual implementation alone.

---

## Deployment

Deployed on [Render](https://render.com):

- **Backend**: Python web service · Gunicorn · `flask db upgrade` on deploy
- **Frontend**: Static site · Vite build output
- **Database**: Managed PostgreSQL on Render
- **Cache / rate-limit**: Redis (Render or external)

Environment variables are managed via Render's dashboard (see `render.yaml` for the full list of required keys).

---

## Privacy

H&M Home is a private application. Access is restricted to a pre-approved list of Google accounts (`ALLOWED_EMAILS` env var on the backend). Visitors who attempt to sign in with an unauthorised account are shown a private-use notice and are not granted access.

---

*Built by Hitesh Pradhan · AI-assisted with Claude (Anthropic)*
