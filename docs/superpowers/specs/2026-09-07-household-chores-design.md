# Household Chores Tracker — Design

## Purpose

A local web app for tracking shared household chores. One admin (the
user) manages the app; chores are assigned to household members who
are tracked as data records, not app users — there is no login or
multi-user auth.

## Scope

- Single household, single admin, no authentication.
- Chores can be one-off or recurring (simple intervals: every N days).
- Each chore is either manually assigned to a person, or set to
  auto-rotate round-robin across a pool of people.
- Dashboard shows overdue / due today / upcoming chores.
- Completion history is logged and viewable.

### Out of scope for v1

- Notifications/reminders (email, push, etc.)
- Login / multi-user accounts
- Specific-day-of-week recurrence (e.g. "every Monday and Thursday")
- Gamification (points, streaks, badges)
- Deployment/hosting — local use only (`manage.py runserver`)

## Architecture

- Django project with a single app (e.g. `chores`).
- SQLite as the database (Django default), via the Django ORM.
- Server-rendered Django templates for all pages.
- A small amount of vanilla JS for the "mark done" action: a fetch
  POST that updates the affected list without a full page reload.
- No REST API layer, no separate frontend build step.

## Data Model

**HouseholdMember**
- `name`

**Chore**
- `name`
- `description`
- `priority` — low / medium / high
- `kind` — one-off / recurring
- `interval_days` — used only when `kind` is recurring (e.g. 1, 7,
  30, or a custom N)
- `assignment_mode` — manual / auto-rotate
- `assignee` — FK to HouseholdMember, the person currently
  responsible
- `rotation_pool` — M2M to HouseholdMember, used only when
  `assignment_mode` is auto-rotate
- `next_due_date`
- `active` — boolean, false once a one-off chore is completed

**CompletionLog**
- `chore` — FK to Chore
- `completed_by` — FK to HouseholdMember
- `completed_at` — timestamp
- on-time/late is derived by comparing `completed_at` to the chore's
  `next_due_date` at the time of completion (store the due date at
  completion time so history remains accurate after the chore's
  `next_due_date` advances)

### Completion behavior

When a chore is marked done:
1. A `CompletionLog` entry is created.
2. If `kind` is recurring: `next_due_date` advances by
   `interval_days` from the previous due date. If `assignment_mode`
   is auto-rotate, `assignee` advances to the next person in
   `rotation_pool` (round-robin, wrapping around).
3. If `kind` is one-off: the chore is marked `active = False`.

## Pages / Flows

1. **Dashboard** (home) — chores bucketed into overdue (past
   `next_due_date`), due today, and upcoming (next 7 days), grouped
   by assignee. Each entry has a "mark done" button.
2. **Chores management** — create/edit/delete chores: name,
   description, priority, one-off vs. recurring + interval, manual
   assignee or rotation pool.
3. **Household members** — add/edit/remove people.
4. **History log** — list of completions, filterable by member or
   chore, showing on-time/late status.

## Testing

- Django test framework.
- Model-level tests: rotation advancement (round-robin wraps
  correctly), due-date math for recurring chores, one-off chores
  deactivating on completion.
- View-level tests: dashboard bucketing (overdue/today/upcoming
  boundaries), the mark-done flow (creates log entry, updates chore
  state correctly for each kind/assignment_mode combination).
