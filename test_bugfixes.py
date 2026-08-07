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
import greek_text  # leaf module: οι ελληνικοί πίνακες ημερών/μηνών ζουν εδώ, όχι στο gui
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

# --- (ς) Διπλό τηλέφωνο/email: ελληνικό μήνυμα, ΟΧΙ το ωμό κείμενο του sqlite ---
# Το UNIQUE constraint χτυπούσε ως sqlite3.IntegrityError και έφτανε στον χρήστη ως
# «Αποτυχία στην αποθήκευση του πελάτη: UNIQUE constraint failed: customers.email».
RAW_SQLITE_LEAK = "UNIQUE constraint failed"

dup_base = Customer("Πρώτος", "Κάτοχος", "6940000001", "katoxos@paradeigma.gr")
dup_base.save_to_db()
check("(ς) setup — δημιουργήθηκε ο πελάτης που κατέχει τηλέφωνο και email",
      dup_base.id is not None)

# ΔΕΝ χρησιμοποιούμε την try_save_customer εδώ: ο βοηθός της ελέγχει «καμία γραμμή με
# αυτό το τηλέφωνο», που είναι λάθος invariant για διπλότυπο — η γραμμή ΟΦΕΙΛΕΙ να υπάρχει,
# ανήκει στον άλλο πελάτη. Το σωστό invariant είναι ότι δεν προστέθηκε ΝΕΑ γραμμή.
def duplicate_attempt(phone, email, label):
    before = len(Customer.get_all())
    try:
        Customer("Διπλό", "Τυπο", phone, email).save_to_db()
        check(label, False, "(αποθηκεύτηκε ενώ έπρεπε να απορριφθεί!)")
        return None
    except Exception as e:
        # ΣΚΟΠΙΜΑ ευρύ except: αν ξαναδιαρρεύσει το sqlite3.IntegrityError, θέλουμε ΚΟΚΚΙΝΟ
        # έλεγχο εδώ, όχι κατάρρευση της σουίτας που ακυρώνει σιωπηλά ό,τι ακολουθεί.
        check(f"{label} -> ως CustomerValidationError, όχι ωμό sqlite",
              isinstance(e, CustomerValidationError),
              f"(διέρρευσε {type(e).__name__}: {e})")
        check(label, True)
        check(f"{label} -> δεν προστέθηκε νέα γραμμή",
              len(Customer.get_all()) == before,
              f"(πριν={before}, μετά={len(Customer.get_all())})")
        return str(e)

# ίδιο ΤΗΛΕΦΩΝΟ, διαφορετικό email
dup_phone_msg = duplicate_attempt("6940000001", "allo-email@paradeigma.gr",
                                  "(ς) διπλό τηλέφωνο απορρίπτεται")
check("(ς) το μήνυμα διπλού τηλεφώνου είναι ελληνικό και δείχνει τον αριθμό",
      dup_phone_msg is not None and "ήδη" in dup_phone_msg
      and "τηλέφωνο" in dup_phone_msg and "6940000001" in dup_phone_msg,
      f"(μήνυμα={dup_phone_msg!r})")
check("(ς) το μήνυμα διπλού τηλεφώνου ΔΕΝ διαρρέει το ωμό κείμενο του sqlite",
      dup_phone_msg is not None and RAW_SQLITE_LEAK not in dup_phone_msg,
      f"(μήνυμα={dup_phone_msg!r})")

# ίδιο EMAIL, διαφορετικό τηλέφωνο
dup_email_msg = duplicate_attempt("6940000002", "katoxos@paradeigma.gr",
                                  "(ς) διπλό email απορρίπτεται")
check("(ς) το μήνυμα διπλού email είναι ελληνικό και δείχνει τη διεύθυνση",
      dup_email_msg is not None and "ήδη" in dup_email_msg
      and "email" in dup_email_msg and "katoxos@paradeigma.gr" in dup_email_msg,
      f"(μήνυμα={dup_email_msg!r})")
check("(ς) το μήνυμα διπλού email ΔΕΝ διαρρέει το ωμό κείμενο του sqlite",
      dup_email_msg is not None and RAW_SQLITE_LEAK not in dup_email_msg,
      f"(μήνυμα={dup_email_msg!r})")

# Το UPDATE path χτυπά το ίδιο UNIQUE: μετακινούμε το τηλέφωνο του ενός πάνω στου άλλου.
other = Customer("Δεύτερος", "Κάτοχος", "6940000003", "deuteros@paradeigma.gr")
other.save_to_db()
clash = Customer("Δεύτερος", "Κάτοχος", "6940000001", "deuteros@paradeigma.gr", other.id)
try:
    clash.save_to_db(other.id)
    check("(ς) το UPDATE σε κατειλημμένο τηλέφωνο απορρίπτεται", False,
          "(πέρασε χωρίς σφάλμα!)")
except Exception as e:  # ευρύ σκόπιμα, όπως στη duplicate_attempt
    check("(ς) το UPDATE σε κατειλημμένο τηλέφωνο απορρίπτεται", True)
    check("(ς) το UPDATE δίνει CustomerValidationError, όχι ωμό sqlite",
          isinstance(e, CustomerValidationError),
          f"(διέρρευσε {type(e).__name__}: {e})")
    check("(ς) και εκεί το μήνυμα είναι ελληνικό, χωρίς ωμό sqlite",
          "ήδη" in str(e) and RAW_SQLITE_LEAK not in str(e), f"(μήνυμα={str(e)!r})")

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
# [11] show_appointment_popup: αποτυχία αναζήτησης πελάτη δεν αφήνει modal φάντασμα
# ---------------------------------------------------------------------------
print("\n[11] Το popup λεπτομερειών ραντεβού καταρρέει με ασφάλεια")

