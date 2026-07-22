# CLAUDE.md — Hair Salon Appointment App

PROJECT: Python/Tkinter/SQLite desktop appointment-booking app for a hair salon ("Κομμώσεις για όλα τα γούστα"). Formerly a graded EAP university project (complete, 10/10); now personal hardening \+ portfolio piece. This file is auto-read at session start — treat everything below as standing rules for this repo.

## HARD RULES

- App UI language \= Greek. All in-app text (labels, menus, placeholders) and in-app error/message dialogs shown to the salon end user MUST be Greek, never English. Governs the app only — code comments, commit messages, and replies to the developer stay English.  
- SMTP creds: entered per-send, memory-only. NEVER persist to disk — no file, no keyring, no env dump, no logging.

## FILE MAP

- `main.py` — entry point → `MainApp` in `gui.py`  
- `gui.py` (\~2260 lines) — all Tkinter UI \+ most logic  
- `models.py` — `Customer`, `Appointment` (SQLite data layer)  
- `database.py` — schema \+ connection. Tables: `customers`, `appointments` (single `datetime` column, not separate date/time)  
- `export_excel.py` — XlsxWriter per-day export  
- `emails_utils.py` — smtplib reminder sender (`EmailSender`)  
- `salon_appointments.db` — runtime SQLite data. Don't depend on its contents for logic.

## DEPS

- stdlib: tkinter, sqlite3, smtplib (smtplib is NOT pip-installable — README is wrong on this)  
- third-party: tkcalendar, tktooltip, XlsxWriter  
- PIL: imported commented-out; not active  
- Install: `pip install tkcalendar tktooltip XlsxWriter`

## RUN / TEST

- Run app: `python main.py`  
- Tests: `python test_bugfixes.py` — plain runnable script (no pytest framework). Chdirs to a temp dir so the real `salon_appointments.db` is untouched.

## CHANGE DISCIPLINE

- Small, scoped, one concern per change. Reviewable diffs.  
- Flag any bonus/adjacent fix explicitly. Never bundle silently.  
- Multi-file/bug work: trace data flow directly across methods (e.g. save path in gui.py → models.py). No shape pattern-matching. Prefer direct file reads over subagent summaries that drop cross-method context.  
- Before claiming done: show the real diff, run the test/script and show real output, and call out anything that still needs manual GUI testing. Do not assert "passes" without evidence.

## KNOWN LANDMINES (snapshot — may lag current code; verify against the actual files, they are the source of truth)

- Overlap validation is now enforced in `models.Appointment.save_to_db` (`find_overlap` \+ `AppointmentOverlapError`, interval test on stored duration). DO NOT reintroduce dropdown-only checking or bypass this choke point.  
- `gui.py` quality debt: heavy copy-paste (search\_customer ×3, popup helpers ×2); `service_durations` defined twice (dict vs if/elif — can drift); \~60 lines commented-out dead code; some English dialogs \+ misleading messages inside the Greek UI.  
- Dead/broken: `models.Appointment.get_all()` has a bad `ORDER BY` on nonexistent columns; `export_customer_appointments` uses a wrong method name and is unwired; frozen `datetime.today()` default-argument in the calendar grid.  
- Open functional bugs (fix only when instructed): edit-appointment can't change the customer (silent); favicon fallback crash on missing `images/favicon.png`; popup-save doesn't close the popup (dead `is_popup` flag); no email/first-name search; no phone/email format validation; SMTP send blocks the Tk main thread.

## SCOPE

- Active feature/bug priorities are decided in planning chats, not in this file. When starting a task, work from the specific instruction given — do not guess at "what's next" and start editing.

