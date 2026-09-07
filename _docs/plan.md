# Household Chores Tracker — Spec

## Overview

A local web app for tracking shared household chores. One admin (the
user) manages the app. Chores are assigned to household members, who
are data records, not app users — there is no login or multi-user
auth.

## Functional Requirements

### 1. Household Members

1.1. The admin can create, edit, and delete household members.
1.2. A household member has exactly one field: `name`.
1.3. A household member cannot be deleted while referenced as a
     chore's `assignee` or a member of a `rotation_pool`; deletion
     must be blocked or the chore's assignment must be updated first.

#### Acceptance criteria

- Creating a member with a name persists it and it appears in all
  member-selection lists (chore assignee, rotation pool).
- Deleting a member not referenced by any chore succeeds immediately.
- Deleting a member referenced by a chore is rejected with a clear
  message identifying the blocking chore(s).

### 2. Chores

2.1. The admin can create, edit, and delete chores.
2.2. A chore has: `name`, `description`, `priority` (low / medium /
     high), `kind` (one-off / recurring), `interval_days` (required
     if `kind` is recurring, otherwise unset), `assignment_mode`
     (manual / auto-rotate), `assignee` (required if `assignment_mode`
     is manual), `rotation_pool` (required, 2+ members, if
     `assignment_mode` is auto-rotate), `next_due_date`, `active`.
2.3. A one-off chore must not have `interval_days` set.
2.4. A recurring chore must have `interval_days` >= 1.
2.5. An auto-rotate chore's `rotation_pool` must contain at least 2
     household members.

#### Acceptance criteria

- Creating a recurring chore without `interval_days` is rejected.
- Creating an auto-rotate chore with fewer than 2 people in
  `rotation_pool` is rejected.
- Editing a chore's `assignment_mode` from auto-rotate to manual
  requires selecting a single `assignee` before saving.

### 3. Completion

3.1. The admin can mark any active chore as done.
3.2. Marking a chore done creates a `CompletionLog` entry recording
     `chore`, `completed_by` (the chore's current `assignee` at the
     time of completion), `completed_at`, and the chore's
     `next_due_date` at the time of completion.
3.3. If the chore is recurring, `next_due_date` is set to the prior
     `next_due_date` plus `interval_days`.
3.4. If the chore is recurring and `assignment_mode` is auto-rotate,
     `assignee` advances to the next member in `rotation_pool`
     (round-robin, wrapping from the last member back to the first).
3.5. If the chore is one-off, `active` is set to `False` and it no
     longer appears on the dashboard or in chore-selection lists,
     but remains visible in history.

#### Acceptance criteria

- Marking a daily (`interval_days=1`) recurring chore done sets
  `next_due_date` to exactly one day after its previous
  `next_due_date`, regardless of what day it was actually completed.
- Marking an auto-rotate chore done advances `assignee` to the next
  person in `rotation_pool`; completing it once per pool member
  returns `assignee` to the original person.
- Marking a one-off chore done sets `active=False` and it is excluded
  from the dashboard on next load.
- Each completion produces exactly one `CompletionLog` row.

### 4. Dashboard

4.1. The dashboard lists all active chores in three buckets:
     **overdue** (`next_due_date` < today), **due today**
     (`next_due_date` == today), **upcoming** (`next_due_date` within
     the next 7 days, exclusive of today).
4.2. Chores within each bucket are grouped by current `assignee`.
4.3. Each chore listed has a "mark done" action that performs the
     behavior in section 3 without a full page reload.

#### Acceptance criteria

- A chore due yesterday appears only in "overdue".
- A chore due in 8+ days does not appear on the dashboard.
- Clicking "mark done" removes/updates the chore's dashboard entry
  without a full page navigation.

### 5. History Log

5.1. The admin can view a list of all `CompletionLog` entries,
     newest first.
5.2. The list is filterable by household member and by chore.
5.3. Each entry shows whether it was on-time or late, computed by
     comparing `completed_at` to the due date stored on the log entry
     at completion time.

#### Acceptance criteria

- Filtering by a member shows only completions where
  `completed_by` matches.
- A completion where `completed_at` is after the stored due date is
  labeled "late"; otherwise "on-time".
- History entries for a since-completed one-off chore remain visible
  and correctly labeled after the chore is deactivated.

## Data Model (Contract)

**HouseholdMember**
- `name`

**Chore**
- `name`, `description`
- `priority`: low / medium / high
- `kind`: one-off / recurring
- `interval_days`: integer, required iff `kind == recurring`
- `assignment_mode`: manual / auto-rotate
- `assignee`: FK → HouseholdMember, required iff `assignment_mode == manual`
- `rotation_pool`: M2M → HouseholdMember, required (2+) iff `assignment_mode == auto-rotate`
- `next_due_date`: date
- `active`: boolean, default True

**CompletionLog**
- `chore`: FK → Chore
- `completed_by`: FK → HouseholdMember
- `completed_at`: timestamp
- `due_date_at_completion`: date (snapshot of `chore.next_due_date` at completion time)

## Non-Goals

- Notifications/reminders (email, push, etc.)
- Login / multi-user accounts
- Specific-day-of-week recurrence (e.g. "every Monday and Thursday")
- Gamification (points, streaks, badges)
- Deployment/hosting — local use only

## Technical Constraints

- Django project, single app.
- SQLite via the Django ORM.
- Server-rendered Django templates; no separate frontend build.
- "Mark done" is the only action requiring JS (fetch POST, partial
  update); no other REST/JSON API surface.

## Testing

- Model-level: rotation round-robin wraps correctly; recurring
  due-date math; one-off chores deactivate on completion.
- View-level: dashboard bucket boundaries (overdue/today/upcoming);
  mark-done flow for every `kind` × `assignment_mode` combination;
  history filtering and on-time/late labeling.