if app is not None:
    dash = app.get_frame("DashboardPage")

    def toplevels_of(page):
        return [w for w in page.winfo_children()
                if isinstance(w, tk.Toplevel) and w.winfo_exists()]

    # Το popup διαβάζει μόνο πεδία του Appointment, οπότε δεν χρειάζεται εγγραφή στη βάση.
    ghost_appt = Appointment(customer_id=999999, datetime=f"{FRIDAY} 10:00",
                             services="Κούρεμα", duration=40, notes="", id=999999)

    # Καθαρή αφετηρία: κλείνουμε ό,τι popup άφησαν οι προηγούμενες ενότητες.
    for w in toplevels_of(dash):
        try:
            w.grab_release()
        except tk.TclError:
            pass
        w.destroy()
    app.update()

    _real_lookup = Customer.get_customer_by_id
    Customer.get_customer_by_id = staticmethod(lambda customer_id: None)
    shown_messages.clear()
    before_tops = len(toplevels_of(dash))
    try:
        dash.show_appointment_popup(ghost_appt, "Φάντασμα Πελάτης")
        raised = None
    except Exception as e:
        raised = e
    app.update()
    Customer.get_customer_by_id = _real_lookup

    check("[11] το popup δεν πετάει εξαίρεση όταν λείπει ο πελάτης",
          raised is None, f"({type(raised).__name__}: {raised})")
    # (α) κανένα ορφανό Toplevel
    check("[11] δεν έμεινε ορφανό Toplevel στην οθόνη",
          len(toplevels_of(dash)) == before_tops,
          f"(πριν={before_tops}, μετά={len(toplevels_of(dash))})")
    # (β) κανένα grab — ΤΟ ΚΡΙΣΙΜΟ: ένα modal φάντασμα κλειδώνει την εφαρμογή
    check("[11] δεν κρατιέται grab από κανένα παράθυρο",
          app.grab_current() is None, f"(grab_current={app.grab_current()!r})")
    # (γ) ελληνικός διάλογος σφάλματος
    err_titles = [t for t, _m in shown_messages]
    err_msgs = [m for _t, m in shown_messages]
    check("[11] εμφανίστηκε διάλογος σφάλματος με ελληνικό τίτλο",
          "Σφάλμα" in err_titles, f"({shown_messages})")
    check("[11] το μήνυμα είναι ελληνικό και μιλά για τα στοιχεία του πελάτη",
          any("πελάτη" in m for m in err_msgs), f"({err_msgs})")

    # POSITIVE CONTROL: με υπαρκτό πελάτη το popup ανοίγει κανονικά και ΚΡΑΤΑ grab.
    real_cust = Customer.get_all()[0]
    real_appt = Appointment(customer_id=real_cust.id, datetime=f"{FRIDAY} 10:00",
                            services="Κούρεμα", duration=40, notes="", id=999998)
    shown_messages.clear()
    dash.show_appointment_popup(real_appt, f"{real_cust.first_name} {real_cust.last_name}")
    app.update()
    opened = toplevels_of(dash)
    check("[11] positive control: με υπαρκτό πελάτη το popup ΑΝΟΙΓΕΙ",
          len(opened) == before_tops + 1, f"(τώρα={len(opened)})")
    check("[11] positive control: δεν εμφανίστηκε σφάλμα",
          not any(t == "Σφάλμα" for t, _m in shown_messages), f"({shown_messages})")
    for w in opened:
        try:
            w.grab_release()
        except tk.TclError:
            pass
        w.destroy()
    app.update()

# ---------------------------------------------------------------------------
# [12] get_customer_by_id: «δεν υπάρχει» != «η βάση δεν απαντά»
# ---------------------------------------------------------------------------
print("\n[12] Απουσία πελάτη vs βλάβη βάσης (models.Customer.get_customer_by_id)")

# Η βλάβη παράγεται ΑΛΗΘΙΝΑ: πειράζουμε κάτι από το οποίο ΕΞΑΡΤΑΤΑΙ η μέθοδος (τον
# πίνακα customers), ΟΧΙ την ίδια τη μέθοδο. Ένα patch της μεθόδου θα απεδείκνυε μόνο
# ότι το mock δουλεύει.
class _BrokenDB:
    """Μετονομάζει προσωρινά τον πίνακα customers, ώστε κάθε SELECT να σκάει αληθινά."""
    def __enter__(self):
        with sqlite3.connect('salon_appointments.db') as conn:
            conn.execute("ALTER TABLE customers RENAME TO customers_hidden")
        return self
    def __exit__(self, *exc):
        with sqlite3.connect('salon_appointments.db') as conn:
            conn.execute("ALTER TABLE customers_hidden RENAME TO customers")
        return False

alive = Customer.get_all()[0]

# (α) απουσία -> None, ΧΩΡΙΣ εξαίρεση
missing = Customer.get_customer_by_id(10**9)
check("[12] ανύπαρκτο id επιστρέφει None", missing is None, f"(got={missing!r})")
present = Customer.get_customer_by_id(alive.id)
check("[12] υπαρκτό id επιστρέφει τον πελάτη",
      present is not None and present.id == alive.id, f"(got={present!r})")

