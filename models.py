# Classes
import sqlite3
from datetime import datetime, timedelta

# Συνάρτηση ρύθμισης της βάσης δεδομένων 
def setup_database():
    # Συνδέεται με τη βάση δεδομένων SQLite ή τη δημιουργεί εάν δεν υπάρχει
    conn = sqlite3.connect('salon_appointments.db')
    c = conn.cursor()
    
    # Δημιουργία του πίνακα για πελάτες αν δεν υπάρχει ήδη
    c.execute('''CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY,  -- Πρωτεύων κλειδί για μοναδική ταυτοποίηση
                    first_name TEXT NOT NULL,  -- Όνομα πελάτη
                    last_name TEXT NOT NULL,   -- Επίθετο πελάτη
                    phone TEXT NOT NULL UNIQUE, -- Τηλέφωνο, μοναδικό για κάθε πελάτη
                    email TEXT NOT NULL UNIQUE  -- Email, μοναδικό για κάθε πελάτη
                 )''')

    # Δημιουργία του πίνακα για ραντεβού αν δεν υπάρχει ήδη
    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY NOT NULL,  -- Πρωτεύων κλειδί για μοναδική ταυτοποίηση
                    customer_id INTEGER NOT NULL,     -- Αναφορά στο ID του πελάτη
                    date_time TEXT NOT NULL,          -- Ημερομηνία και ώρα του ραντεβού
                    duration INTEGER NOT NULL,        -- Διάρκεια ραντεβού σε λεπτά
                    FOREIGN KEY (customer_id) REFERENCES customers (id)  -- Σχέση με τον πίνακα πελατών
                 )''')
    conn.commit()
    conn.close()

class Customer:
    def __init__(self, first_name, last_name, phone, email):
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.email = email

    def save_to_db(self):
    # Αποθηκεύει ή ενημερώνει τον πελάτη στη βάση δεδομένων βάσει του id
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()

                # Ελέγχει αν υπάρχει πελάτης με το συγκεκριμένο id
                c.execute('SELECT * FROM customers WHERE id = ?', (self.id,))
                existing_customer = c.fetchone()

                if existing_customer:
                    # Αν υπάρχει, ενημερώνει τα στοιχεία
                    c.execute('''
                        UPDATE customers SET first_name = ?, last_name = ?, phone = ?, email = ?
                        WHERE id = ?
                    ''', (self.first_name, self.last_name, self.phone, self.email, self.id))
                else:
                    # Αν δεν υπάρχει, εισάγει νέο πελάτη
                    c.execute('''
                        INSERT INTO customers (id, first_name, last_name, phone, email)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (self.id, self.first_name, self.last_name, self.phone, self.email))
        except sqlite3.Error as e:
            raise e


    @staticmethod
    def delete_from_db(phone):
        # Διαγράφει πελάτη από τη βάση δεδομένων βάσει του τηλεφώνου
        conn = sqlite3.connect('salon_appointments.db')
        c = conn.cursor()
        c.execute('DELETE FROM customers WHERE phone = ?', (phone,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_all():
        """
        Retrieve all patients with their full names.
        """
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()
                c.execute("SELECT first_name, last_name, phone, email FROM customers")
                patients = [Customer(first_name=row[0], last_name=row[1], phone=row[2], email=row[3]) for row in c.fetchall()]
                return patients
        except sqlite3.Error as e:
            print(f"Error fetching patients: {e}")
            return []

class Appointment:
    def __init__(self, customer_id, date_time, duration=20):
        self.customer_id = customer_id
        self.date_time = date_time  # Εισάγει την ημερομηνία/ώρα ως datetime object
        self.duration = duration

    def save_to_db(self):
    # Αποθηκεύει ή ενημερώνει τον πελάτη στη βάση δεδομένων βάσει του id
            try:
                with sqlite3.connect('salon_appointments.db') as conn:
                    c = conn.cursor()

                    # Ελέγχει αν υπάρχει πελάτης με το συγκεκριμένο id
                    c.execute('SELECT * FROM customers WHERE id = ?', (self.id,))
                    existing_customer = c.fetchone()

                    if existing_customer:
                        # Αν υπάρχει, ενημερώνει τα στοιχεία
                        c.execute('''
                            UPDATE customers SET first_name = ?, last_name = ?, phone = ?, email = ?
                            WHERE id = ?
                        ''', (self.first_name, self.last_name, self.phone, self.email, self.id))
                    else:
                        # Αν δεν υπάρχει, εισάγει νέο πελάτη
                        c.execute('''
                            INSERT INTO customers (id, first_name, last_name, phone, email)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (self.id, self.first_name, self.last_name, self.phone, self.email))
            except sqlite3.Error as e:
                raise e

    def check_for_overlap(self):
        # Ελέγχει για επικαλύψεις με ήδη υπάρχοντα ραντεβού
        conn = sqlite3.connect('salon_appointments.db')
        c = conn.cursor()
        start_time = self.date_time
        end_time = self.date_time + timedelta(minutes=self.duration)
        
        # Ερώτημα για ανεύρεση επικαλυπτόμενων ραντεβού
        c.execute('''SELECT * FROM appointments WHERE (
                        (date_time BETWEEN ? AND ?) OR
                        (? BETWEEN date_time AND datetime(date_time, '+' || duration || ' minutes'))
                     )''', (start_time.isoformat(), end_time.isoformat(), start_time.isoformat()))
        
        overlap = c.fetchone()  # Επιστρέφει το πρώτο επικαλυπτόμενο ραντεβού αν υπάρχει
        conn.close()
        return overlap is not None

    @staticmethod
    def delete_from_db(appointment_id):
        # Διαγράφει ραντεβού από τη βάση δεδομένων βάσει του ID
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()
                c.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Σφάλμα διαγραφής ραντεβού: {e}")


## Σημειώσεις

# Το σφάλμα database is locked στη SQLite σημαίνει ότι κάποια σύνδεση (ή cursor) δεν έχει κλείσει σωστά ή έχει μείνει ανοιχτή λόγω προηγούμενου σφάλματος. Αν δεν την απελευθερώσεις (ή κάνεις rollback), η βάση παραμένει κλειδωμένη και δεν επιτρέπει νέες εγγραφές.

# 1. Πάντα να χρησιμοποιείς with για τις συνδέσεις στη SQLite

# def save_to_db(self):
#     try:
#         with sqlite3.connect("mydb.db") as conn:
#             cursor = conn.cursor()
#             cursor.execute(
#                 "INSERT INTO customers (first_name, last_name, phone, email) VALUES (?, ?, ?, ?)",
#                 (self.first_name, self.last_name, self.phone, self.email)
#             )
#     except sqlite3.Error as e:
#         raise e

# ✅ Άρα χρειάζομαι conn.commit();

# Μέσα σε with → ✨ Όχι, δεν χρειάζεται. Το κάνει μόνο του στο τέλος.
# Χωρίς with → ✅ Ναι, είναι υποχρεωτικό. Χωρίς αυτό, τίποτα δεν αποθηκεύεται

