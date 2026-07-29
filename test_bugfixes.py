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
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

workdir = tempfile.mkdtemp(prefix="appt_test_")
os.chdir(workdir)

import database
from models import Customer, Appointment, AppointmentOverlapError

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

    # (query, mode, αναμενόμενο για listbox σελίδες, αναμενόμενο για ClientsPage)
    QUERIES = [
        # κενός όρος -> εμφανίζονται όλοι
        ("",                    "count",    None,                        None),
        # POSITIVE CONTROL: το επώνυμο ακριβώς όπως είναι αποθηκευμένο
        ("παπαδοπούλου",        "equals",   (" Ελένη Παπαδοπούλου",),    ["Παπαδοπούλου"]),
        # χωρίς τόνο -> δεν βρίσκει (ευαισθησία σε τόνους)
        ("παπαδοπουλου",        "equals",   NOT_FOUND,                   []),
        # κεφαλαία -> δεν βρίσκει (το .lower() των κεφαλαίων χάνει τον τόνο)
        ("ΠΑΠΑΔΟΠΟΥΛΟΥ",        "equals",   NOT_FOUND,                   []),
        # μικρό όνομα -> δεν ψάχνεται
        ("ελένη",               "equals",   NOT_FOUND,                   []),
        # email -> δεν ψάχνεται
        ("paradeigma",          "equals",   NOT_FOUND,                   []),
        # πλήρες ονοματεπώνυμο -> δεν ψάχνεται
        ("Ελένη Παπαδοπούλου",  "equals",   NOT_FOUND,                   []),
        # τηλέφωνο ακριβώς -> βρίσκει
        ("6971234567",          "equals",   (" Ελένη Παπαδοπούλου",),    ["Παπαδοπούλου"]),
        # τμήμα τηλεφώνου -> βρίσκει
        ("697123",              "contains", (" Ελένη Παπαδοπούλου",),    ["Παπαδοπούλου"]),
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

# ---------------------------------------------------------------------------
if app is not None:
    app.destroy()
print(f"\nΑποτέλεσμα: {passed} πέρασαν, {failed} απέτυχαν")
sys.exit(1 if failed else 0)
