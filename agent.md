# agent.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Development setup (first time)
./setup.sh          # Installs Python 3.10.13, creates venv, installs deps

# Run locally
source venv/bin/activate
python3 app.py      # Starts Flask dev server

# Or shortcut
./run.sh

# Initialize database
python3 init_db.py

# Create admin user
python3 create_admin.py

# Production
gunicorn app:app --bind=0.0.0.0:$PORT
```

No test suite exists in this project.

## Architecture

Single-module Flask app with one auth blueprint:

- **`app.py`** — All main routes (~39) and business logic in one file
- **`models.py`** — SQLAlchemy models; the core domain
- **`auth.py`** — `@admin_required`/`@user_required` decorators and audit helpers
- **`auth_routes.py`** — Auth blueprint registered at `/auth` prefix
- **`utils.py`** — Utility functions
- **`wsgi.py`** — Gunicorn entry point

### Data Model

```
User ──────────────────── AuditLog (all CRUD operations)
Cliente ──┐
          ├── Prestamo ── Cuota ── Pago
Garante ──┘
```

**Prestamo** states: `ACTIVO → JUDICIAL | FINALIZADO`  
**Cuota** states: `PENDIENTE → PAGO_PARCIAL → JUDICIAL | PAGADA`

Key methods on `Cuota`:
- `registrar_pago_con_trazabilidad()` — preferred; creates a `Pago` audit record
- `calcular_interes_diario()` — 0.5% daily on overdue amount
- `monto_total_pendiente()` — owed including accrued interest

Key methods on `Prestamo`:
- `verificar_estado()` — call after any payment to auto-finalize if all cuotas are paid
- `marcar_judicial()` — cascades judicial state to all pending cuotas

### Database

SQLite at `instance/prestamos.db`. Schema changes are managed via ad-hoc scripts in `migrations/`. When adding columns or modifying schema, create a new script there rather than relying on ORM auto-migration.

### Session & Security

- 30-minute session timeout, filesystem sessions
- CSRF via Flask-WTF on all forms
- Role-based: `admin` vs `user` (via `role` field on `User`)
- All writes go through `audit_change()` from `auth.py` for compliance tracking

### Document Generation

Contracts and pagarés are generated as `.docx` via `python-docx` in routes `/generar_contrato/<id>` and `/generar_pagare/<id>`.

### External API

BCRA central debt registry at `/consultar_bcra` — queries `api.bcra.gob.ar` by CUIT.

### Deployment

Deployed on Render via `render.yaml` and `Procfile`. Gunicorn config in `gunicorn.conf.py` (4 workers, 2 threads, 120s timeout, `preload_app=True`).

Guidelines for Interaction:
1. Analyze requirements carefully and implement exactly what was requested.
2. Propose a short step-by-step plan before coding when scope is not trivial.
3. Keep solutions pragmatic and consistent with the current architecture.
4. Write code that is:
   - Correct: Fully functional and robust.
   - Readable: Simple, maintainable, and explicit.
   - DRY: Avoid unnecessary duplication.
   - Complete: Include required imports and no placeholders.
5. If requirements are ambiguous, ask concise clarifying questions first.

Implementation Guidelines:
- Prefer minimal diffs over broad refactors.
- Reuse existing patterns in `app.py`, `models.py`, and `auth_routes.py`.
- Use descriptive naming for variables, functions, and constants.
- Prefer early returns to simplify control flow.
- Preserve backward compatibility unless user requests breaking changes.
- Add brief comments only for non-obvious logic.
- Include basic validation and error handling on DB writes and form processing.

Token Efficiency Rules:
- Read only files relevant to the task.
- Do not restate full architecture unless explicitly requested.
- Keep responses short, concrete, and action-oriented.
- Provide concise summaries of changes and verification steps.
- Write in "caveman mode" by default: few words, clear meaning, no extras.

Communication Compression Rules (Max Token Saving):
- Use minimal words; avoid filler, repetition, and polite padding.
- Prefer short, direct sentences with simple structure (caveman style).
- Default format: action + object + result.
- Avoid long introductions, conclusions, and redundant context.
- If user asks for detail, then expand only that section.
