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
                    date TEXT NOT NULL,           -- Ημερομηνία
                    time TEXT NOT NULL,                 --και ώρα του ραντεβού
                    services TEXT NOT NULL,
                    duration NOT NULL DEFAULT 20,        -- Διάρκεια ραντεβού σε λεπτά
                    notes TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)  -- Σχέση με τον πίνακα πελατών
                 )''')
    conn.commit()
    conn.close()

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
                    conn.commit()
                    self.id = c.lastrowid
        except sqlite3.Error as e:
            raise e
        finally:
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

    @staticmethod
    def get_all():
        """
        Retrieve all customers with their full names.
        """
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()
                c.execute("SELECT first_name, last_name, phone, email, id FROM customers")
                customers = [Customer(first_name=row[0], last_name=row[1], phone=row[2], email=row[3], id=row[4]) for row in c.fetchall()]
                return customers
        except sqlite3.Error as e:
            print(f"Error fetching customers: {e}")
            return []
        finally:
            conn.close()
        
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
        # finally:
        #     conn.close()
            

class Appointment:
    def __init__(self, customer_id, date, time, services, duration=20, notes="", id=None):
        self.customer_id = customer_id
        self.date = date  # Εισάγει την ημερομηνία
        self.time = time  #ώρα 
        self.duration = duration
        self.services = services
        self.notes = notes
        self.id = id
        self.date_time = datetime.strptime(f"{self.date} {self.time}", "%Y-%m-%d %H:%M")
    
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
                            UPDATE appointments SET date = ?, time = ?, services = ?, duration = ?, notes = ?
                            WHERE id = ?
                        ''', (self.date, self.time, self.services, self.duration, self.notes, id))
                    else:
                        # Αν δεν υπάρχει, εισάγει νέο πελάτη
                        c.execute('''
                            INSERT INTO appointments (id, customer_id, date, time, services, duration, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (self.id, self.customer_id, self.date, self.time, self.services, self.duration, self.notes))
                        # conn.commit()
                        self.id = c.lastrowid
            except Exception as e:
                print(f"Error retrieving customer by ID: {e}")
                raise e
            # finally:
            #     conn.commit()
            #     conn.close()

    def check_for_overlap(self):
        conn = sqlite3.connect('salon_appointments.db')
        c = conn.cursor()
        start_time = self.date_time
        end_time = self.date_time + timedelta(minutes=self.duration)

        # Query for overlapping appointments
        c.execute('''
            SELECT * FROM appointments 
            WHERE (
                (datetime(date || ' ' || time) BETWEEN ? AND ?)
                OR (? BETWEEN datetime(date || ' ' || time) AND datetime(date || ' ' || time, '+' || duration || ' minutes'))
            )
        ''', (start_time.isoformat(), end_time.isoformat(), start_time.isoformat()))

        overlap = c.fetchone()  # This checks if there is any overlapping appointment
        conn.close()
        return overlap is not None


    @staticmethod
    def delete_from_db(appointment_id):
        # Διαγράφει ραντεβού από τη βάση δεδομένων βάσει του ID
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()
                c.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
        except sqlite3.Error as e:
            print(f"Σφάλμα διαγραφής ραντεβού: {e}")
        finally:
            conn.close()

    @staticmethod
    def get_by_date(date):
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM appointments WHERE date = ? ORDER BY time ASC", (date,))
                appointments = [Appointment(id=row[0], customer_id=row[1], date=row[2], time=row[3], services=row[4], duration=row[5], notes=row[6]) for row in c.fetchall()]
                return appointments
        except sqlite3.Error as e:
            print(f"Error fetching all appointments(get_by_date): {e}")
            return []
        finally:
            conn.close()
            

    # @staticmethod
    # def get_by_customer_id(customer_id):
    #     try:
    #         with sqlite3.connect('salon_appointments.db') as conn:
    #             c = conn.cursor()
    #             c.execute("SELECT customer_id, date, time, services, duration, notes, id FROM appointments WHERE customer_id = ? ORDER BY date ASC, time ASC", (customer_id,))
    #             appointments = c.fetchall()
    #             return [Appointment(customer_id=row[0], date=row[1], time=row[2], services=row[3], duration=row[4], notes=row[5], id=row[6]) for row in appointments]
    #     except sqlite3.Error as e:
    #         print(f"Error fetching all appointments(get_by_patient_id): {e}")
    #         return []
    #     finally:
    #         conn.close()

    @staticmethod
    def get_all():
        """
        Retrieve all appointments.
        """
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()
                c.execute("SELECT id, customer_id, date, time, services, duration, notes FROM appointments ORDER BY date ASC, time ASC")
                appointments = [Appointment(row[1], row[2], row[3], row[4], row[5], row[6], id=row[0]) for row in c.fetchall()]
                return appointments
        except sqlite3.Error as e:
            print(f"Error fetching all appointments: {e}")
            return []
        finally:
            conn.close()


## Σημειώσεις

