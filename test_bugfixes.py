# -*- coding: utf-8 -*-
"""
Επιβεβαίωση για τα δύο bug fixes:
  1) Έλεγχος επικάλυψης ραντεβού κατά την αποθήκευση (απόρριψη double-booking)
  2) Η επιλογή κλειστής ημέρας (Κυριακή/Δευτέρα) δεν κρασάρει πλέον την εφαρμογή

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
page.current_customer_id = cust_id
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
root.destroy()
print(f"\nΑποτέλεσμα: {passed} πέρασαν, {failed} απέτυχαν")
sys.exit(1 if failed else 0)