# (β) βλάβη -> sqlite3.Error, ΟΧΙ None
with _BrokenDB():
    try:
        broken_result = Customer.get_customer_by_id(alive.id)
        check("[12] βλάβη βάσης ανεβάζει sqlite3.Error αντί να επιστρέφει None",
              False, f"(επέστρεψε {broken_result!r} — η βλάβη καταπιέστηκε)")
    except sqlite3.Error:
        check("[12] βλάβη βάσης ανεβάζει sqlite3.Error αντί να επιστρέφει None", True)
    except Exception as e:
        check("[12] βλάβη βάσης ανεβάζει sqlite3.Error αντί να επιστρέφει None",
              False, f"(ανέβηκε {type(e).__name__}: {e})")

# ο πίνακας επανήλθε
check("[12] ο πίνακας customers επανήλθε μετά τη δοκιμή",
      Customer.get_customer_by_id(alive.id) is not None)

if app is not None:
    sp = app.get_frame("ShowClientPage")
    dash = app.get_frame("DashboardPage")

    def messages_from(action):
        shown_messages.clear()
        try:
            action()
        except Exception as e:
            return [("ΑΝΕΞΕΛΕΓΚΤΗ", f"{type(e).__name__}: {e}")]
        app.update()
        return list(shown_messages)

    # --- ShowClientPage.customer_info: τα δύο μηνύματα πρέπει να ΔΙΑΦΕΡΟΥΝ ---
    absent_msgs = messages_from(lambda: sp.customer_info(10**9))
    with _BrokenDB():
        broken_msgs = messages_from(lambda: sp.customer_info(alive.id))

    absent_txt = " | ".join(m for _t, m in absent_msgs)
    broken_txt = " | ".join(m for _t, m in broken_msgs)
    check("[12] customer_info: η απουσία δίνει «Δεν βρέθηκε ο πελάτης»",
          "Δεν βρέθηκε ο πελάτης" in absent_txt, f"({absent_msgs})")
    check("[12] customer_info: η βλάβη δίνει μήνυμα ΒΑΣΗΣ, όχι «δεν βρέθηκε»",
          "βάση" in broken_txt and "Δεν βρέθηκε ο πελάτης" not in broken_txt,
          f"({broken_msgs})")
    check("[12] customer_info: τα δύο μηνύματα ΔΙΑΦΕΡΟΥΝ",
          absent_txt != broken_txt and broken_txt != "",
          f"(absent={absent_txt!r}, broken={broken_txt!r})")
    check("[12] customer_info: η βλάβη δεν διαρρέει αγγλικό κείμενο sqlite",
          "no such table" not in broken_txt.lower(), f"({broken_txt!r})")

    # --- show_appointment_popup: η βλάβη περνά ΚΑΙ ΑΥΤΗ από το teardown ---
    def toplevels_of(page):
        return [w for w in page.winfo_children()
                if isinstance(w, tk.Toplevel) and w.winfo_exists()]
    for w in toplevels_of(dash):
        try:
            w.grab_release()
        except tk.TclError:
            pass
        w.destroy()
    app.update()

    err_appt = Appointment(customer_id=alive.id, datetime=f"{FRIDAY} 10:00",
                           services="Κούρεμα", duration=40, notes="", id=999997)
    with _BrokenDB():
        popup_msgs = messages_from(
            lambda: dash.show_appointment_popup(err_appt, "Κάποιος Πελάτης"))
    popup_txt = " | ".join(m for _t, m in popup_msgs)

    check("[12] popup: η βλάβη δεν αφήνει ορφανό Toplevel",
          len(toplevels_of(dash)) == 0, f"(έμειναν {len(toplevels_of(dash))})")
    check("[12] popup: η βλάβη δεν κρατά grab",
          app.grab_current() is None, f"(grab_current={app.grab_current()!r})")
    check("[12] popup: η βλάβη δίνει μήνυμα ΒΑΣΗΣ, όχι «δεν βρέθηκαν τα στοιχεία»",
          "βάση" in popup_txt and "Δεν βρέθηκαν τα στοιχεία" not in popup_txt,
          f"({popup_msgs})")

# ---------------------------------------------------------------------------
# [13] Ονόματα ημερών/μηνών: ελληνικά ΑΝΕΞΑΡΤΗΤΑ από το locale του συστήματος
# ---------------------------------------------------------------------------
print("\n[13] Ελληνικές ημέρες/μήνες χωρίς εξάρτηση από το locale")

import locale as _locale

# ΚΡΙΣΙΜΟ: επιβάλλουμε ΜΗ ελληνικό locale. Χωρίς αυτό, ο έλεγχος θα περνούσε στο μηχάνημα
# του developer (που έχει ελληνικό locale) ακόμη και με το παλιό strftime("%A") — δηλαδή
# δεν θα απεδείκνυε τίποτα. Δοκιμάζουμε διαδοχικά ονόματα· το "C" υπάρχει παντού.
_saved_locale = _locale.setlocale(_locale.LC_TIME)
_forced = None
for _cand in ("English_United States.1252", "en_US.UTF-8", "en_US", "C"):
    try:
        _locale.setlocale(_locale.LC_TIME, _cand)
        _forced = _cand
        break
    except _locale.Error:
        continue
