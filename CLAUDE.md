# CLAUDE.md — Hair Salon Appointment App

PROJECT: Python/Tkinter/SQLite desktop appointment-booking app for a hair salon ("Κομμώσεις για όλα τα γούστα"). Formerly a graded EAP university project (complete, 10/10); now personal hardening \+ portfolio piece. This file is auto-read at session start — treat everything below as standing rules for this repo.

## HARD RULES

<!-- SYNC v2 — mirrored in project instructions; bump on any edit -->

- App UI language \= Greek. All in-app text (labels, menus, placeholders) and in-app error/message dialogs shown to the salon end user MUST be Greek, never English. Governs the app only — these stay English: code comments, commit messages, replies to the developer, `state.md`, `build-diary.md`.  
- SMTP creds: entered per-send, memory-only. NEVER persist to disk — no file, no keyring, no env dump, no logging.

<!-- /SYNC v2 -->

## FILE MAP

- `main.py` — entry point → `MainApp` in `gui.py`  
- `gui.py` — all Tkinter UI \+ most logic  
- `models.py` — `Customer`, `Appointment` (SQLite data layer)  
- `database.py` — schema \+ connection. Tables: `customers`, `appointments` (single `datetime` column, not separate date/time)  
- `export_excel.py` — XlsxWriter per-day export  
- `emails_utils.py` — smtplib reminder sender (`EmailSender`)  
- `greek_text.py` — leaf module, ZERO imports: `GREEK_DAYS`, `GREEK_DAYS_SHORT`, `GREEK_MONTHS_SHORT`. Imported by both `gui.py` and `emails_utils.py`; it exists because `gui.py` imports `emails_utils`, so the reverse import would be a cycle.  
- `salon_appointments.db` — runtime SQLite data. Don't depend on its contents for logic.

## DEPS

<!-- SYNC v2 — mirrored in project instructions; bump on any edit -->

- stdlib: tkinter, sqlite3, smtplib (smtplib is NOT pip-installable — README is wrong on this)  
- third-party: tkcalendar, XlsxWriter, sv-ttk (Sun Valley theme; pip name `sv-ttk`, import name `sv_ttk`), tkinter-tooltip (pip name `tkinter-tooltip`, import name `tktooltip`)  
- PIL: imported commented-out; not active  
- Install: `pip install tkcalendar tkinter-tooltip XlsxWriter sv-ttk`  
- TRAP: `pip install tktooltip` also resolves on PyPI, but to a DIFFERENT project — TkToolTip 1.2.0, by a different author, whose top-level package is `TkToolTip/`. It installs successfully and then `from tktooltip import ToolTip` (gui.py) fails on case-sensitive filesystems, or silently imports a different author's API on Windows. Always install `tkinter-tooltip`. `main.py`'s `required_modules` is keyed correctly: `'tktooltip': 'tkinter-tooltip'` (key \= import name, value \= pip name).

<!-- /SYNC v2 -->

## RUN / TEST

- Run app: `python main.py`  
- Tests: `python test_bugfixes.py` — plain runnable script (no pytest framework). Chdirs to a temp dir so the real `salon_appointments.db` is untouched.

## GIT

- `main` tracks `origin/main`, so `git status` reports ahead/behind for it. But `push.autoSetupRemote` is unset (local and global), so any NEW branch starts with no upstream and `git status` then stays SILENT about unpushed commits on it. Use `git push -u origin <branch>` the first time you push a branch.  
- Remote is `github.com/trickywisdom/appointment-system`, moved from `PLHPRO/appointment-system`. Credentials are per-repo on GitHub: pushing requires the `spyrostrimis` account to hold collaborator access on the new repo, otherwise the push fails with a 403 even though the URL is correct.

## CHANGE DISCIPLINE

<!-- SYNC v2 — mirrored in project instructions; bump on any edit -->

- Small, scoped, one concern per change. Reviewable diffs.  
- Flag any bonus/adjacent fix explicitly. Never bundle silently.  
- Multi-file/bug work: trace data flow directly across methods (e.g. save path in gui.py → models.py). No shape pattern-matching. Prefer direct file reads over subagent summaries that drop cross-method context.  
- Before claiming done: show the real diff, run the test/script and show real output, and call out anything that still needs manual GUI testing. Do not assert "passes" without evidence.  
- Tests must be proven non-vacuous: break the fix, confirm the test goes red, restore. A green test that has never been seen red proves nothing.  
- One commit per fix.  
- Manual verification happens BEFORE the commit, not after — every commit should describe something actually seen working.

