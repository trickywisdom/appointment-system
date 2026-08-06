# -*- coding: utf-8 -*-
"""
Επιβεβαίωση για τα δύο bug fixes:
  1) Έλεγχος επικάλυψης ραντεβού κατά την αποθήκευση (απόρριψη double-booking)

Τρέχει σε προσωρινό φάκελο ώστε να ΜΗΝ αγγίξει το πραγματικό salon_appointments.db
(όλα τα sqlite3.connect χρησιμοποιούν relative path).

Εκτέλεση:  python test_bugfixes.py
"""
import os
import sys
import tempfile
from datetime import datetime, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

workdir = tempfile.mkdtemp(prefix="appt_test_")
os.chdir(workdir)

import database
from models import Customer, Appointment, AppointmentOverlapError, CustomerValidationError

passed = 0
failed = 0

def check(name, condition, extra=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  OK   {name}")
    else:
        failed += 1
        print(f"  FAIL {name} {extra}")

print(f"Προσωρινή βάση: {os.path.join(workdir, 'salon_appointments.db')}\n")
database.setup_database()

# ---------------------------------------------------------------------------
# [1] Έλεγχος επικάλυψης στο επίπεδο του μοντέλου (το μοναδικό σημείο αποθήκευσης)
# ---------------------------------------------------------------------------
print("[1] Έλεγχος επικάλυψης ραντεβού (models.Appointment.save_to_db)")

customer = Customer("Δοκιμή", "Δοκιμάκης", "6900000001", "test@example.com")
customer.save_to_db()
cust_id = customer.id

FRIDAY = "2026-07-24"  # Παρασκευή (ανοιχτό κατάστημα)

a1 = Appointment(cust_id, f"{FRIDAY} 10:00", "Βάψιμο", 60)  # 10:00-11:00
a1.save_to_db()
check("αρχικό ραντεβού 10:00-11:00 αποθηκεύτηκε", a1.id is not None)

def try_save(dt, services, duration, expect_conflict, label, appt_id=None):
    appt = Appointment(cust_id, dt, services, duration, id=appt_id)
    try:
        appt.save_to_db(appt_id)
        check(label, not expect_conflict, "(αποθηκεύτηκε ενώ έπρεπε να απορριφθεί!)")
        return appt
    except AppointmentOverlapError as e:
        check(label, expect_conflict, f"(απορρίφθηκε ενώ δεν έπρεπε: {e})")
        return None

try_save(f"{FRIDAY} 10:20", "Κούρεμα", 40, True,
         "10:20-11:00 (ξεκινά μέσα στο υπάρχον) απορρίπτεται")
try_save(f"{FRIDAY} 09:40", "Κούρεμα", 40, True,
         "09:40-10:20 (τελειώνει μέσα στο υπάρχον) απορρίπτεται")
try_save(f"{FRIDAY} 10:00", "Χτένισμα", 20, True,
         "10:00 (ίδια ώρα έναρξης) απορρίπτεται")
a2 = try_save(f"{FRIDAY} 11:00", "Χτένισμα", 20, False,
              "11:00-11:20 (ξεκινά ακριβώς στο τέλος του υπάρχοντος) επιτρέπεται")
try_save(f"{FRIDAY} 10:00", "Βάψιμο", 60, False,
         "update του ίδιου ραντεβού στην ίδια ώρα επιτρέπεται (exclude_id)", appt_id=a1.id)
try_save(f"{FRIDAY} 10:40", "Χτένισμα", 20, True,
         "update άλλου ραντεβού πάνω σε κατειλημμένη ώρα απορρίπτεται", appt_id=a2.id)

count = len(Appointment.get_by_date(FRIDAY))
check(f"στη βάση υπάρχουν ακριβώς 2 ραντεβού (βρέθηκαν {count})", count == 2)

# ---------------------------------------------------------------------------
# [2] Κλειστή ημέρα: το get_time_options / save_appoint δεν κρασάρουν πλέον
# ---------------------------------------------------------------------------
print("\n[2] Επιλογή κλειστής ημέρας (Κυριακή/Δευτέρα)")

import tkinter as tk
import gui  # το import τρέχει setup_database() στον προσωρινό φάκελο
import sv_ttk

# Τα messagebox μπλοκάρουν το script - τα αντικαθιστούμε με καταγραφή
shown_messages = []
gui.messagebox.showerror = lambda title, msg, **kw: shown_messages.append((title, msg))
gui.messagebox.showinfo = lambda title, msg, **kw: shown_messages.append((title, msg))

root = tk.Tk()
root.withdraw()
sv_ttk.set_theme("light")
page = gui.NewAppointPage(root, controller=None)

SUNDAY = datetime(2026, 7, 26).date()  # Κυριακή
page.appoint_date.set_date(SUNDAY)
page.get_time_options()  # ο guard κλειστής ημέρας καθαρίζει το πεδίο ημερομηνίας
check("το πεδίο ημερομηνίας καθαρίστηκε από τον guard", page.appoint_date.get() == "")

page.service_dropdown.set("Κούρεμα")
try:
    page.get_time_options()  # πριν το fix: UnboundLocalError στο date_str
    check("get_time_options με κενή ημερομηνία δεν σκάει", True)
except Exception as e:
    check("get_time_options με κενή ημερομηνία δεν σκάει", False,
          f"({type(e).__name__}: {e})")
check("το time dropdown απενεργοποιήθηκε", str(page.time_dropdown['state']) == 'disabled')

# save_appoint με κενό πεδίο ημερομηνίας: πριν το fix σκούσε με ValueError στο strptime
page.selected_id = cust_id  # όπως όταν ο χρήστης επιλέγει πελάτη από τη λίστα (my_upd)
page.selected_name = "Δοκιμή Δοκιμάκης"
page.search_var.set("Δοκιμή Δοκιμάκης")
shown_messages.clear()
try:
    page.save_appoint()
    check("save_appoint με κενή ημερομηνία δεν σκάει", True)
except ValueError as e:
    check("save_appoint με κενή ημερομηνία δεν σκάει", False, f"(ValueError: {e})")
check("εμφανίστηκε φιλικό μήνυμα για την ημερομηνία",
      any("ημερομηνία" in msg for _t, msg in shown_messages))

# ---------------------------------------------------------------------------
# [3] Double-booking μέσω GUI με "μπαγιάτικο" dropdown απορρίπτεται στο save
# ---------------------------------------------------------------------------
print("\n[3] Προσομοίωση stale dropdown: double-booking μέσω save_appoint")

page.appoint_date.set_date(datetime(2026, 7, 24).date())  # Παρασκευή
page.service_dropdown.set("Κούρεμα")  # 40 λεπτά
page.time_dropdown.set("10:20")  # stale επιλογή: η 10:20 είναι πλέον κατειλημμένη
shown_messages.clear()
page.save_appoint()

count = len(Appointment.get_by_date(FRIDAY))
check(f"δεν προστέθηκε ραντεβού στη βάση (παραμένουν 2, βρέθηκαν {count})", count == 2)
check("εμφανίστηκε μήνυμα επικάλυψης στον χρήστη",
      any("κατειλημμένη" in msg for _t, msg in shown_messages))

# ---------------------------------------------------------------------------
# [4] Αλλαγή πελάτη σε υπάρχον ραντεβού (edit-appointment bug)
# ---------------------------------------------------------------------------
print("\n[4] Αλλαγή πελάτη σε υπάρχον ραντεβού")

import sqlite3

def db_customer_id(appointment_id):
    """Διαβάζει το customer_id απευθείας από τη βάση (όχι μέσω των models)."""
    with sqlite3.connect('salon_appointments.db') as conn:
        row = conn.cursor().execute(
            "SELECT customer_id FROM appointments WHERE id = ?", (appointment_id,)
        ).fetchone()
    return row[0] if row else None

customer2 = Customer("Νέος", "Πελάτης", "6900000002", "new@example.com")
customer2.save_to_db()
cust2_id = customer2.id
check("δημιουργήθηκε δεύτερος πελάτης", cust2_id is not None and cust2_id != cust_id)

# --- 4α. Επίπεδο μοντέλου: το UPDATE πρέπει να γράφει και το customer_id ---
check(f"πριν την αλλαγή, το ραντεβού ανήκει στον πελάτη {cust_id}",
      db_customer_id(a1.id) == cust_id)

moved = Appointment(cust2_id, f"{FRIDAY} 10:00", "Βάψιμο", 60, id=a1.id)
moved.save_to_db(a1.id)  # ίδια ώρα, διαφορετικός πελάτης
check(f"μετά το update το customer_id στη ΒΑΣΗ έγινε {cust2_id} "
      f"(βρέθηκε {db_customer_id(a1.id)})",
      db_customer_id(a1.id) == cust2_id)

# --- 4β. Ο έλεγχος επικάλυψης εξακολουθεί να ισχύει κατά την αλλαγή πελάτη ---
try:
    clash = Appointment(cust_id, f"{FRIDAY} 10:20", "Χτένισμα", 20, id=a2.id)
    clash.save_to_db(a2.id)  # μετακίνηση πάνω στο 10:00-11:00 με άλλο πελάτη
    check("αλλαγή πελάτη ΔΕΝ παρακάμπτει τον έλεγχο επικάλυψης", False,
          "(αποθηκεύτηκε ενώ επικαλύπτεται!)")
except AppointmentOverlapError:
    check("αλλαγή πελάτη ΔΕΝ παρακάμπτει τον έλεγχο επικάλυψης", True)
check("το ραντεβού που απορρίφθηκε δεν άλλαξε πελάτη στη βάση",
      db_customer_id(a2.id) == cust_id)

# --- 4γ. Επίπεδο GUI: το save_appoint πρέπει να προτιμά τη νέα επιλογή πελάτη ---
class _StubController:
    """Ελάχιστο stub του MainApp για τα tests (χωρίς πραγματική πλοήγηση)."""
    def show_frame(self, page_name):
        pass
    def get_frame(self, page_name):
        return self
    def on_minical_date_selected(self, event=None):
        pass

page2 = gui.NewAppointPage(root, controller=_StubController())

# Φόρτωση του υπάρχοντος ραντεβού a2 (11:00, Χτένισμα) όπως κάνει το popup λεπτομερειών
popup = tk.Toplevel(root)
page2.edit_appoint(cust_id, "Δοκιμή Δοκιμάκης", f"{FRIDAY} 11:00",
                   "Χτένισμα", "", a2.id, popup)
check("το edit φόρτωσε τον αρχικό πελάτη του ραντεβού",
      page2.current_customer_id == cust_id)
check("το edit καθάρισε τυχόν προηγούμενη επιλογή πελάτη",
      page2.selected_id is None)

# Ο χρήστης επιλέγει άλλον πελάτη από τη λίστα (όπως κάνει η my_upd)
page2.selected_id = cust2_id
page2.selected_name = "Νέος Πελάτης"
page2.search_var.set("Νέος Πελάτης")
shown_messages.clear()
page2.save_appoint()

check(f"μετά το save μέσω GUI το customer_id στη ΒΑΣΗ έγινε {cust2_id} "
      f"(βρέθηκε {db_customer_id(a2.id)})",
      db_customer_id(a2.id) == cust2_id)
check("η ώρα του ραντεβού παρέμεινε 11:00",
      any(a.id == a2.id and a.datetime == f"{FRIDAY} 11:00"
          for a in Appointment.get_by_date(FRIDAY)))
check("δεν εμφανίστηκε σφάλμα στον χρήστη",
      not any(t.startswith("Σφάλμα") for t, _m in shown_messages),
      f"({shown_messages})")

# ---------------------------------------------------------------------------
# [5] Fallback όταν λείπει το images/favicon.png
# ---------------------------------------------------------------------------
print("\n[5] Fallback όταν λείπει το images/favicon.png")

root.destroy()  # κλείνουμε το πρώτο root πριν φτιάξουμε την πραγματική MainApp

# Προσομοίωση: καμία εικόνα δεν φορτώνεται (σαν να λείπει ο φάκελος images/)
def _broken_photoimage(*args, **kwargs):
    raise tk.TclError("προσομοίωση: δεν βρέθηκε το αρχείο εικόνας")

gui.PhotoImage = _broken_photoimage

app = None
try:
    app = gui.MainApp()
    app.withdraw()
    check("η MainApp ξεκινά παρά την αποτυχία φόρτωσης εικόνων", True)
except Exception as e:
    check("η MainApp ξεκινά παρά την αποτυχία φόρτωσης εικόνων", False,
          f"({type(e).__name__}: {e})")

if app is not None:
    check("το attribute favicon υπάρχει στο instance", hasattr(app, "favicon"))
    check("το favicon είναι None όταν αποτύχει η φόρτωση",
          getattr(app, "favicon", "ΛΕΙΠΕΙ") is None)

    dash = app.get_frame("DashboardPage")
    try:
        dash.show_new_client_popup()  # πριν το fix: AttributeError στο controller.favicon
        check("το popup νέου πελάτη ανοίγει χωρίς favicon", True)
    except Exception as e:
        check("το popup νέου πελάτη ανοίγει χωρίς favicon", False,
              f"({type(e).__name__}: {e})")

    open_popups = [w for w in dash.winfo_children()
                   if isinstance(w, tk.Toplevel) and w.winfo_exists()]
    check("το popup όντως δημιουργήθηκε", len(open_popups) == 1)

# ---------------------------------------------------------------------------
# [6] Αποθήκευση πελάτη μέσα από popup: το popup πρέπει να κλείνει
# ---------------------------------------------------------------------------
print("\n[6] Το popup νέου πελάτη κλείνει μετά την αποθήκευση")

def popups_of(page):
    return [w for w in page.winfo_children()
            if isinstance(w, tk.Toplevel) and w.winfo_exists()]

if app is not None and popups_of(dash):
    popup = popups_of(dash)[0]
    # Το NewClientPage ζει μέσα στο popup (διαφορετικό instance από το frames[])
    form = next(w for w in popup.winfo_children() if isinstance(w, gui.NewClientPage))
    check("το popup περιέχει φόρμα NewClientPage", form is not None)
    check("η current_frame παραμένει η Dashboard όσο είναι ανοιχτό το popup",
          app.current_frame is dash)

    form.entry_name.insert(0, "Ποπ")
    form.entry_surname.insert(0, "Απάκης")
    form.entry_phone.insert(0, "6900000003")
    form.entry_email.insert(0, "popup@example.com")

    shown_messages.clear()
    form.save_customer()

    check("ο πελάτης αποθηκεύτηκε στη βάση",
          any(c.phone == "6900000003" for c in Customer.get_all()))
    check("το popup ΕΚΛΕΙΣΕ μετά την αποθήκευση",
          len(popups_of(dash)) == 0,
          f"(παρέμειναν ανοιχτά: {len(popups_of(dash))})")
    check("παραμένουμε στη Dashboard, δεν πήγαμε στη ClientsPage",
          app.current_frame is dash)
else:
    check("υπάρχει ανοιχτό popup για τον έλεγχο", False, "(δεν βρέθηκε popup)")

# ---------------------------------------------------------------------------
# [7] <<ListboxSelect>> με κενή επιλογή δεν πρέπει να σκάει (IndexError)
# ---------------------------------------------------------------------------
print("\n[7] <<ListboxSelect>> με κενή επιλογή")

if app is not None:
    # Με exportselection=0 το Tk δεν παραδίδει virtual events σε unmapped widget,
    # οπότε για αυτόν τον έλεγχο εμφανίζουμε πραγματικά το παράθυρο και τη σελίδα.
    app.deiconify()
    app.show_frame("NewAppointPage")
    app.update()

    appt_page = app.get_frame("NewAppointPage")
    appt_page.search_var.set("")  # κενό query -> ταιριάζουν όλοι οι πελάτες
    app.update_idletasks()

    check("το my_upd είναι δεμένο στο listbox",
          bool(appt_page.l1.bind("<<ListboxSelect>>")))
    check("το listbox έχει πελάτες", appt_page.l1.size() > 0)

    # Το Tkinter καταπίνει τις εξαιρέσεις των callbacks - τις καταγράφουμε
    callback_errors = []
    app.report_callback_exception = lambda exc, val, tb: callback_errors.append(val)

    # Θετικός έλεγχος: κανονική επιλογή -> ο handler όντως τρέχει
    appt_page.selected_id = None
    appt_page.l1.selection_set(0)
    appt_page.l1.event_generate("<<ListboxSelect>>")
    app.update()
    check("κανονική επιλογή ενημερώνει το selected_id",
          appt_page.selected_id is not None, f"({callback_errors})")

    # Ο πραγματικός έλεγχος: κενή επιλογή, όπως όταν χάνεται το exportselection
    callback_errors.clear()
    sentinel = appt_page.selected_id
    appt_page.l1.selection_clear(0, tk.END)
    check("δεν υπάρχει πλέον επιλογή στο listbox",
          appt_page.l1.curselection() == ())
    appt_page.l1.event_generate("<<ListboxSelect>>")
    app.update()
    check("κενή επιλογή δεν προκαλεί εξαίρεση", not callback_errors,
          f"({callback_errors})")
    check("το selected_id δεν άλλαξε από το κενό event",
          appt_page.selected_id == sentinel)

    app.withdraw()

# ---------------------------------------------------------------------------
# [8] Edit mode: ελεύθερο κείμενο στο πεδίο πελάτη
# ---------------------------------------------------------------------------
print("\n[8] Edit mode: ελεύθερο κείμενο στο πεδίο πελάτη")

if app is not None:
    ap = app.get_frame("NewAppointPage")
    orig_owner = db_customer_id(a1.id)
    orig_name = Customer.get_name_by_id(orig_owner)

    def load_a1():
        """Φορτώνει το ραντεβού a1 στη φόρμα, όπως κάνει το popup λεπτομερειών."""
        ap.edit_appoint(orig_owner, orig_name, f"{FRIDAY} 10:00",
                        "Βάψιμο", "", a1.id, tk.Toplevel(app))
        app.update_idletasks()

    def titles():
        return [t for t, _m in shown_messages]

    # (α) ελεύθερο κείμενο που δεν αντιστοιχεί σε πελάτη -> απόρριψη
    load_a1()
    ap.search_var.set("ανύπαρκτο ονοματεπώνυμο")
    shown_messages.clear()
    ap.save_appoint()
    check("ελεύθερο κείμενο σε edit απορρίπτεται",
          any(t.startswith("Σφάλμα") for t in titles()), f"({shown_messages})")
    check("δεν εμφανίστηκε μήνυμα επιτυχίας για ελεύθερο κείμενο",
          "Επιτυχία" not in titles(), f"({shown_messages})")
    check("ο πελάτης του ραντεβού δεν άλλαξε μετά την απόρριψη",
          db_customer_id(a1.id) == orig_owner)

    # (β) πεδίο πελάτη ανέγγιχτο -> αποθηκεύεται κανονικά με τον αρχικό πελάτη
    load_a1()
    ap.notes.delete("1.0", tk.END)
    ap.notes.insert("1.0", "αλλαγή μόνο στις σημειώσεις")
    shown_messages.clear()
    ap.save_appoint()
    check("ανέγγιχτο πεδίο πελάτη -> το ραντεβού αποθηκεύεται",
          "Επιτυχία" in titles(), f"({shown_messages})")
    check("διατηρήθηκε ο αρχικός πελάτης", db_customer_id(a1.id) == orig_owner)

    # (γ) το μήνυμα επιτυχίας ονομάζει τον πελάτη που όντως γράφτηκε στη βάση
    load_a1()
    ap.selected_id = cust_id                      # ο χρήστης επιλέγει άλλον πελάτη
    ap.selected_name = Customer.get_name_by_id(cust_id)
    ap.search_var.set(ap.selected_name)
    shown_messages.clear()
    ap.save_appoint()
    saved_name = Customer.get_name_by_id(db_customer_id(a1.id))
    success = [m for t, m in shown_messages if t == "Επιτυχία"]
    check("η αλλαγή πελάτη μέσω λίστας αποθηκεύτηκε",
          db_customer_id(a1.id) == cust_id)
    check("το μήνυμα επιτυχίας ονομάζει τον πελάτη που αποθηκεύτηκε",
          bool(success) and saved_name in success[0],
          f"(μήνυμα={success}, στη βάση='{saved_name}')")

    # (δ) το όνομα στο μήνυμα διαβάζεται από τη βάση, όχι από το πεδίο αναζήτησης:
    #     μετονομάζουμε τον πελάτη ΑΦΟΥ φορτωθεί η φόρμα, ώστε τα δύο να διαφέρουν
    cur_owner = db_customer_id(a1.id)
    ap.edit_appoint(cur_owner, Customer.get_name_by_id(cur_owner), f"{FRIDAY} 10:00",
                    "Βάψιμο", "", a1.id, tk.Toplevel(app))
    app.update_idletasks()

    c = Customer.get_customer_by_id(cur_owner)
    Customer(c.first_name, "Μετονομασμένος", c.phone, c.email, cur_owner).save_to_db(cur_owner)

    shown_messages.clear()
    ap.save_appoint()  # πεδίο ανέγγιχτο -> ίδιος πελάτης, αλλά νέο επώνυμο στη βάση
    success = [m for t, m in shown_messages if t == "Επιτυχία"]
    check("το μήνυμα παίρνει το όνομα από τη βάση, όχι από το πεδίο",
          bool(success) and "Μετονομασμένος" in success[0], f"({success})")

# ---------------------------------------------------------------------------
# [9] Characterization: κωδικοποιεί τη ΣΗΜΕΡΙΝΗ συμπεριφορά αναζήτησης μαζί με τα γνωστά
# ελαττώματά της (ευαισθησία σε τόνους/κεφαλαία, δεν ψάχνει όνομα/email/πλήρες
# ονοματεπώνυμο)· το βήμα 2 θα αλλάξει σκόπιμα τέσσερα από αυτά.
# ---------------------------------------------------------------------------
print("\n[9] Characterization: αναζήτηση πελατών (Dashboard / Clients / NewAppoint)")

if app is not None:
    # Η [9] έχει δικό της fixture: οι προηγούμενες ενότητες μεταλλάσσουν το κοινό roster -
    # συγκεκριμένα η [8](δ) μετονομάζει τον πελάτη 1 σε "Μετονομασμένος" - οπότε δεν
    # στηριζόμαστε σε ονόματα που δημιούργησε άλλη ενότητα.
    fixture = Customer("Ελένη", "Παπαδοπούλου", "6971234567", "elenip@paradeigma.gr")
    fixture.save_to_db()
    check("δημιουργήθηκε ο πελάτης-fixture της [9]", fixture.id is not None)

    def listbox_rows(page):
        """Οι γραμμές του listbox ως tuple (DashboardPage / NewAppointPage)."""
        return tuple(page.l1.get(0, tk.END))

    def client_rows(page):
        """Το επώνυμο κάθε γραμμής που ζωγραφίστηκε στη ClientsPage (μη κενές μόνο)."""
        rows = []
        for row in page.scrollable_frame.winfo_children():
            labels = [w for w in row.winfo_children() if isinstance(w, tk.Label)]
            if not labels:
                continue
            text = labels[0].cget("text")
            if text:
                rows.append(text)
        return rows

    NOT_FOUND = ("   Ο πελάτης δε βρέθηκε...",)
    # Η γραμμή του listbox δείχνει πλέον ΚΑΙ το τηλέφωνο· η ταυτότητα όμως δεν προκύπτει
    # από αυτό το κείμενο (βλ. το decoupling block στο τέλος της ενότητας).
    FIXTURE_ROW = (" Ελένη Παπαδοπούλου — 6971234567",)

    # (query, mode, αναμενόμενο για listbox σελίδες, αναμενόμενο για ClientsPage)
    QUERIES = [
        # κενός όρος -> εμφανίζονται όλοι (κανένα token, all([]) is True)
        ("",                    "count",    None,                        None),
        # POSITIVE CONTROL: το επώνυμο ακριβώς όπως είναι αποθηκευμένο
        ("παπαδοπούλου",        "equals",   FIXTURE_ROW,                 ["Παπαδοπούλου"]),
        # χωρίς τόνο -> ΒΡΙΣΚΕΙ πλέον (οι τόνοι αφαιρούνται στη σύγκριση)
        ("παπαδοπουλου",        "equals",   FIXTURE_ROW,                 ["Παπαδοπούλου"]),
        # κεφαλαία -> ΒΡΙΣΚΕΙ πλέον (casefold + αφαίρεση τόνων)
        ("ΠΑΠΑΔΟΠΟΥΛΟΥ",        "equals",   FIXTURE_ROW,                 ["Παπαδοπούλου"]),
        # μικρό όνομα -> ΨΑΧΝΕΤΑΙ πλέον
        ("ελένη",               "equals",   FIXTURE_ROW,                 ["Παπαδοπούλου"]),
        # email -> ΨΑΧΝΕΤΑΙ πλέον (τμήμα του domain)
        ("paradeigma",          "equals",   FIXTURE_ROW,                 ["Παπαδοπούλου"]),
        # πλήρες ονοματεπώνυμο -> ΒΡΙΣΚΕΙ πλέον (δύο tokens, και τα δύο ταιριάζουν)
        ("Ελένη Παπαδοπούλου",  "equals",   FIXTURE_ROW,                 ["Παπαδοπούλου"]),
        # κεφαλαίο μικρό όνομα -> βρίσκει
        ("ΕΛΕΝΗ",               "equals",   FIXTURE_ROW,                 ["Παπαδοπούλου"]),
        # πλήρες ονοματεπώνυμο χωρίς τόνους -> βρίσκει
        ("ελενη παπαδοπουλου",  "equals",   FIXTURE_ROW,                 ["Παπαδοπούλου"]),
        # αντεστραμμένη σειρά λέξεων -> βρίσκει (τα tokens είναι ανεξάρτητα)
        ("παπαδοπουλου ελενη",  "equals",   FIXTURE_ROW,                 ["Παπαδοπούλου"]),
        # μερικά tokens -> βρίσκει
        ("ελενη παπ",           "equals",   FIXTURE_ROW,                 ["Παπαδοπούλου"]),
        # ολόκληρο email με κεφαλαία -> βρίσκει
        ("ELENIP@PARADEIGMA.GR","equals",   FIXTURE_ROW,                 ["Παπαδοπούλου"]),
        # NEGATIVE CONTROL: ανοησία εξακολουθεί να μη βρίσκει τίποτα
        ("ζζζζζ",               "equals",   NOT_FOUND,                   []),
        # NEGATIVE CONTROL: ένα κακό token αρκεί για να πέσει το AND
        ("ελενη ζζζζζ",         "equals",   NOT_FOUND,                   []),
        # τηλέφωνο ακριβώς -> βρίσκει
        ("6971234567",          "equals",   FIXTURE_ROW,                 ["Παπαδοπούλου"]),
        # τμήμα τηλεφώνου -> βρίσκει
        ("697123",              "contains", FIXTURE_ROW,                 ["Παπαδοπούλου"]),
    ]

    PAGES = [
        ("DashboardPage",  app.get_frame("DashboardPage"),  listbox_rows, True),
        ("NewAppointPage", app.get_frame("NewAppointPage"), listbox_rows, True),
        ("ClientsPage",    app.get_frame("ClientsPage"),    client_rows,  False),
    ]

    for page_name, pg, read_rows, is_listbox in PAGES:
        for query, mode, exp_listbox, exp_clients in QUERIES:
            expected = exp_listbox if is_listbox else exp_clients
            pg.search_var.set(query)
            app.update_idletasks()
            got = read_rows(pg)
            label = f"{page_name} q={query!r}"

            if mode == "count":
                n = len(Customer.get_all())
                check(f"{label} -> {n} γραμμές (μία ανά πελάτη)",
                      len(got) == n, f"(got={got})")
            elif mode == "equals":
                check(f"{label} -> {expected}",
                      got == expected, f"(got={got})")
            else:
                check(f"{label} -> περιέχει {expected}",
                      all(e in got for e in expected), f"(got={got})")

    # --- Decoupling: η ταυτότητα του πελάτη ΔΕΝ προκύπτει από το κείμενο της γραμμής ---
    # Φρουρεί το invariant του a30fc3e: το save_appoint δέχεται τον πελάτη μόνο αν
    # selected_name == το κείμενο του πεδίου. Αν το selected_name έπαιρνε το κείμενο της
    # γραμμής (με τηλέφωνο και παύλα), κάθε επιλογή θα περνούσε για "ελεύθερο κείμενο".
    # Χρειάζεται πραγματική παράδοση events, όπως στην [7].
    app.deiconify()
    app.update()

    for page_name in ("DashboardPage", "NewAppointPage"):
        app.show_frame(page_name)
        app.update()
        pg = app.get_frame(page_name)

        pg.search_var.set("παπαδοπούλου")
        app.update()
        check(f"{page_name}: το listbox έχει ακριβώς 1 γραμμή προς επιλογή",
              pg.l1.size() == 1, f"(rows={tuple(pg.l1.get(0, tk.END))})")

        pg.l1.selection_set(0)
        pg.l1.event_generate("<<ListboxSelect>>")
        app.update()

        check(f"{page_name}: selected_name = σκέτο όνομα, χωρίς τηλέφωνο/παύλα "
              f"(invariant a30fc3e)",
              pg.selected_name == "Ελένη Παπαδοπούλου", f"(got={pg.selected_name!r})")
        check(f"{page_name}: το πεδίο αναζήτησης δείχνει σκέτο όνομα "
              f"(invariant a30fc3e)",
              pg.search_var.get() == "Ελένη Παπαδοπούλου", f"(got={pg.search_var.get()!r})")
        check(f"{page_name}: selected_id = id του fixture (ταυτότητα από το tuple)",
              pg.selected_id == fixture.id, f"(got={pg.selected_id})")

        # --- Οι δύο σελίδες πρέπει πλέον να συμπεριφέρονται ΔΙΑΦΟΡΕΤΙΚΑ μετά την επιλογή ---
        if page_name == "DashboardPage":
            # Η επιλογή στο Dashboard ανοίγει την καρτέλα του πελάτη.
            sp = app.get_frame("ShowClientPage")
            check("DashboardPage: η επιλογή πλοηγεί στη ShowClientPage",
                  app.current_frame is sp,
                  f"(current_frame={type(app.current_frame).__name__})")
            check("DashboardPage: η ShowClientPage δείχνει το όνομα του πελάτη",
                  sp.client_name.cget("text") == "Ελένη Παπαδοπούλου",
                  f"(got={sp.client_name.cget('text')!r})")
            check("DashboardPage: η ShowClientPage δείχνει το τηλέφωνο του πελάτη",
                  sp.contact_phone.cget("text") == "6971234567",
                  f"(got={sp.contact_phone.cget('text')!r})")
        else:
            # REGRESSION GUARD: στο Νέο Ραντεβού η επιλογή τροφοδοτεί τη φόρμα και
            # ΔΕΝ πρέπει να πλοηγεί πουθενά.
            check("NewAppointPage: η επιλογή ΔΕΝ πλοηγεί (μένουμε στη φόρμα)",
                  app.current_frame is pg,
                  f"(current_frame={type(app.current_frame).__name__})")

    # --- Κουμπί "Νέο ραντεβού" στη ShowClientPage: προ-συμπλήρωση πελάτη ---
    # Η on_show είναι deferred ΚΑΙ κατασταλμένη από το editing=True, οπότε η φόρμα κρατά
    # ό,τι άφησε η προηγούμενη επίσκεψη· η customer path πρέπει να την ανοίγει καθαρή.
    sp = app.get_frame("ShowClientPage")
    na = app.get_frame("NewAppointPage")
    sp.customer_info(fixture.id)
    app.update()

    check("ShowClientPage: θυμάται το id του πελάτη που δείχνει",
          sp.current_customer_id == fixture.id, f"(got={sp.current_customer_id})")
    check("ShowClientPage: θυμάται το όνομα του πελάτη που δείχνει",
          sp.current_customer_name == "Ελένη Παπαδοπούλου",
          f"(got={sp.current_customer_name!r})")

    # Σπέρνουμε ΕΠΙΤΗΔΕΣ μπαγιάτικη κατάσταση πριν πατηθεί το κουμπί.
    # Η μπαγιάτικη ημερομηνία παράγεται από το σήμερα, ώστε να μη συμπέσει ποτέ με αυτό.
    TODAY_STR = datetime.today().strftime("%d-%m-%Y")
    STALE_DATE = datetime.today().date() + timedelta(days=30)
    STALE_STR = STALE_DATE.strftime("%d-%m-%Y")
    na.appoint_date.set_date(STALE_DATE)
    na.time_dropdown.set("15:20")
    app.update()
    # Θετικός έλεγχος: αν δεν "κόλλησε" η μπαγιάτικη κατάσταση, οι δύο guards παρακάτω
    # θα περνούσαν κενά.
    check("το μπαγιάτικο date/time όντως σπάρθηκε πριν το κουμπί",
          na.appoint_date.get() == STALE_STR and na.time_dropdown.get() == "15:20",
          f"(date={na.appoint_date.get()!r} time={na.time_dropdown.get()!r}, "
          f"περιμέναμε {STALE_STR!r}/'15:20')")

    # Πατάμε το ΠΡΑΓΜΑΤΙΚΟ κουμπί, όχι τη μέθοδο — έτσι ελέγχεται και το lambda του command
    # (σωστά keywords, σωστά attributes της ShowClientPage).
    NEW_APPT_BTN_TEXT = "➕ Νέο ραντεβού"

    def find_new_appt_button(page):
        # Ακριβής σύγκριση, όχι substring: μελλοντικό widget που απλώς περιέχει τη φράση
        # δεν πρέπει να επιλέγεται σιωπηλά στη θέση του κουμπιού.
        def walk(w):
            yield w
            for child in w.winfo_children():
                yield from walk(child)
        for w in walk(page):
            try:
                if str(w.cget("text")).strip() == NEW_APPT_BTN_TEXT:
                    return w
            except Exception:
                continue
        return None

    new_appt_btn = find_new_appt_button(sp)
    # Χωρίς αυτόν τον έλεγχο, ένας finder που δεν βρίσκει τίποτα θα ακύρωνε σιωπηλά
    # όλους τους επόμενους ελέγχους.
    check(f"βρέθηκε το κουμπί {NEW_APPT_BTN_TEXT!r} στη ShowClientPage",
          new_appt_btn is not None)

    if new_appt_btn is None:
        # Καθαρή αναφορά αντί για AttributeError που θα διέκοπτε την υπόλοιπη ενότητα.
        print(f"  ΠΑΡΑΛΕΙΨΗ: δεν βρέθηκε το κουμπί {NEW_APPT_BTN_TEXT!r} — "
              f"οι έλεγχοι prefill ΔΕΝ εκτελέστηκαν")
    else:
        new_appt_btn.invoke()
        app.update()

        check("prefill: το πεδίο πελάτη δείχνει το όνομα του πελάτη",
              na.search_var.get() == "Ελένη Παπαδοπούλου", f"(got={na.search_var.get()!r})")
        check("prefill: loaded_customer_name = το όνομα (branch 2 του guard)",
              na.loaded_customer_name == "Ελένη Παπαδοπούλου",
              f"(got={na.loaded_customer_name!r})")
        check("prefill: current_customer_id = id του fixture (branch 2)",
              na.current_customer_id == fixture.id, f"(got={na.current_customer_id})")
        check("prefill: selected_id είναι None (branch 2, ΟΧΙ branch 1)",
              na.selected_id is None, f"(got={na.selected_id})")
        check("prefill: η ημερομηνία μηδενίζεται στο σήμερα (stale-date guard)",
              na.appoint_date.get() == TODAY_STR,
              f"(got={na.appoint_date.get()!r}, σήμερα={TODAY_STR})")
        check("prefill: η ώρα καθαρίζεται (stale-time guard)",
              na.time_dropdown.get() == "", f"(got={na.time_dropdown.get()!r})")
        check("prefill: πλοηγούμαστε στη NewAppointPage",
              app.current_frame is na, f"(current_frame={type(app.current_frame).__name__})")

    # REGRESSION GUARD για την αλλαγή υπογραφής: η θετική κλήση από το ημερολόγιο
    # create_new_appointment(date, time) πρέπει να συνεχίσει να δουλεύει αμετάβλητη.
    SLOT_DATE = datetime(2026, 9, 11).date()
    na.create_new_appointment(SLOT_DATE, "11:00")
    app.update()
    check("slot path: η θέση των date/time δεν μετακινήθηκε από τα νέα ορίσματα",
          na.appoint_date.get() == "11-09-2026" and na.time_dropdown.get() == "11:00",
          f"(date={na.appoint_date.get()!r} time={na.time_dropdown.get()!r})")
    check("slot path: χωρίς customer_id δεν στήνεται branch 2",
          na.current_customer_id is None, f"(got={na.current_customer_id})")

    # --- FIX (a): ο handler της ΠΡΟΗΓΟΥΜΕΝΗΣ αναζήτησης δεν επιβιώνει στο "δε βρέθηκε" ---
    # Τα "break" bindings κόβουν μόνο ποντίκι/Enter. Τα βελάκια περνούν από τα class
    # bindings του Listbox και θέτουν επιλογή, οπότε χωρίς unbind το index 0 της γραμμής
    # "δε βρέθηκε" έλυνε στον ΠΡΩΤΟ πελάτη του προηγούμενου αποτελέσματος (μετρημένο).
    NOT_FOUND_QUERY = "ζζζζζ"
    for page_name in ("DashboardPage", "NewAppointPage"):
        app.show_frame(page_name)
        app.update()
        pg = app.get_frame(page_name)

        # 1) επιτυχής αναζήτηση -> το else-branch δένει τον my_upd πάνω σε ΜΗ κενή λίστα
        pg.search_var.set("Παπαδοπούλου")
        app.update()
        check(f"{page_name}: (a) setup — η επιτυχής αναζήτηση έδεσε τον handler",
              bool(pg.l1.bind("<<ListboxSelect>>")),
              "(δεν δέθηκε — το σενάριο δεν στήθηκε, οι επόμενοι έλεγχοι είναι κενοί)")

        # καθαρή αφετηρία, ώστε το before/after να μετράει μόνο τη γραμμή "δε βρέθηκε"
        pg.selected_id = None
        pg.selected_name = ""
        before_id, before_name = pg.selected_id, pg.selected_name

        # 2) αναζήτηση που δεν ταιριάζει σε κανέναν
        pg.search_var.set(NOT_FOUND_QUERY)
        app.update()
        check(f"{page_name}: (a) setup — δείχνεται η γραμμή 'δε βρέθηκε'",
              tuple(pg.l1.get(0, tk.END)) == NOT_FOUND,
              f"(rows={tuple(pg.l1.get(0, tk.END))})")
        check(f"{page_name}: (a) το <<ListboxSelect>> ΛΥΘΗΚΕ στη γραμμή 'δε βρέθηκε'",
              not pg.l1.bind("<<ListboxSelect>>"),
              f"(binding={pg.l1.bind('<<ListboxSelect>>')!r})")

        frame_before = app.current_frame

        # 3) πραγματική επιλογή πάνω στη γραμμή "δε βρέθηκε" — ό,τι κάνει ένα <Down>
        pg.l1.selection_set(0)
        pg.l1.event_generate("<<ListboxSelect>>")
        app.update()

        check(f"{page_name}: (a) το selected_id ΔΕΝ άλλαξε από τη γραμμή 'δε βρέθηκε'",
              pg.selected_id == before_id,
              f"(before={before_id}, after={pg.selected_id})")
        check(f"{page_name}: (a) το selected_name ΔΕΝ άλλαξε από τη γραμμή 'δε βρέθηκε'",
              pg.selected_name == before_name,
              f"(before={before_name!r}, after={pg.selected_name!r})")
        check(f"{page_name}: (a) το πεδίο αναζήτησης κρατά ό,τι πληκτρολόγησε ο χρήστης",
              pg.search_var.get() == NOT_FOUND_QUERY, f"(got={pg.search_var.get()!r})")
        if page_name == "DashboardPage":
            check("DashboardPage: (a) η γραμμή 'δε βρέθηκε' ΔΕΝ πλοηγεί πουθενά",
                  app.current_frame is frame_before,
                  f"(current_frame={type(app.current_frame).__name__})")

    # --- FIX (b): η φόρμα δεν ανοίγει ΠΟΤΕ με μπαγιάτικα date/time ---
    na = app.get_frame("NewAppointPage")
    STALE_B = datetime.today().date() + timedelta(days=45)
    STALE_B_STR = STALE_B.strftime("%d-%m-%Y")
    na.appoint_date.set_date(STALE_B)
    na.time_dropdown.set("18:40")
    app.update()
    # Χωρίς αυτόν τον έλεγχο, οι δύο επόμενοι θα περνούσαν κενοί αν δεν κόλλαγε το stale.
    check("(b) setup — το μπαγιάτικο date/time όντως σπάρθηκε",
          na.appoint_date.get() == STALE_B_STR and na.time_dropdown.get() == "18:40",
          f"(date={na.appoint_date.get()!r} time={na.time_dropdown.get()!r}, "
          f"περιμέναμε {STALE_B_STR!r}/'18:40')")

    na.create_new_appointment()  # ΧΩΡΙΣ date, ΧΩΡΙΣ time, ΧΩΡΙΣ πελάτη
    app.update()
    check("(b) χωρίς ορίσματα η ημερομηνία πέφτει στο σήμερα",
          na.appoint_date.get() == TODAY_STR,
          f"(got={na.appoint_date.get()!r}, σήμερα={TODAY_STR})")
    check("(b) χωρίς ορίσματα η ώρα καθαρίζεται",
          na.time_dropdown.get() == "", f"(got={na.time_dropdown.get()!r})")
    check("(b) χωρίς customer_id δεν στήνεται branch 2",
          na.current_customer_id is None, f"(got={na.current_customer_id})")

    # REGRESSION GUARD: γίνεται κόκκινο αν κάποιος «απλοποιήσει» τα else σε ανεπιφύλακτα
    # resets στην κορυφή — θα έτρεχαν ΜΕΤΑ τα ορίσματα και θα σκότωναν το slot booking.
    na.appoint_date.set_date(STALE_B)
    na.time_dropdown.set("18:40")
    app.update()
    na.create_new_appointment(datetime(2026, 10, 2).date(), "12:20")
    app.update()
    check("(b) regression: θετικά ορίσματα date/time ΕΠΙΒΙΩΝΟΥΝ του reset",
          na.appoint_date.get() == "02-10-2026" and na.time_dropdown.get() == "12:20",
          f"(date={na.appoint_date.get()!r} time={na.time_dropdown.get()!r})")

    app.withdraw()

# ---------------------------------------------------------------------------
# [10] Έλεγχος μορφής τηλεφώνου/email στο ΜΟΝΑΔΙΚΟ σημείο αποθήκευσης πελάτη
# (models.Customer.save_to_db) — ίδιο μοτίβο με τον έλεγχο επικάλυψης της [1].
# ---------------------------------------------------------------------------
print("\n[10] Έλεγχος μορφής τηλεφώνου/email (models.Customer.save_to_db)")

# Η ενότητα έχει δικά της fixtures και δικό της αριθμοδοτικό χώρο (69100000xx /
# valid-xx@paradeigma.gr) ώστε να μη συγκρούεται με τα UNIQUE των προηγούμενων.
def customer_exists(phone):
    return any(c.phone == phone for c in Customer.get_all())

def try_save_customer(phone, email, expect_ok, label, id=None):
    """Επιχειρεί αποθήκευση· ελέγχει ΚΑΙ την εξαίρεση ΚΑΙ το τι έγραψε στη βάση."""
    cust = Customer("Έλεγχος", "Μορφής", phone, email, id)
    try:
        cust.save_to_db(id)
    except CustomerValidationError as e:
        check(label, not expect_ok, f"(απορρίφθηκε ενώ έπρεπε να γίνει δεκτό: {e})")
        # Το choke point πρέπει να μπλοκάρει ΠΡΙΝ γραφτεί οτιδήποτε στη βάση.
        check(f"{label} -> τίποτα δεν γράφτηκε στη βάση",
              not customer_exists(phone), "(βρέθηκε γραμμή παρά την απόρριψη!)")
        return None, str(e)
    check(label, expect_ok, "(αποθηκεύτηκε ενώ έπρεπε να απορριφθεί!)")
    return cust, None

# --- (α) POSITIVE CONTROLS: έγκυρες μορφές περνούν ---
ok_cust, _ = try_save_customer("6910000001", "valid-01@paradeigma.gr", True,
                               "κινητό 10ψήφιο + κανονικό email γίνεται δεκτό")
check("ο έγκυρος πελάτης πήρε id", ok_cust is not None and ok_cust.id is not None)
try_save_customer("6910000005", "valid.05+tag@sub.paradeigma.co.uk", True,
                  "email με τελείες/+ και πολλαπλό domain γίνεται δεκτό")
try_save_customer("  6910000006  ", "  valid-06@paradeigma.gr  ", True,
                  "κενά γύρω από τις τιμές δεν ρίχνουν τον έλεγχο")
# Κανονικοποιήσιμα: ο διαχωρισμός ψηφίων είναι συνηθισμένος τρόπος πληκτρολόγησης και
# ΔΕΝ είναι λάθος του χρήστη — αφαιρείται πριν τον έλεγχο.
try_save_customer("691 000 0007", "valid-07@paradeigma.gr", True,
                  "κενά ΑΝΑΜΕΣΑ στα ψηφία κανονικοποιούνται και γίνονται δεκτά")
try_save_customer("691-000-0008", "valid-08@paradeigma.gr", True,
                  "παύλες ανάμεσα στα ψηφία κανονικοποιούνται και γίνονται δεκτές")

# --- (β) NEGATIVE CONTROLS: άκυρα τηλέφωνα απορρίπτονται ---
# Ο κανόνας είναι ΑΥΣΤΗΡΑ 69XXXXXXXX: μόνο ελληνικά κινητά, χωρίς διεθνές πρόθεμα.
# Τα τρία πρώτα ήταν ΔΕΚΤΑ στο 2c8882f και απορρίπτονται σκόπιμα πλέον.
BAD_PHONES = [
    ("2101234567",      "σταθερό — δεν ξεκινά με 69"),
    ("+306910000003",   "διεθνές πρόθεμα +30 δεν γίνεται δεκτό"),
    ("00306910000004",  "διεθνές πρόθεμα 0030 δεν γίνεται δεκτό"),
    ("69100000",        "πολύ λίγα ψηφία"),
    ("69100000012",     "πολλά ψηφία"),
    ("5910000001",      "δεν ξεκινά με 69"),
    ("6810000001",      "ξεκινά με 6 αλλά όχι 69"),
    ("69100000ab",      "γράμματα"),
    ("+16910000001",    "λάθος διεθνές πρόθεμα"),
    ("",                "κενό τηλέφωνο"),
]
for i, (bad_phone, why) in enumerate(BAD_PHONES):
    _c, msg = try_save_customer(bad_phone, f"badphone-{i}@paradeigma.gr", False,
                                f"τηλέφωνο {bad_phone!r} ({why}) απορρίπτεται")
    check(f"το μήνυμα για {bad_phone!r} είναι στα ελληνικά και αφορά το τηλέφωνο",
          msg is not None and "τηλέφων" in msg.lower(), f"(μήνυμα={msg!r})")

# --- (γ) NEGATIVE CONTROLS: άκυρα email απορρίπτονται ---
BAD_EMAILS = [
    ("xoris-papaki.gr",         "χωρίς @"),
    ("diplo@@paradeigma.gr",    "διπλό @"),
    ("xoris-domain@",           "χωρίς domain"),
    ("@xoris-onoma.gr",         "χωρίς local part"),
    ("keno mesa@paradeigma.gr", "κενό μέσα"),
    ("xoris@teleia",            "domain χωρίς τελεία"),
    ("diplh@paradeigma..gr",    "διπλή τελεία"),
    ("",                        "κενό email"),
]
for i, (bad_email, why) in enumerate(BAD_EMAILS):
    _c, msg = try_save_customer(f"692000{i:04d}", bad_email, False,
                                f"email {bad_email!r} ({why}) απορρίπτεται")
    check(f"το μήνυμα για {bad_email!r} είναι στα ελληνικά και αφορά το email",
          msg is not None and "email" in msg.lower(), f"(μήνυμα={msg!r})")

# --- (δ) Και τα δύο λάθος -> αναφέρονται ΚΑΙ ΤΑ ΔΥΟ σε ένα μήνυμα ---
_c, both_msg = try_save_customer("άκυρο", "άκυρο", False,
                                 "τηλέφωνο ΚΑΙ email άκυρα απορρίπτονται")
check("το μήνυμα αναφέρει και τα δύο προβλήματα μαζί",
      both_msg is not None and "τηλέφων" in both_msg.lower() and "email" in both_msg.lower(),
      f"(μήνυμα={both_msg!r})")

# --- (ε) ROUND-TRIP: αυτό που ΑΠΟΘΗΚΕΥΤΗΚΕ είναι το κανονικοποιημένο, όχι ό,τι δόθηκε ---
# Ένας έλεγχος που λέει μόνο «η αποθήκευση πέτυχε» δεν αποδεικνύει ΤΙΠΟΤΑ για το τι
# γράφτηκε. Διαβάζουμε με σκέτο sqlite3, παρακάμπτοντας τα models, ώστε να μη μας
# κρύψει τίποτα ένα μελλοντικό getter.
rt_cust, rt_err = try_save_customer("  691-000-0002  ", "  roundtrip@paradeigma.gr  ", True,
                                    "τηλέφωνο με κενά ΚΑΙ παύλες γίνεται δεκτό")
check("ο πελάτης του round-trip πήρε id",
      rt_cust is not None and rt_cust.id is not None, f"(σφάλμα={rt_err!r})")

if rt_cust is not None and rt_cust.id is not None:
    with sqlite3.connect('salon_appointments.db') as conn:
        stored = conn.cursor().execute(
            "SELECT phone, email FROM customers WHERE id = ?", (rt_cust.id,)
        ).fetchone()

    check("ΣΤΗ ΒΑΣΗ το τηλέφωνο αποθηκεύτηκε κανονικοποιημένο ως '6910000002'",
          stored is not None and stored[0] == "6910000002",
          f"(στη βάση={stored[0] if stored else None!r})")
    check("ΣΤΗ ΒΑΣΗ το email αποθηκεύτηκε χωρίς κενά άκρων",
          stored is not None and stored[1] == "roundtrip@paradeigma.gr",
          f"(στη βάση={stored[1] if stored else None!r})")
    # Το instance πρέπει να συμφωνεί με τη βάση: η normalize μεταλλάσσει το self.
    check("το instance κρατά την ίδια κανονικοποιημένη τιμή με τη βάση",
          rt_cust.phone == "6910000002", f"(instance={rt_cust.phone!r})")
    # Και το πρακτικό αποτέλεσμα: ο πελάτης βρίσκεται πλέον με σκέτα ψηφία.
    # (Customer.matches συγκρίνει το τηλέφωνο ΑΚΑΤΕΡΓΑΣΤΟ — γι' αυτό έχει σημασία.)
    check("ο πελάτης βρίσκεται με αναζήτηση σκέτων ψηφίων '6910000002'",
          any(c.id == rt_cust.id for c in Customer.search("6910000002")))

# --- (ζ) Το UPDATE path περνά από τον ίδιο έλεγχο, όχι μόνο το INSERT ---
if ok_cust is not None and ok_cust.id is not None:
    stale = Customer("Έλεγχος", "Μορφής", "6910000001", "valid-01@paradeigma.gr", ok_cust.id)
    stale.phone = "αυθαίρετο"
    try:
        stale.save_to_db(ok_cust.id)
        check("το update με άκυρο τηλέφωνο απορρίπτεται", False,
              "(το update πέρασε χωρίς έλεγχο!)")
    except CustomerValidationError:
        check("το update με άκυρο τηλέφωνο απορρίπτεται", True)
    reread = Customer.get_customer_by_id(ok_cust.id)
    check("το update που απορρίφθηκε ΔΕΝ άλλαξε τη γραμμή στη βάση",
          reread is not None and reread.phone == "6910000001",
          f"(στη βάση={reread.phone if reread else None!r})")

# --- (η) Επίπεδο GUI: το NewClientPage.save_customer δείχνει το ελληνικό μήνυμα ---
if app is not None:
    form = app.get_frame("NewClientPage")
    form.id = None
    form.reset_fields()
    form.entry_name.insert(0, "Γκουί")
    form.entry_surname.insert(0, "Ελεγκτής")
    form.entry_phone.insert(0, "123")            # άκυρο
    form.entry_email.insert(0, "oxi-email")      # άκυρο

    shown_messages.clear()
    form.save_customer()
    titles_10 = [t for t, _m in shown_messages]
    msgs_10 = [m for _t, m in shown_messages]

    check("GUI: εμφανίστηκε σφάλμα, όχι επιτυχία",
          "Σφάλμα" in titles_10 and "Επιτυχία" not in titles_10, f"({shown_messages})")
    check("GUI: το μήνυμα είναι το ελληνικό μήνυμα του validator",
          any("τηλέφων" in m.lower() and "email" in m.lower() for m in msgs_10),
          f"({msgs_10})")
    check("GUI: ο άκυρος πελάτης ΔΕΝ γράφτηκε στη βάση",
          not customer_exists("123"))
    # Το generic except δεν πρέπει να προλάβει το ειδικό: κανένα "Αποτυχία στην αποθήκευση"
    check("GUI: δεν εμφανίστηκε το γενικό μήνυμα αποτυχίας",
          not any("Αποτυχία στην αποθήκευση" in m for m in msgs_10), f"({msgs_10})")

    # POSITIVE CONTROL στο ίδιο μονοπάτι: με έγκυρα στοιχεία η φόρμα αποθηκεύει κανονικά.
    form.reset_fields()
    form.id = None
    form.entry_name.insert(0, "Γκουί")
    form.entry_surname.insert(0, "Εγκυρος")
    form.entry_phone.insert(0, "6930000001")
    form.entry_email.insert(0, "gui-ok@paradeigma.gr")
    shown_messages.clear()
    form.save_customer()
    check("GUI: έγκυρα στοιχεία αποθηκεύονται κανονικά",
          "Επιτυχία" in [t for t, _m in shown_messages] and customer_exists("6930000001"),
          f"({shown_messages})")

# ---------------------------------------------------------------------------
if app is not None:
    app.destroy()
print(f"\nΑποτέλεσμα: {passed} πέρασαν, {failed} απέτυχαν")
sys.exit(1 if failed else 0)
