# CLAUDE.md — Hair Salon Appointment App

PROJECT: Python/Tkinter/SQLite desktop appointment-booking app for a hair salon ("Κομμώσεις για όλα τα γούστα"). Formerly a graded EAP university project (complete, 10/10); now personal hardening \+ portfolio piece. This file is auto-read at session start — treat everything below as standing rules for this repo.

## HARD RULES

<!-- SYNC v1 — mirrored in project instructions; bump on any edit -->

- App UI language \= Greek. All in-app text (labels, menus, placeholders) and in-app error/message dialogs shown to the salon end user MUST be Greek, never English. Governs the app only — code comments, commit messages, and replies to the developer stay English.  
- SMTP creds: entered per-send, memory-only. NEVER persist to disk — no file, no keyring, no env dump, no logging.

<!-- /SYNC v1 -->

## FILE MAP

- `main.py` — entry point → `MainApp` in `gui.py`  
- `gui.py` — all Tkinter UI \+ most logic  
- `models.py` — `Customer`, `Appointment` (SQLite data layer)  
- `database.py` — schema \+ connection. Tables: `customers`, `appointments` (single `datetime` column, not separate date/time)  
- `export_excel.py` — XlsxWriter per-day export  
- `emails_utils.py` — smtplib reminder sender (`EmailSender`)  
- `salon_appointments.db` — runtime SQLite data. Don't depend on its contents for logic.

## DEPS

<!-- SYNC v1 — mirrored in project instructions; bump on any edit -->

- stdlib: tkinter, sqlite3, smtplib (smtplib is NOT pip-installable — README is wrong on this)  
- third-party: tkcalendar, tktooltip, XlsxWriter, sv-ttk (Sun Valley theme; pip name `sv-ttk`, import name `sv_ttk`)  
- PIL: imported commented-out; not active  
- Install: `pip install tkcalendar tktooltip XlsxWriter sv-ttk`

<!-- /SYNC v1 -->

## RUN / TEST

- Run app: `python main.py`  
- Tests: `python test_bugfixes.py` — plain runnable script (no pytest framework). Chdirs to a temp dir so the real `salon_appointments.db` is untouched.

## GIT

- `main` tracks `origin/main`, so `git status` reports ahead/behind for it. But `push.autoSetupRemote` is unset (local and global), so any NEW branch starts with no upstream and `git status` then stays SILENT about unpushed commits on it. Use `git push -u origin <branch>` the first time you push a branch.  
- Remote is `github.com/trickywisdom/appointment-system`, moved from `PLHPRO/appointment-system`. Credentials are per-repo on GitHub: pushing requires the `spyrostrimis` account to hold collaborator access on the new repo, otherwise the push fails with a 403 even though the URL is correct.

## CHANGE DISCIPLINE

<!-- SYNC v1 — mirrored in project instructions; bump on any edit -->

- Small, scoped, one concern per change. Reviewable diffs.  
- Flag any bonus/adjacent fix explicitly. Never bundle silently.  
- Multi-file/bug work: trace data flow directly across methods (e.g. save path in gui.py → models.py). No shape pattern-matching. Prefer direct file reads over subagent summaries that drop cross-method context.  
- Before claiming done: show the real diff, run the test/script and show real output, and call out anything that still needs manual GUI testing. Do not assert "passes" without evidence.

<!-- /SYNC v1 -->

## KNOWN LANDMINES (snapshot — may lag current code; verify against the actual files, they are the source of truth)

- Overlap validation is enforced in `models.Appointment.save_to_db` (`find_overlap` \+ `AppointmentOverlapError`, interval test on stored duration). DO NOT reintroduce dropdown-only checking or bypass this choke point.  
- Customer search normalizes both sides for comparison in `models._normalize`: NFD, strip combining marks, casefold — so accents and case do not matter. `models.Customer.matches` searches first name, last name, phone and email; the phone is deliberately NOT normalized. A term containing spaces splits into tokens and ALL tokens must match some field, so a full name works in either word order and partial tokens work. An empty term yields zero tokens and `all([])` is True, so everyone matches — the pages rely on this for show-all, and any rewrite must preserve it.  
- `SEARCH_PLACEHOLDER` (`gui.py`, module level) is written into the traced `search_var` at NINE sites — six via `Entry.insert` on a `textvariable`-bound widget, three via `search_var.set` — so the placeholder text is itself a live search term on every page. It is inert only because of the `🔍` and the comma in `"Όνομα,"`; the tokens `η` and `email` would otherwise match real customers. Changing the wording requires re-verifying it matches no customer.  
- The not-found branch of `search_customer` (both listbox pages) never rebinds `<<ListboxSelect>>`, so the binding from the previous call survives with a stale closure over the OLD filtered list. That branch is entered after every successful selection, then hidden.  
- `export_excel.export_customer_appointments` has three defects: it calls a nonexistent `Appointment.get_by_customer` (real name is `get_by_customer_id`), writes `appt.datetime` into BOTH the date and the time column, and still contains a `print("So far so good3:")` debug line. Uncalled from anywhere.  
- Frozen `datetime.today()` default arguments in `CalendarView.build_grid` / `load_appointments` — evaluated once at import, so an app left running past midnight keeps showing launch day as "today".  
- `gui.py` quality debt: `search_customer` ×3, `show_all_customers` ×1, `show_new_client_popup`/`on_popup_close` ×2; `service_durations` defined twice (dict in `get_time_options` vs if/elif chain in `save_appoint` — can drift); English `"Error"` dialogs inside the Greek UI (×6), one of which reports "Failed to fetch customers" while actually fetching appointments.  
- Open functional bugs (fix only when instructed): no phone/email format validation (no `re` import anywhere in the project); SMTP send blocks the Tk main thread (no `threading` anywhere).  
- `test_bugfixes.py` sections share ONE mutating database and run in order — section \[8\](δ) renames customer 1 mid-run. New sections must create and own their fixtures; do not key assertions on names created by an earlier section.

## SCOPE

- Active feature/bug priorities are decided in planning chats, not in this file. When starting a task, work from the specific instruction given — do not guess at "what's next" and start editing.