<!-- /SYNC v2 -->

## KNOWN LANDMINES (snapshot — may lag current code; verify against the actual files, they are the source of truth)

- Overlap validation is enforced in `models.Appointment.save_to_db` (`find_overlap` \+ `AppointmentOverlapError`, interval test on stored duration). DO NOT reintroduce dropdown-only checking or bypass this choke point.  
- `models.Customer.save_to_db` is the customer-validation CHOKE POINT, the sibling of the overlap check above. It calls `self.normalize()` (mutates in place, returns the typed originals so error messages echo what the user actually typed) and then `self.validate()` BEFORE opening sqlite, so nothing unvalidated is ever written. It covers INSERT and UPDATE both — new-vs-edit is decided INSIDE this method, by whether a row with that `id` already exists, NOT in `gui.py`. Any new customer write path that does not go through it skips validation entirely. `Customer.delete_from_db` is the one other writer; it is currently uncalled from anywhere.  
- `NewClientPage.save_customer` is the handler for BOTH new and edited customers — one method, one code path, discriminated only by `self.id` (None ⇒ INSERT, set ⇒ UPDATE). `NewClientPage.edit_customer` is a PRE-FILL entry point, called by the ✏️ buttons in `ClientsPage`: it fills the four entry widgets and stashes `self.id`, and does NO database work at all — despite its docstring claiming "Επεξεργασία πελάτη και update database". Do not trust that docstring.  
- Phone rule is STRICT `69XXXXXXXX` (`_PHONE_RE = ^69\d{8}$`): exactly 10 digits, leading 69. `+30`, `0030` and landlines starting with 2 are rejected BY DECISION, not by oversight — an earlier draft accepted all three and was deliberately narrowed. Whitespace and ASCII hyphens are stripped by `normalize_phone` BEFORE matching, and the stripped value is what gets STORED, so `69-47-47-47-47` is saved as `6947474747`. That matters because `Customer.matches` compares the phone RAW: a stored separator would make the customer unfindable by phone search. Email is stripped at the EDGES only — an inner space is a user error and must stay rejected, never repaired. Normalisation deliberately does NOT happen in `__init__`, because `Customer` is also built from database reads and must not silently rewrite values on load.  
- Customer search normalizes both sides for comparison in `models._normalize`: NFD, strip combining marks, casefold — so accents and case do not matter. `models.Customer.matches` searches first name, last name, phone and email; the phone is deliberately NOT normalized. A term containing spaces splits into tokens and ALL tokens must match some field, so a full name works in either word order and partial tokens work. An empty term yields zero tokens and `all([])` is True, so everyone matches — the pages rely on this for show-all, and any rewrite must preserve it.  
- `SEARCH_PLACEHOLDER` (`gui.py`, module level) is written into the traced `search_var` at NINE sites — six via `Entry.insert` on a `textvariable`-bound widget, three via `search_var.set` — so the placeholder text is itself a live search term on every page. It is inert only because of the `🔍` and the comma in `"Όνομα,"`; the tokens `η` and `email` would otherwise match real customers. Changing the wording requires re-verifying it matches no customer.  
- The not-found branch of `search_customer` (both listbox pages) never rebinds `<<ListboxSelect>>`, so the binding from the previous call survives with a stale closure over the OLD filtered list. The mechanism is still there, but since 39b6899 it is no longer routinely entered: selecting a customer writes the full name back into `search_var`, and the re-query now MATCHES that full name (tokenized, both tokens hit), so the else-branch runs and the binding is refreshed. The branch is now reached only by typing a term that matches nobody — where `<Button-1>` is bound to `"break"`, so a real click cannot set a selection.  
- `ShowClientPage.customer_info(customer_id)` takes an id, NOT five positional args, and looks the customer up itself via `Customer.get_customer_by_id`. It navigates on its own last line, so callers fetch the page with `get_frame(...)` and must NOT call `show_frame` separately. Three call sites: the two `ClientsPage` 🔍 buttons and `DashboardPage.my_upd`.  
- The two `my_upd` copies are deliberately DIFFERENT and must stay that way. `DashboardPage.my_upd` navigates to `ShowClientPage` after tearing down the dropdown; `NewAppointPage.my_upd` feeds the appointment form and must NOT navigate. Section \[9\] of `test_bugfixes.py` carries a regression guard that goes red if the navigation is copied into the NewAppointPage copy.  
- `MainApp.show_frame` calls `on_show` via `self.after(0, ...)` — deferred to the next event-loop iteration, AFTER the calling code finishes. `NewAppointPage.on_show` clears every field unless `self.editing` or `self.onlyinit` is set. Any code that pre-fills that page and then navigates MUST set `self.editing = True` BEFORE calling `show_frame`, or the pre-fill is silently wiped. `edit_appoint` and `create_new_appointment` both do this.  
- CONSEQUENCE of the above: because `on_show` is both deferred AND suppressed by `editing=True`, the `NewAppointPage` widgets keep whatever the PREVIOUS visit left in them. A calendar-slot click can leave its date and time sitting in the form three navigations later — measured, not theorised. `create_new_appointment`'s customer path therefore resets the date to today and clears the time explicitly. ANY new field added to that form will leak the same way unless it is explicitly cleared too.  
- `create_new_appointment`'s parameter ORDER is load-bearing. The signature is `(date=None, time=None, customer_id=None, customer_name=None)`. The calendar-slot binding (`gui.py` \~291) calls it POSITIONALLY as `create_new_appointment(d, t)` and is the primary way appointments get created; the `ShowClientPage` button calls it BY KEYWORD. Moving `customer_id` ahead of `date` would bind a `datetime.date` into `customer_id` and kill slot booking. Section \[9\] of `test_bugfixes.py` guards this — the check goes red with `current_customer_id` coming back as a date.  
- The test suite locates the `➕ Νέο ραντεβού` button by EXACT text match: `NEW_APPT_BTN_TEXT` in `test_bugfixes.py` must stay byte-identical to the label in `gui.py`, emoji included. Rewording the caption makes the found-check go red and skips the seven button-dependent prefill checks — loudly by design, but the coupling is invisible from either file alone.  
- `ShowClientPage` has NO `on_show`, so the `hasattr` guard in `show_frame` short-circuits and nothing runs after navigation — whatever `customer_info` set is not clobbered.  
- `ShowClientPage.get_appoints_from_id` DROPS the appointment id and everything except `datetime` and `services`; rows are rebuilt as 3-tuples of display strings. `show_appointments` then mutates `self.appoints_list` IN PLACE, appending `["", "", ""]` padding to a 10-row floor, so row index does not map cleanly to an appointment. Anything needing per-row edit or delete must fix both.  
- `save_appoint`'s customer guard reads FIVE things: `search_var` (stripped, as `typed_name`), `selected_id` \+ `selected_name` (branch 1, an explicit listbox click), and `current_customer_id` \+ `loaded_customer_name` (branch 2, a programmatic pre-fill). Either pair must match `typed_name` exactly or the save is rejected. Pre-filling a customer from elsewhere should use branch 2.  
- `export_excel.export_customer_appointments` has three defects: it calls a nonexistent `Appointment.get_by_customer` (real name is `get_by_customer_id`), writes `appt.datetime` into BOTH the date and the time column, and still contains a `print("So far so good3:")` debug line. Uncalled from anywhere.  
- Frozen `datetime.today()` default arguments in `CalendarView.build_grid` / `load_appointments` — evaluated once at import, so an app left running past midnight keeps showing launch day as "today".  
- `gui.py` quality debt: `search_customer` ×3, `show_new_client_popup`/`on_popup_close` ×2; `service_durations` defined twice (dict in `get_time_options` vs if/elif chain in `save_appoint` — can drift); English `"Error"` dialogs inside the Greek UI (×6), one of which reports "Failed to fetch customers" while actually fetching appointments.  
- Open functional bugs (fix only when instructed): SMTP send blocks the Tk main thread (no `threading` anywhere).  
- `re` is used in EXACTLY one place: `models.py`, for `_PHONE_RE` and `_EMAIL_RE` (the two customer-validation patterns). This is a deliberate boundary, NOT a prohibition — do not read the scarcity of regex in this project as a rule and hand-roll a character-by-character email or phone check to honour it. If another validation pattern is genuinely needed, put it in `models.py` beside these two. Regex should stay confined to that one file.  
- `test_bugfixes.py` sections share ONE mutating database and run in order — section \[8\](δ) renames customer 1 mid-run. New sections must create and own their fixtures; do not key assertions on names created by an earlier section.

## SCOPE

- Active feature/bug priorities are decided in planning chats, not in this file. When starting a task, work from the specific instruction given — do not guess at "what's next" and start editing.

