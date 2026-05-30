# Project: Home Super App

## Objective
Household management web app for 2 users (owner + partner). ML-ready data from day 1.

---

## Users & Auth
- 2 users only: owner + partner (Google accounts via Firebase Auth)
- Whitelist enforced at two levels: Firebase Auth (restrict to 2 emails) + backend middleware (reject any token not in whitelist)
- All data shared between both users (including menstrual tracker)
- Profile picture: use `photoURL` from Firebase Auth Google token — no media storage needed
- No offline support — always-online browser app
- PWA installable via browser (`vite-plugin-pwa`) — iOS 16.4+ via Safari Add to Home Screen

---

## Tech Stack
| Layer | Choice |
|---|---|
| Backend | Python 3.12 + Flask + Flask-Blueprints |
| DB | PostgreSQL (primary) + Redis (cache/sessions) |
| Frontend | Vue 3 + Vite + Vue Router + Pinia |
| CSS | Bootstrap 5 (vanilla CSS) |
| PWA | vite-plugin-pwa |
| Auth | Firebase Authentication (Google OAuth) |
| Push Notifications | Firebase Cloud Messaging (FCM) |
| OCR | Google Gemini Vision API |
| Deploy | Render (web service + managed Postgres) |
| Currency | INR |

---

## Project Structure
```
home-super-app/
├── .venv/              # Python virtual environment (project root)
├── src/
│   ├── backend/        # Flask application
│   └── frontend/       # Vue 3 + Vite application
└── PROJECT.md
```

---

## ML-Ready Data Contract (enforced day 1)
Every database table must include:
- `id` — UUID primary key
- `created_at` — TIMESTAMPTZ
- `updated_at` — TIMESTAMPTZ
- `created_by` — FK → users
- `household_id` — FK → households

---

## Unified Finance Model

All financial activity flows through a single `transactions` table.

| Field | Type | Notes |
|---|---|---|
| `transaction_type` | ENUM | `bill`, `subscription`, `grocery`, `outing`, `vacation`, `other` |
| `amount` | DECIMAL | INR |
| `transaction_date` | DATE | |
| `paid_by` | FK → users | |
| `split_amount` | DECIMAL | nullable |
| `split_with` | FK → users | nullable |
| `notes` | TEXT | |
| `tags` | TEXT[] | |
| `metadata` | JSONB | type-specific fields (see below) |
| + ML contract cols | | `id`, `created_at`, `updated_at`, `created_by`, `household_id` |

### metadata by type
- **bill** — `subcategory` (rent/electricity/water/maintenance/other), `due_date`, `recurring_interval`, `status` (paid/unpaid)
- **subscription** — `service_name`, `renewal_date`, `payment_mode`
- **grocery** — links to `grocery_items` table (one receipt = one transaction row)
- **outing / vacation / other** — free-form tags and notes

### grocery_items table
Separate table for item-level detail (supports Gemini OCR extraction):
- `transaction_id` FK → transactions
- `item_name`, `mrp` (INR), `quantity`, `unit` (count/kg/ml/L/g), `category`
- + ML contract cols

---

## Other Modules

### Reminders
- Fields: title, body, due_datetime, repeat (none / daily / weekly / monthly)
- FCM push notification on trigger

### Notes
- Fields: title, body (rich text), tags
- Shared between both users

### Menstrual Tracker
- Fields: cycle_start, cycle_end, symptoms, notes
- Predicted next date computed server-side
- Visible to both users

### Well-being Tracker
- Fields: date, mood (1–10), energy (1–10), sleep_hours, notes, remarks
- User-attributed for per-user sentiment analysis later

### Vision Board
- DEFERRED — not building in current phase

---

## Dashboard
- Shared household dashboard with user filter
- Displays: unified expense summary, upcoming bills/subscriptions, recent mood trends

---

## Notifications
- FCM for push (desktop browser + iOS PWA)
- iOS requirement: app must be added to Home Screen via Safari, iOS 16.4+

---

## Deployment
- Render: web service (Flask) + managed PostgreSQL
- Single GitHub repo, CI/CD via Render auto-deploy on push to main

---

## Implementation Phases

### Phase 1 — Skeleton
- Migrate frontend from Vue CLI → Vite
- Add Vue Router, Pinia, Bootstrap 5
- Flask app factory + blueprints scaffold
- PostgreSQL schema with ML-ready columns on every table
- Alembic migrations setup
- Redis setup
- Firebase Auth JWT middleware (verify token server-side + whitelist check)
- PWA manifest + basic service worker
- Render config files (render.yaml)

### Phase 2 — Auth + Core
- Google login end-to-end (Firebase → Flask JWT verify → whitelist → user record)
- Notes module (CRUD)
- Reminders module + FCM push integration

### Phase 3 — Finance Module
- Unified transactions table + grocery_items table
- Bills UI (recurring auto-generate)
- Subscriptions UI (FCM renewal alerts)
- Groceries UI + Gemini Vision OCR endpoint
- Outings / Vacations / Other entries
- Shared dashboard with user filter + expense analytics

### Phase 4 — Health Modules
- Well-being tracker
- Menstrual cycle tracker

### Phase 5 — Polish
- Mood and expense analytics charts
- iOS PWA install + notification testing
- Notification permission UX flow
- Render production hardening (env vars, DB pooling, secrets)
