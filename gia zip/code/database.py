import sqlite3
# from datetime import datetime, timedelta

# Συνάρτηση ρύθμισης της βάσης δεδομένων 
def setup_database():
    # Συνδέεται με τη βάση δεδομένων SQLite ή τη δημιουργεί εάν δεν υπάρχει
    conn = sqlite3.connect('salon_appointments.db')
    c = conn.cursor()
    
    # Δημιουργία του πίνακα για πελάτες αν δεν υπάρχει ήδη
    c.execute('''CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Πρωτεύων κλειδί για μοναδική ταυτοποίηση
                    first_name TEXT NOT NULL,  -- Όνομα πελάτη
                    last_name TEXT NOT NULL,   -- Επίθετο πελάτη
                    phone TEXT NOT NULL UNIQUE, -- Τηλέφωνο, μοναδικό για κάθε πελάτη
                    email TEXT NOT NULL UNIQUE  -- Email, μοναδικό για κάθε πελάτη
                 )''')

    # Δημιουργία του πίνακα για ραντεβού αν δεν υπάρχει ήδη
    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Πρωτεύων κλειδί για μοναδική ταυτοποίηση
                    customer_id INTEGER NOT NULL,     -- Αναφορά στο ID του πελάτη    
                    datetime TEXT NOT NULL,         -- Ημερομηνία και ώρα του ραντεβού
                    services TEXT NOT NULL,
                    duration INTEGER NOT NULL DEFAULT 20,        -- Διάρκεια ραντεβού σε λεπτά
                    notes TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)  -- Σχέση με τον πίνακα πελατών
                 )''')
    conn.commit()
    conn.close()
