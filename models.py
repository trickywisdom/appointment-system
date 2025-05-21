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
                    id INTEGER PRIMARY KEY,  # Πρωτεύων κλειδί για μοναδική ταυτοποίηση
                    first_name TEXT NOT NULL,  # Όνομα πελάτη
                    last_name TEXT NOT NULL,   # Επίθετο πελάτη
                    phone TEXT NOT NULL UNIQUE, # Τηλέφωνο, μοναδικό για κάθε πελάτη
                    email TEXT NOT NULL UNIQUE  # Email, μοναδικό για κάθε πελάτη
                 )''')

    # Δημιουργία του πίνακα για ραντεβού αν δεν υπάρχει ήδη
    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY,  # Πρωτεύων κλειδί για μοναδική ταυτοποίηση
                    customer_id INTEGER,     # Αναφορά στο ID του πελάτη
                    date_time TEXT,          # Ημερομηνία και ώρα του ραντεβού
                    duration INTEGER,        # Διάρκεια ραντεβού σε λεπτά
                    FOREIGN KEY (customer_id) REFERENCES customers (id)  # Σχέση με τον πίνακα πελατών
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
        # Αποθηκεύει τον πελάτη στη βάση δεδομένων
        conn = sqlite3.connect('salon_appointments.db')
        c = conn.cursor()
        c.execute('INSERT INTO customers (first_name, last_name, phone, email) VALUES (?, ?, ?, ?)',
                  (self.first_name, self.last_name, self.phone, self.email))
        conn.commit()
        conn.close()

    @staticmethod
    def delete_from_db(phone):
        # Διαγράφει πελάτη από τη βάση δεδομένων βάσει του τηλεφώνου
        conn = sqlite3.connect('salon_appointments.db')
        c = conn.cursor()
        c.execute('DELETE FROM customers WHERE phone = ?', (phone,))
        conn.commit()
        conn.close()

class Appointment:
    def __init__(self, customer_id, date_time, duration=20):
        self.customer_id = customer_id
        self.date_time = date_time  # Εισάγει την ημερομηνία/ώρα ως datetime object
        self.duration = duration

    def save_to_db(self):
        # Αποθηκεύει το ραντεβού στη βάση δεδομένων εάν δεν υπάρχει σύγκρουση
        if not self.check_for_overlap():
            conn = sqlite3.connect('salon_appointments.db')
            c = conn.cursor()
            c.execute('INSERT INTO appointments (customer_id, date_time, duration) VALUES (?, ?, ?)',
                      (self.customer_id, self.date_time.isoformat(), self.duration))
            conn.commit()
            conn.close()
        else:
            print("Δεν είναι δυνατή η κράτηση επικαλυπτόμενων ραντεβού.")

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
        conn = sqlite

