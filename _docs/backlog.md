# Household Chores Tracker — Backlog

**Spec:** `_docs/plan.md`

**Goal:** Build the Django app described in the spec, one independently
testable feature at a time.

**Tech stack:** Django (project `choretracker`, app `chores`), SQLite,
server-rendered templates, vanilla JS for the mark-done action.

Scaffolding already done: Django project and `chores` app created,
`chores` added to `INSTALLED_APPS`, initial migrations applied.

---

## Task 1: Models & validation

Implements spec §1.2, §2.2–2.5, §"Data Model (Contract)".

**Files:**
- Modify: `chores/models.py` — `HouseholdMember`, `Chore`,
  `CompletionLog`
- Create: `chores/migrations/0001_initial.py` (via `makemigrations`)
- Modify: `chores/admin.py` — register all three models for quick
  inspection while UI doesn't exist yet

**What it does:** Defines the three models and their fields exactly as
in the spec's data model. `Chore.clean()` enforces: one-off chores
can't have `interval_days` set; recurring chores need
`interval_days >= 1`; manual assignment needs `assignee`; auto-rotate
needs 2+ members in `rotation_pool`.

**Testing:** Model tests for each validation rule in `clean()`
(valid one-off, valid recurring, rejects recurring without interval,
rejects auto-rotate with <2 pool members, rejects manual without
assignee).

---

## Task 2: Household members CRUD + base layout

Implements spec §1.1, §1.3.

**Files:**
- Create: `chores/templates/chores/base.html` — shared layout/nav
  (Dashboard / Chores / Members / History links)
- Create: `chores/templates/chores/member_list.html`,
  `member_form.html`, `member_confirm_delete.html`
- Modify: `chores/views.py` — list/create/edit/delete views for
  `HouseholdMember`
- Modify: `chores/urls.py`, `choretracker/urls.py` — wire up routes,
  include `chores.urls` from the project

**What it does:** Basic CRUD for household members. Delete is blocked
with an error message when the member is referenced by any chore's
`assignee` or `rotation_pool` (§1.3).

**Testing:** View tests — create persists and appears in a
subsequent chore's assignee dropdown; delete succeeds when
unreferenced; delete is rejected with a message naming the blocking
chore when referenced.

---

## Task 3: Chore CRUD

Implements spec §2.1–2.5.

**Files:**
- Create: `chores/forms.py` — `ChoreForm` (ModelForm wrapping the
  Task 1 validation, with conditional field requirements)
- Create: `chores/templates/chores/chore_list.html`,
  `chore_form.html`, `chore_confirm_delete.html`
- Modify: `chores/views.py` — list/create/edit/delete views for
  `Chore`
- Modify: `chores/urls.py`

**What it does:** Create/edit/delete chores, surfacing the Task 1
validation as form errors (e.g. switching `assignment_mode` from
auto-rotate to manual requires picking a single assignee before
saving).

**Testing:** View tests — valid submissions save; each invalid
combination from §2.3–2.5 re-renders the form with the specific
error instead of saving.

---

## Task 4: Completion behavior

Implements spec §3.1–3.5.

**Files:**
- Modify: `chores/models.py` — add `Chore.mark_done()` method
- Modify: `chores/views.py` — add a `mark_done` view (POST-only)
  calling `Chore.mark_done()`
- Modify: `chores/urls.py`

**What it does:** `mark_done()` is the single place implementing:
create a `CompletionLog` snapshotting `completed_by` and
`due_date_at_completion`; advance `next_due_date` by `interval_days`
if recurring; advance `assignee` round-robin through `rotation_pool`
if auto-rotate; set `active=False` if one-off. This is a model
method (not just a view) so it's directly unit-testable.

**Testing:** Model tests — daily recurring chore's `next_due_date`
advances by exactly 1 day regardless of completion date; auto-rotate
`assignee` cycles correctly and returns to the start after one full
lap; one-off chore becomes `active=False`; exactly one
`CompletionLog` row is created per call, for every
kind × assignment_mode combination.

---

## Task 5: Dashboard

Implements spec §4.1–4.3.

**Files:**
- Modify: `chores/views.py` — `dashboard` view: query active chores
  into overdue / due-today / upcoming buckets, grouped by `assignee`
- Create: `chores/templates/chores/dashboard.html`
- Create: `chores/static/chores/mark_done.js` — fetch POST to the
  Task 4 endpoint, updates the DOM without a full reload
- Modify: `chores/urls.py` — dashboard as the app's root route

**Testing:** View tests — a chore due yesterday appears only under
overdue; a chore due in 8+ days is absent; a chore due today appears
under due-today. (The no-full-reload behavior is a manual/browser
check, not a Django test.)

---

## Task 6: History log

Implements spec §5.1–5.3.

**Files:**
- Modify: `chores/views.py` — `history` view with optional
  `member`/`chore` query-string filters
- Create: `chores/templates/chores/history.html`

**What it does:** Lists `CompletionLog` entries newest-first, each
labeled on-time/late by comparing `completed_at` to
`due_date_at_completion`. Filterable by member and by chore via query
params.

**Testing:** View tests — filtering by member returns only that
member's entries; a completion after its due date is labeled "late",
on/before is "on-time"; history for a deactivated one-off chore is
still listed and correctly labeled.

---

## Notes

This is a task-level backlog, not a fully detailed step-by-step TDD
plan (no per-step code snippets). When you're ready to implement a
task, ask and I'll expand it into that level of detail via the
writing-plans/executing-plans workflow, or we can just implement it
directly task-by-task from here.
