# Classes
import sqlite3
from datetime import datetime, timedelta
# import re # regurar expressions

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
    
# TODO Customer
class Customer:
    def __init__(self, first_name, last_name, phone, email, id=None):
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.email = email
        self.id = id

    def save_to_db(self, id=None):
    # Αποθηκεύει ή ενημερώνει τον πελάτη στη βάση δεδομένων βάσει του id    
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()

                # Ελέγχει αν υπάρχει πελάτης με το συγκεκριμένο id
                c.execute('SELECT * FROM customers WHERE id = ?', (id,))
                existing_customer = c.fetchone()

                if existing_customer:
                    # Αν υπάρχει, ενημερώνει τα στοιχεία
                    c.execute('''
                        UPDATE customers SET first_name = ?, last_name = ?, phone = ?, email = ?
                        WHERE id = ?
                    ''', (self.first_name, self.last_name, self.phone, self.email, id))
                else:
                    # Αν δεν υπάρχει, εισάγει νέο πελάτη
                    c.execute('''
                        INSERT INTO customers (id, first_name, last_name, phone, email)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (self.id, self.first_name, self.last_name, self.phone, self.email))
                    self.id = c.lastrowid
        except sqlite3.Error as e:
            raise e
        
    @staticmethod
    def delete_from_db(phone):
        #Συνδεση στο databse
        conn = sqlite3.connect('salon_appointments.db')
        c = conn.cursor()
        try:
            # Ευρεση του customer ID βάση αριθμού τηλεφώνου
            c.execute('SELECT id FROM customers WHERE phone = ?', (phone,))
            result = c.fetchone()
            if result:
                customer_id = result[0]
                # Διαγραφή όλων των ραντεβού του πελάτη πρώτα
                c.execute('DELETE FROM appointments WHERE customer_id = ?', (customer_id,))
            # Διαγραφη του πελάτη
            c.execute('DELETE FROM customers WHERE phone = ?', (phone,))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error deleting customer and appointments: {e}")
        finally:
            conn.close()

    @staticmethod
    def get_all():
        """
        Retrieve all customers with their full names.
        """
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()
                c.execute("SELECT first_name, last_name, phone, email, id FROM customers ORDER BY last_name ASC")
                customers = [Customer(first_name=row[0], last_name=row[1], phone=row[2], email=row[3], id=row[4]) for row in c.fetchall()]
                return customers
        except sqlite3.Error as e:
            print(f"Error fetching customers: {e}")
            return []
        
    @classmethod
    def get_name_by_id(self, customer_id):
        """
        Retrieve a customers full name by their customer ID.
        """
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()
                c.execute("SELECT first_name, last_name FROM customers WHERE id = ?", (customer_id,))
                result = c.fetchone()
            
            if result:
                return f"{result[0]} {result[1]}"
            return ""
        except Exception as e:
            print(f"Error retrieving customer by ID: {e}")
            return None
            
# TODO Appointment
class Appointment:
    def __init__(self, customer_id, datetime, services, duration=20, notes="", id=None,
                 customer_name=None, customer_phone=None, customer_email=None):
        self.customer_id = customer_id
        self.datetime = datetime  # Εισάγει την ημερομηνία-ώρα
        self.duration = duration
        self.services = services
        self.notes = notes
        self.id = id
        self.customer_name = customer_name
        self.customer_phone= customer_phone 
        self.customer_email= customer_email

    def save_to_db(self, id=None):
    # Αποθηκεύει ή ενημερώνει το ραντεβού στη βάση δεδομένων βάσει του id
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()

                # Ελέγχει αν υπάρχει ραντεβού με το συγκεκριμένο id
                c.execute('SELECT * FROM appointments WHERE id = ?', (id,))
                existing_appointment = c.fetchone()

                if existing_appointment:
                    # Αν υπάρχει, ενημερώνει τα στοιχεία
                    c.execute('''
                        UPDATE appointments SET datetime = ?, services = ?, duration = ?, notes = ?
                        WHERE id = ?
                    ''', (self.datetime, self.services, self.duration, self.notes, id))
                else:
                    # Αν δεν υπάρχει, εισάγει νέο πελάτη
                    c.execute('''
                        INSERT INTO appointments (id, customer_id, datetime, services, duration, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (self.id, self.customer_id, self.datetime, self.services, self.duration, self.notes))
                    self.id = c.lastrowid
        except Exception as e:
            print(f"Error retrieving customer by ID: {e}")
            raise e
        
    @staticmethod
    def delete_from_db(phone):
        #Συνδεση στο databse
        conn = sqlite3.connect('salon_appointments.db')
        c = conn.cursor()
        try:
            # Ευρεση του customer ID βάση αριθμού τηλεφώνου
            c.execute('SELECT id FROM customers WHERE phone = ?', (phone,))
            result = c.fetchone()
            if result:
                customer_id = result[0]
                # Διαγραφή όλων των ραντεβού του πελάτη πρώτα
                c.execute('DELETE FROM appointments WHERE customer_id = ?', (customer_id,))
            # Διαγραφη του πελάτη
            c.execute('DELETE FROM customers WHERE phone = ?', (phone,))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error deleting customer and appointments: {e}")
        finally:
            conn.close()


    # @staticmethod
    # def delete_from_db(appointment_id):
    #     # Διαγράφει ραντεβού από τη βάση δεδομένων βάσει του ID
    #     try:
    #         with sqlite3.connect('salon_appointments.db') as conn:
    #             c = conn.cursor()
    #             c.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
    #             return c.rowcount > 0  # True αν διαγράφηκε έστω 1 γραμμή
    #     except sqlite3.Error as e:
    #         print(f"Σφάλμα διαγραφής ραντεβού στη βάση: {e}")
    #         return False
        
        
    @staticmethod
    def get_by_date(date):
        """Επιστρέφει όλα τα ραντεβού μιας συγκεκριμένης ημέρας"""
        with sqlite3.connect('salon_appointments.db') as conn:
            c = conn.cursor()
            
            c.execute('''SELECT a.*, c.first_name, c.last_name, c.phone, c.email
                        FROM appointments a
                        JOIN customers c ON a.customer_id = c.id
                        WHERE date(a.datetime) = date(?)
                        ORDER BY a.datetime ASC''', (date,))
            
            appointments = []
            for row in c.fetchall():
                appt = Appointment(
                    customer_id=row[1],
                    datetime=row[2],
                    duration=row[4],
                    services=row[3],
                    notes=row[5],
                    id=row[0]
                )
                # Προσθήκη στοιχείων πελάτη
                appt.customer_name = f"{row[6]} {row[7]}"
                appt.customer_phone = row[8]
                appt.customer_email = row[9]
                appointments.append(appt)
            
            return appointments
            

    @staticmethod
    def get_by_customer_id(customer_id):
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()
                c.execute("SELECT customer_id, datetime, services, duration, notes, id FROM appointments WHERE customer_id = ? ORDER BY datetime ASC", (customer_id,))
                appointments = c.fetchall()
                return [Appointment(customer_id=row[0], datetime=row[1], services=row[2], duration=row[3], notes=row[4], id=row[5]) for row in appointments]  # Correct Mapping
        except sqlite3.Error as e:
            print(f"Error fetching all appointments(get_by_customer_id): {e}")
            return []

    @staticmethod
    def get_all():
        """
        Retrieve all appointments.
        """
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()
                c.execute("SELECT id, customer_id, datetime, services, duration, notes FROM appointments ORDER BY date ASC, time ASC")
                appointments = [Appointment(row[1], row[2], row[3], row[4], row[5], id=row[0]) for row in c.fetchall()]
                return appointments
        except sqlite3.Error as e:
            print(f"Error fetching all appointments: {e}")
            return []


## Σημειώσεις

