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
- third-party: tkcalendar, tktooltip, XlsxWriter, sv-ttk (Sun Valley theme; pip name `sv-ttk`, import name `sv_ttk`)  
- PIL: imported commented-out; not active  
- Install: `pip install tkcalendar tktooltip XlsxWriter sv-ttk`

## RUN / TEST

- Run app: `python main.py`  
- Tests: `python test_bugfixes.py` — plain runnable script (no pytest framework). Chdirs to a temp dir so the real `salon_appointments.db` is untouched.

## GIT

- `main` tracks `origin/main`, so `git status` reports ahead/behind for it. But `push.autoSetupRemote` is unset (local and global), so any NEW branch starts with no upstream and `git status` then stays SILENT about unpushed commits on it. Use `git push -u origin <branch>` the first time you push a branch.  
- Remote is `github.com/trickywisdom/appointment-system`, moved from `PLHPRO/appointment-system`. Credentials are per-repo on GitHub: pushing requires the `spyrostrimis` account to hold collaborator access on the new repo, otherwise the push fails with a 403 even though the URL is correct.

## CHANGE DISCIPLINE

- Small, scoped, one concern per change. Reviewable diffs.  
- Flag any bonus/adjacent fix explicitly. Never bundle silently.  
- Multi-file/bug work: trace data flow directly across methods (e.g. save path in gui.py → models.py). No shape pattern-matching. Prefer direct file reads over subagent summaries that drop cross-method context.  
- Before claiming done: show the real diff, run the test/script and show real output, and call out anything that still needs manual GUI testing. Do not assert "passes" without evidence.

## KNOWN LANDMINES (snapshot — may lag current code; verify against the actual files, they are the source of truth)

- Overlap validation is enforced in `models.Appointment.save_to_db` (`find_overlap` \+ `AppointmentOverlapError`, interval test on stored duration). DO NOT reintroduce dropdown-only checking or bypass this choke point.  
- Customer search is accent-sensitive: Greek `.lower()` preserves the tonos, and Greek capitals carry none, so caps-lock input can NEVER match an accented stored name (`ΠΑΠΑΔΟΠΟΥΛΟΥ`.lower() → `παπαδοπουλου` ≠ `παπαδοπούλου`). Pinned by section \[9\] of the tests.  
- The search predicate matches last name OR phone only — not first name, not email, not full "First Last". Single source: `models.Customer.matches`; the phone side is deliberately not lowercased.  
- The not-found branch of `search_customer` (both listbox pages) never rebinds `<<ListboxSelect>>`, so the binding from the previous call survives with a stale closure over the OLD filtered list. That branch is entered after every successful selection, then hidden.  
- `show_all_customers` is dead on `DashboardPage` and `NewAppointPage` (0 callers since the predicate extraction). `ClientsPage`'s copy is still live, called by `load_clients`.  
- `models.Appointment.get_all()` orders by nonexistent `date`/`time` columns (the schema has a single `datetime`), so it raises, gets swallowed by its own `except`, and returns `[]` every time. Zero callers; slated for deletion.  
- `export_excel.export_customer_appointments` has three defects: it calls a nonexistent `Appointment.get_by_customer` (real name is `get_by_customer_id`), writes `appt.datetime` into BOTH the date and the time column, and still contains a `print("So far so good3:")` debug line. Uncalled from anywhere.  
- Frozen `datetime.today()` default arguments in `CalendarView.build_grid` / `load_appointments` — evaluated once at import, so an app left running past midnight keeps showing launch day as "today".  
- `gui.py` quality debt: `search_customer` ×3, `show_all_customers` ×3, `show_new_client_popup`/`on_popup_close` ×2; `service_durations` defined twice (dict in `get_time_options` vs if/elif chain in `save_appoint` — can drift); English `"Error"` dialogs inside the Greek UI (×8), one of which reports "Failed to fetch customers" while actually fetching appointments.  
- Open functional bugs (fix only when instructed): no first-name/email search; no phone/email format validation (no `re` import anywhere in the project); SMTP send blocks the Tk main thread (no `threading` anywhere).  
- `test_bugfixes.py` sections share ONE mutating database and run in order — section \[8\](δ) renames customer 1 mid-run. New sections must create and own their fixtures; do not key assertions on names created by an earlier section.

## SCOPE

- Active feature/bug priorities are decided in planning chats, not in this file. When starting a task, work from the specific instruction given — do not guess at "what's next" and start editing.