check("[13] setup — επιβλήθηκε μη ελληνικό locale", _forced is not None,
      "(δεν βρέθηκε κανένα· ο έλεγχος θα ήταν κενός)")
print(f"     locale δοκιμής: {_forced!r}")

GREEK_LETTERS = set("ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩάέήίόύώϊϋΐΰαβγδεζηθικλμνξοπρστυφχψως")

def is_greek(text):
    return bool(text) and any(ch in GREEK_LETTERS for ch in text)

try:
    # Θετικός έλεγχος ότι το locale ΟΝΤΩΣ άλλαξε: αν το strftime εξακολουθεί να βγάζει
    # ελληνικά, το επιβαλλόμενο locale δεν εφαρμόστηκε και οι έλεγχοι παρακάτω είναι κενοί.
    _probe = datetime(2026, 8, 6).strftime("%A")
    check("[13] setup — το strftime ΟΝΤΩΣ βγάζει πλέον μη ελληνικά",
          not is_greek(_probe), f"(strftime('%A') = {_probe!r})")

    # (α) οι πίνακες είναι πλήρεις και ελληνικοί
    check("[13] GREEK_DAYS: 7 ελληνικά ονόματα",
          len(greek_text.GREEK_DAYS) == 7 and all(is_greek(d) for d in greek_text.GREEK_DAYS),
          f"({greek_text.GREEK_DAYS})")
    check("[13] GREEK_DAYS_SHORT: 7 ελληνικές συντομεύσεις",
          len(greek_text.GREEK_DAYS_SHORT) == 7 and all(is_greek(d) for d in greek_text.GREEK_DAYS_SHORT),
          f"({greek_text.GREEK_DAYS_SHORT})")
    check("[13] GREEK_MONTHS_SHORT: 12 ελληνικές συντομεύσεις",
          len(greek_text.GREEK_MONTHS_SHORT) == 12
          and all(is_greek(m) for m in greek_text.GREEK_MONTHS_SHORT),
          f"({greek_text.GREEK_MONTHS_SHORT})")
    # η αντιστοίχιση δείκτη είναι σωστή: 2026-08-06 είναι Πέμπτη
    check("[13] ο δείκτης weekday() δείχνει τη σωστή ημέρα",
          greek_text.GREEK_DAYS[datetime(2026, 8, 6).weekday()] == "Πέμπτη",
          f"(got={greek_text.GREEK_DAYS[datetime(2026, 8, 6).weekday()]!r})")
    check("[13] ο δείκτης μήνα δείχνει τον σωστό μήνα",
          greek_text.GREEK_MONTHS_SHORT[8 - 1] == "Αυγ",
          f"(got={greek_text.GREEK_MONTHS_SHORT[8 - 1]!r})")

    if app is not None:
        dash = app.get_frame("DashboardPage")

        # (β) το popup ραντεβού: η γραμμή ημερομηνίας ξεκινά με ελληνική ημέρα
        def toplevels_of(page):
            return [w for w in page.winfo_children()
                    if isinstance(w, tk.Toplevel) and w.winfo_exists()]
        for w in toplevels_of(dash):
            try:
                w.grab_release()
            except tk.TclError:
                pass
            w.destroy()
        app.update()

        alive = Customer.get_all()[0]
        appt13 = Appointment(customer_id=alive.id, datetime="2026-08-06 10:00",
                             services="Κούρεμα", duration=40, notes="", id=999995)
        dash.show_appointment_popup(appt13, f"{alive.first_name} {alive.last_name}")
        app.update()
        opened = toplevels_of(dash)
        check("[13] setup — το popup άνοιξε", len(opened) == 1, f"({len(opened)})")
        if opened:
            date_line = [w.cget("text") for w in opened[0].winfo_children()
                         if w.winfo_class() == "Label"][0]
            check("[13] popup: η γραμμή ημερομηνίας είναι ΕΛΛΗΝΙΚΑ υπό ξένο locale",
                  date_line.startswith("Πέμπτη"), f"(got={date_line!r})")
            check("[13] popup: δεν εμφανίζεται αγγλικό όνομα ημέρας",
                  "Thursday" not in date_line, f"(got={date_line!r})")
            for w in opened:
                try:
                    w.grab_release()
                except tk.TclError:
                    pass
                w.destroy()
            app.update()

        # (γ) οι επικεφαλίδες του ημερολογίου, ξαναχτισμένες υπό το ξένο locale
        cal = None
        def walk(w):
            yield w
            for c in w.winfo_children():
                yield from walk(c)
        for w in walk(dash):
            if isinstance(w, gui.CalendarView):
                cal = w
                break
        check("[13] setup — βρέθηκε το CalendarView", cal is not None)
        if cal is not None:
            cal.build_grid(datetime(2026, 8, 6).date())
            app.update()
            month_txt = cal.lbl_month.cget("text")
            day_txts = [l.cget("text") for l in cal.day_labels]
            check("[13] ημερολόγιο: ο μήνας είναι ελληνικός υπό ξένο locale",
                  month_txt == "Αυγ", f"(got={month_txt!r})")
            check("[13] ημερολόγιο: οι ημέρες είναι ελληνικές υπό ξένο locale",
                  bool(day_txts) and all(is_greek(t) for t in day_txts),
                  f"(got={day_txts})")
            check("[13] ημερολόγιο: καμία αγγλική συντομογραφία ημέρας",
                  not any(t.split()[0] in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
                          for t in day_txts if t.split()),
                  f"(got={day_txts})")
            check("[13] ημερολόγιο: το αριθμητικό μέρος της ημέρας διατηρήθηκε",
                  all(t.split()[-1].isdigit() for t in day_txts if t.split()),
                  f"(got={day_txts})")

    # --- (δ) ΤΟ EMAIL ΤΟΥ ΠΕΛΑΤΗ: το χειρότερο σημείο, γιατί δεν φαίνεται στην οθόνη
    # του κομμωτηρίου. Το day_name μπαίνει ΚΑΙ στο HTML ΚΑΙ στο plain text σώμα.
    import emails_utils as _eu

    class _FakeSMTP:
        """Αντικαθιστά το smtplib.SMTP: πιάνει το μήνυμα ΧΩΡΙΣ δίκτυο και χωρίς credentials."""
        captured = []
        def __init__(self, *a, **k):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
        def starttls(self):
            pass
        def login(self, *a, **k):
            pass
        def send_message(self, msg):
            _FakeSMTP.captured.append(msg)

    _real_smtp = _eu.smtplib.SMTP
    _eu.smtplib.SMTP = _FakeSMTP
    try:
        _FakeSMTP.captured.clear()
        ok, info = _eu.EmailSender(email="a@b.gr", password="x").send_reminder(
            "pelatis@paradeigma.gr", "Ελένη Παπαδοπούλου", "2026-08-06 11:00", "Κούρεμα")
        check("[13] email: το μήνυμα χτίστηκε και «στάλθηκε» (χωρίς δίκτυο)",
              ok and len(_FakeSMTP.captured) == 1, f"(ok={ok}, info={info!r})")
    finally:
        _eu.smtplib.SMTP = _real_smtp

    if _FakeSMTP.captured:
        msg = _FakeSMTP.captured[0]
        bodies = {}
        for part in msg.walk():
            if part.get_content_maintype() == "text":
                bodies[part.get_content_subtype()] = part.get_payload(decode=True).decode("utf-8")
        check("[13] email: υπάρχουν και τα δύο σώματα (plain + html)",
              "plain" in bodies and "html" in bodies, f"(got={sorted(bodies)})")
        for kind in ("plain", "html"):
            body = bodies.get(kind, "")
            check(f"[13] email ({kind}): η ημέρα είναι ΕΛΛΗΝΙΚΑ υπό ξένο locale",
                  "Πέμπτη" in body, f"(απόσπασμα={body[body.find('Ημερομηνία'):][:60]!r})")
            check(f"[13] email ({kind}): δεν στέλνεται αγγλικό όνομα ημέρας",
                  "Thursday" not in body, f"(βρέθηκε 'Thursday' στο σώμα {kind})")
finally:
    _locale.setlocale(_locale.LC_TIME, _saved_locale)

# ---------------------------------------------------------------------------
# [14] CHARACTERIZATION: ο πίνακας ραντεβού της ShowClientPage.
# Κωδικοποιεί τη ΣΗΜΕΡΙΝΗ συμπεριφορά, ΜΑΖΙ με τα ελαττώματά της (χαμένο id, γέμισμα
# 10 γραμμών, φιλτράρισμα padding μέσω αποτυχίας strptime). Το commit 2 θα αλλάξει
# σκόπιμα μέρος από αυτά· εδώ απλώς καρφώνεται η αφετηρία.
# ---------------------------------------------------------------------------
print("\n[14] Characterization: πίνακας ραντεβού της ShowClientPage")

if app is not None:
    sp14 = app.get_frame("ShowClientPage")

    # --- δικά της fixtures: δικός της αριθμοδοτικός χώρος (6950000xx), δικές της ημέρες ---
    # Όλα τα ραντεβού στις 17:00 με διάρκεια 20', και ΞΕΧΩΡΙΣΤΗ ημέρα το καθένα, ώστε ούτε
    # μεταξύ τους να συγκρούονται ούτε με τα 10:00-11:20 της [1] αν πέσει ίδια ημερομηνία.
    TODAY_14 = datetime.today().date()
    APPT_TIME = "17:00"
    NOTE_MARK = "ΣΗΜΕΙΩΣΗ-ΜΟΝΑΔΙΚΗ-Ξ7Ψ"   # μοναδικό, για να έχει νόημα ο έλεγχος απουσίας

    def seed_appts(cust_id, offsets, service="Κούρεμα", notes=NOTE_MARK):
        made = []
        for off in offsets:
            d = TODAY_14 + timedelta(days=off)
            a = Appointment(cust_id, f"{d.isoformat()} {APPT_TIME}", service, 20, notes)
            a.save_to_db()
            made.append((off, d, a))
        return made

    cust_A = Customer("Καρτέλα", "Τριών", "6950000001", "kartela-a@paradeigma.gr")
    cust_A.save_to_db()
    cust_B = Customer("Μόνο", "Παρελθόν", "6950000002", "kartela-b@paradeigma.gr")
    cust_B.save_to_db()
    cust_C = Customer("Δώδεκα", "Ραντεβού", "6950000003", "kartela-c@paradeigma.gr")
    cust_C.save_to_db()
    check("[14] setup — δημιουργήθηκαν οι τρεις πελάτες-fixtures",
          all(c.id is not None for c in (cust_A, cust_B, cust_C)))

    # A: ένα παρελθοντικό, ένα ΣΗΜΕΡΑ, ένα μελλοντικό -> ασκεί το future branch
    seeded_A = seed_appts(cust_A.id, [-40, 0, 40])
    # B: ΜΟΝΟ παρελθοντικά -> ασκεί το past branch
    seeded_B = seed_appts(cust_B.id, [-70, -35])
    # C: 12 ραντεβού (6 παρελθόν, 6 μέλλον) -> n > 10, δηλαδή ΧΩΡΙΣ γέμισμα
    seeded_C = seed_appts(cust_C.id, [-6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6])
    check("[14] setup — αποθηκεύτηκαν 3 + 2 + 12 ραντεβού",
          all(a.id is not None for _o, _d, a in seeded_A + seeded_B + seeded_C)
          and (len(seeded_A), len(seeded_B), len(seeded_C)) == (3, 2, 12))

    def grid_cells(page):
        """(γραμμή, στήλη) -> κείμενο, διαβασμένο από τα ΠΡΑΓΜΑΤΙΚΑ widgets του grid."""
        cells = {}
        for w in page.scrollable_frame.winfo_children():
            info = w.grid_info()
            cells[(int(info["row"]), int(info["column"]))] = w.cget("text")
        return cells

    def grid_row_count(page):
        rows = {int(w.grid_info()["row"]) for w in page.scrollable_frame.winfo_children()}
        return (max(rows) + 1) if rows else 0

    # =========================================================================
    # (1) το σχήμα που επιστρέφει η get_appoints_from_id
    # =========================================================================
    rows_A = sp14.get_appoints_from_id(cust_A.id)
    check("[14.1] επιστρέφεται list", isinstance(rows_A, list), f"({type(rows_A).__name__})")
    check("[14.1] μία εγγραφή ανά ραντεβού", len(rows_A) == 3, f"(got={len(rows_A)})")
    # ΑΛΛΑΞΕ σε αυτό το commit: πριν επέστρεφε 3-tuples από strings οθόνης.
    check("[14.1] κάθε εγγραφή είναι αντικείμενο Appointment (ΟΧΙ tuple strings)",
          all(isinstance(r, Appointment) for r in rows_A),
          f"({[type(r).__name__ for r in rows_A]})")
    check("[14.1] σειρά datetime ASC",
          [r.datetime for r in rows_A] == sorted(r.datetime for r in rows_A),
          f"({[r.datetime for r in rows_A]})")
    expected_dts = [f"{d.isoformat()} {APPT_TIME}"
                    for _off, d, _a in sorted(seeded_A, key=lambda t: t[1])]
    check("[14.1] ακριβώς τα ραντεβού που σπάρθηκαν, στη σωστή σειρά",
          [r.datetime for r in rows_A] == expected_dts,
          f"(got={[r.datetime for r in rows_A]}, exp={expected_dts})")
    # Η ΜΟΡΦΟΠΟΙΗΣΗ έφυγε από εδώ: τα πεδία είναι ακατέργαστα, όπως στη βάση.
    check("[14.1] το datetime είναι ΑΚΑΤΕΡΓΑΣΤΟ '%Y-%m-%d %H:%M', όχι string οθόνης",
          all(len(r.datetime) == 16 and r.datetime[4] == "-" and r.datetime[13] == ":"
              for r in rows_A), f"({[r.datetime for r in rows_A]})")
    check("[14.1] το services μεταφέρεται ΑΥΤΟΥΣΙΟ",
          all(r.services == "Κούρεμα" for r in rows_A), f"({[r.services for r in rows_A]})")

    # =========================================================================
    # (2) ΤΑΥΤΟΤΗΤΑ: id, duration, notes, customer_id ΔΙΑΤΗΡΟΥΝΤΑΙ πλέον.
    #     Αντιστράφηκε σε αυτό το commit — πριν καρφωνόταν η ΑΠΟΥΣΙΑ τους.
    #     Κάθε ισχυρισμός έχει θετικό control στο ΙΔΙΟ fixture.
    # =========================================================================
    probe_off, probe_date, probe_appt = seeded_A[0]
    probe_row = rows_A[0]
    # POSITIVE CONTROL: η γραμμή αυτή ΟΝΤΩΣ αντιστοιχεί σε αυτό το ραντεβού
    check("[14.2] positive control: η γραμμή αντιστοιχεί στο ραντεβού που σπάρθηκε",
          probe_row.datetime == f"{probe_date.isoformat()} {APPT_TIME}",
          f"(row.datetime={probe_row.datetime!r})")
    check("[14.2] positive control: το ραντεβού ΕΧΕΙ id/duration/notes στη βάση",
          probe_appt.id is not None and probe_appt.duration == 20
          and probe_appt.notes == NOTE_MARK,
          f"(id={probe_appt.id}, dur={probe_appt.duration}, notes={probe_appt.notes!r})")

    check("[14.2] το id ΔΙΑΤΗΡΕΙΤΑΙ και ταιριάζει με το αποθηκευμένο",
          probe_row.id == probe_appt.id,
          f"(row={probe_row.id}, seeded={probe_appt.id})")
    check("[14.2] το duration ΔΙΑΤΗΡΕΙΤΑΙ",
          probe_row.duration == 20, f"(got={probe_row.duration!r})")
    check("[14.2] τα notes ΔΙΑΤΗΡΟΥΝΤΑΙ",
          probe_row.notes == NOTE_MARK, f"(got={probe_row.notes!r})")
    check("[14.2] το customer_id ΔΙΑΤΗΡΕΙΤΑΙ",
          probe_row.customer_id == cust_A.id,
          f"(row={probe_row.customer_id}, cust={cust_A.id})")
    check("[14.2] ΟΛΕΣ οι γραμμές έχουν μοναδικό, μη-None id "
          "(αυτό ήταν αδύνατο πριν το commit)",
          len({r.id for r in rows_A}) == len(rows_A)
          and all(r.id is not None for r in rows_A),
          f"(ids={[r.id for r in rows_A]})")

    # =========================================================================
    # (3)+(4)+(5) render με n < 10: γέμισμα, αντιστοίχιση γραμμών, items
    # =========================================================================
    sp14.customer_info(cust_A.id)
    app.update()
    n_A = len(seeded_A)

    # ΤΟ ΔΑΠΕΔΟ ΠΑΡΑΜΕΝΕΙ: ίδιες 10 ζωγραφισμένες γραμμές, όπως πριν.
    check("[14.3] με n<10 ζωγραφίζονται ΑΚΡΙΒΩΣ 10 γραμμές (αμετάβλητο)",
          grid_row_count(sp14) == 10, f"(got={grid_row_count(sp14)})")
    # ΑΛΛΑΞΕ: η appoints_list ΔΕΝ μεταλλάσσεται πλέον στις 10.
    check("[14.3] η appoints_list ΔΕΝ μεταλλάσσεται — μένει στα n πραγματικά",
          len(sp14.appoints_list) == n_A, f"(got={len(sp14.appoints_list)}, n={n_A})")
    check("[14.3] η appoints_list περιέχει ΜΟΝΟ Appointment, κανένα γέμισμα",
          all(isinstance(a, Appointment) for a in sp14.appoints_list),
          f"({[type(a).__name__ for a in sp14.appoints_list]})")
    check("[14.3] το γέμισμα υπάρχει ΜΟΝΟ ως widgets, όχι στα δεδομένα",
          grid_row_count(sp14) - len(sp14.appoints_list) == 10 - n_A,
          f"(grid={grid_row_count(sp14)}, data={len(sp14.appoints_list)})")

    cells_A = grid_cells(sp14)
    # (4) ΚΑΘΕ πραγματική γραμμή, όχι μόνο η πρώτη. Η μορφοποίηση γίνεται πλέον εδώ,
    # οπότε συγκρίνουμε το κείμενο του grid με το ΑΝΤΙΚΕΙΜΕΝΟ, μορφοποιημένο.
    def rendered(appt):
        dt = datetime.strptime(appt.datetime, "%Y-%m-%d %H:%M")
        return (dt.strftime("%d-%m-%Y"), dt.strftime("%H:%M"), appt.services)

    for i in range(n_A):
        check(f"[14.4] γραμμή {i} του grid == μορφοποιημένο appoints_list[{i}]",
              tuple(cells_A[(i, c)] for c in range(3)) == rendered(sp14.appoints_list[i]),
              f"(grid={tuple(cells_A[(i, c)] for c in range(3))}, "
              f"obj={rendered(sp14.appoints_list[i])})")
    for i in range(n_A, 10):
        check(f"[14.4] γραμμή {i} του grid είναι κενή (γέμισμα)",
              all(cells_A[(i, c)] == "" for c in range(3)),
              f"(got={tuple(cells_A[(i, c)] for c in range(3))})")

    # (4β) ΝΕΟ: ο χάρτης γραμμή -> Appointment λύνει σωστό id για ΚΑΘΕ πραγματική γραμμή
    for i in range(n_A):
        expected_appt = sorted(seeded_A, key=lambda t: t[1])[i][2]
        check(f"[14.4β] row_appointments[{i}] δίνει το ΣΩΣΤΟ id",
              sp14.row_appointments.get(i) is not None
              and sp14.row_appointments[i].id == expected_appt.id,
              f"(got={getattr(sp14.row_appointments.get(i), 'id', None)}, "
              f"exp={expected_appt.id})")
    check("[14.4β] ο χάρτης έχει ΑΚΡΙΒΩΣ n εγγραφές",
          len(sp14.row_appointments) == n_A, f"(got={len(sp14.row_appointments)})")
    for i in range(n_A, 10):
        check(f"[14.4β] η γραμμή-γέμισμα {i} ΔΕΝ λύνει σε ραντεβού",
              sp14.row_appointments.get(i) is None,
              f"(got={sp14.row_appointments.get(i)})")

    # (5) items: μόνο πραγματικές γραμμές
    check("[14.5] το items έχει μία εγγραφή ανά ΠΡΑΓΜΑΤΙΚΟ ραντεβού",
          len(sp14.items) == n_A, f"(got={len(sp14.items)})")
    expected_items_A = [(d, idx) for idx, (_o, d, _a)
                        in enumerate(sorted(seeded_A, key=lambda t: t[1]))]
    check("[14.5] το items είναι (date, row_index) στη σειρά του grid",
          sp14.items == expected_items_A, f"(got={sp14.items}, exp={expected_items_A})")
    check("[14.5] καμία γραμμή-γέμισμα δεν μπήκε στο items",
          all(idx < n_A for _d, idx in sp14.items), f"(got={sp14.items})")

    # =========================================================================
    # (6) find_best_matching_item: future branch (A) και past branch (B)
    # =========================================================================
    check("[14.6] FUTURE branch: στόχος = το πλησιέστερο ΜΗ παρελθοντικό (το σημερινό)",
          sp14.target_index == 1, f"(got={sp14.target_index})")
    check("[14.6] positive control: η γραμμή-στόχος είναι όντως η σημερινή",
          sp14.appoints_list[sp14.target_index].datetime.startswith(TODAY_14.isoformat()),
          f"(row={sp14.appoints_list[sp14.target_index].datetime!r})")

    # =========================================================================
    # (7) highlight_target_row: ΑΚΡΙΒΩΣ η γραμμή target_index
    # =========================================================================
    HL_BG, HL_FG = "#0560b6", "white"
    by_row = {}
    for w in sp14.scrollable_frame.winfo_children():
        by_row.setdefault(int(w.grid_info()["row"]), []).append(w)
    tgt = sp14.target_index
    check("[14.7] και οι 3 στήλες της γραμμής-στόχου έχουν χρώμα highlight",
          len(by_row[tgt]) == 3
          and all(str(w.cget("bg")) == HL_BG and str(w.cget("fg")) == HL_FG
                  for w in by_row[tgt]),
          f"(bg={[str(w.cget('bg')) for w in by_row[tgt]]})")
    check("[14.7] ΚΑΜΙΑ άλλη γραμμή δεν έχει το χρώμα highlight",
          all(str(w.cget("bg")) != HL_BG
              for r, ws in by_row.items() if r != tgt for w in ws),
          f"(highlighted rows={[r for r, ws in by_row.items() if any(str(w.cget('bg')) == HL_BG for w in ws)]})")

    # --- past branch, σε δικό του fixture ---
    sp14.customer_info(cust_B.id)
    app.update()
    check("[14.6] PAST branch: στόχος = το πλησιέστερο ΠΑΡΕΛΘΟΝΤΙΚΟ (το πιο πρόσφατο)",
          sp14.target_index == 1, f"(got={sp14.target_index})")
    check("[14.6] positive control: η γραμμή-στόχος είναι το πιο πρόσφατο παρελθοντικό",
          sp14.appoints_list[sp14.target_index].datetime.startswith(
              (TODAY_14 + timedelta(days=-35)).isoformat()),
          f"(row={sp14.appoints_list[sp14.target_index].datetime!r})")

    # =========================================================================
    # (8) ΚΑΤΑΓΡΑΦΗ (όχι έγκριση) του yview_moveto για n=3 και n=12
    # =========================================================================
    moves = []
    _real_moveto = sp14.canvas.yview_moveto
    sp14.canvas.yview_moveto = lambda f: moves.append(f)
    try:
        sp14.customer_info(cust_A.id)   # n = 3 -> γεμίζει στις 10
        app.update()
        moves.clear()
        sp14.scroll_to_target()
        moved_n3 = moves[-1] if moves else None
        tgt_n3 = sp14.target_index

        sp14.customer_info(cust_C.id)   # n = 12 -> ΧΩΡΙΣ γέμισμα
        app.update()
        n_C = len(sp14.appoints_list)
        tgt_n12 = sp14.target_index
        moves.clear()
        sp14.scroll_to_target()
        moved_n12 = moves[-1] if moves else None
    finally:
        sp14.canvas.yview_moveto = _real_moveto

    print(f"     ΚΑΤΑΓΡΑΦΗ n=3 : rows={10} target_index={tgt_n3} yview_moveto={moved_n3!r}")
    print(f"     ΚΑΤΑΓΡΑΦΗ n=12: rows={n_C} target_index={tgt_n12} yview_moveto={moved_n12!r}")
    # Καρφώνονται ΩΣ ΕΧΟΥΝ, χωρίς κρίση για το αν είναι σωστά — ώστε το commit 2 να
    # μπορεί να αποδείξει ότι δεν άλλαξαν.
    check("[14.8] n=3: 3 πραγματικά ραντεβού, 10 ζωγραφισμένες γραμμές",
          len(sp14.get_appoints_from_id(cust_A.id)) == 3, "(fixture άλλαξε;)")
    check("[14.8] n=3: yview_moveto(0.0) [καταγραφή, όχι έγκριση]",
          moved_n3 == 0.0, f"(got={moved_n3!r})")
    check("[14.8] n=12: ΚΑΜΙΑ γραμμή-γέμισμα (n > 10)",
          n_C == 12 and all(isinstance(r, Appointment) for r in sp14.appoints_list)
          and len(sp14.row_appointments) == 12,
          f"(rows={n_C}, map={len(sp14.row_appointments)})")
    check("[14.8] n=12: target_index=6 (πρώτο μελλοντικό) [καταγραφή]",
          tgt_n12 == 6, f"(got={tgt_n12})")
    check("[14.8] n=12: yview_moveto(2/12) [καταγραφή, όχι έγκριση]",
          moved_n12 == 2 / 12, f"(got={moved_n12!r})")
    check("[14.8] n=12: ζωγραφίστηκαν 12 γραμμές, όχι 10",
          grid_row_count(sp14) == 12, f"(got={grid_row_count(sp14)})")

# ---------------------------------------------------------------------------
if app is not None:
    app.destroy()
print(f"\nΑποτέλεσμα: {passed} πέρασαν, {failed} απέτυχαν")
sys.exit(1 if failed else 0)
