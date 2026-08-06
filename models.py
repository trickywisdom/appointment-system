
import re
import sqlite3
import unicodedata
from datetime import datetime, timedelta


class AppointmentOverlapError(Exception):
    """Σφάλμα όταν ένα ραντεβού επικαλύπτεται χρονικά με υπάρχον ραντεβού"""
    pass


class CustomerValidationError(Exception):
    """Σφάλμα όταν τα στοιχεία επικοινωνίας του πελάτη δεν έχουν έγκυρη μορφή"""
    pass


# Ελληνικό κινητό: ΑΚΡΙΒΩΣ 10 ψηφία με πρόθεμα 69. Χωρίς διεθνές πρόθεμα και χωρίς
# σταθερά — ο αριθμός χρησιμεύει για υπενθυμίσεις, οπότε δεχόμαστε μόνο κινητά.
_PHONE_RE = re.compile(r"^69\d{8}$")
# Πρακτικός έλεγχος email (ΟΧΙ πλήρες RFC 5322): local@domain.tld, χωρίς κενά,
# ακριβώς ένα @, και domain που τελειώνει σε κατάληξη 2+ γραμμάτων.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)*\.[A-Za-z]{2,}$")


def normalize_phone(phone):
    """Αφαιρεί ΟΛΑ τα κενά και τις παύλες: «691 000 0001» και «691-000-0001» δίνουν
    και τα δύο «6910000001». Αυτή είναι η μορφή που ελέγχεται ΚΑΙ αποθηκεύεται, ώστε
    η αναζήτηση τηλεφώνου (που συγκρίνει ακατέργαστα) να βρίσκει πάντα τον πελάτη."""
    return re.sub(r"[\s-]", "", phone or "")


def normalize_email(email):
    """Μόνο περικοπή άκρων. Τα εσωτερικά κενά ΔΕΝ αφαιρούνται: ένα email με κενό μέσα
    είναι λάθος του χρήστη και πρέπει να απορριφθεί, όχι να «διορθωθεί» σιωπηλά."""
    return (email or "").strip()


def validate_phone(phone, typed=None):
    """Μήνυμα σφάλματος αν το τηλέφωνο δεν έχει έγκυρη μορφή, αλλιώς None.
    Ο έλεγχος γίνεται στην κανονικοποιημένη τιμή, αλλά το μήνυμα δείχνει το `typed`,
    δηλαδή ό,τι πληκτρολόγησε ο χρήστης."""
    value = normalize_phone(phone)
    shown = (typed if typed is not None else phone) or ""
    if not value:
        return "Το τηλέφωνο είναι υποχρεωτικό."
    if not _PHONE_RE.match(value):
        return (f"Μη έγκυρο τηλέφωνο: «{shown}». Το τηλέφωνο πρέπει να έχει 10 ψηφία "
                f"και να ξεκινά με 69.")
    return None


def validate_email(email, typed=None):
    """Μήνυμα σφάλματος αν το email δεν έχει έγκυρη μορφή, αλλιώς None.
    Ίδια λογική με το validate_phone για το `typed`."""
    value = normalize_email(email)
    shown = (typed if typed is not None else email) or ""
    if not value:
        return "Το email είναι υποχρεωτικό."
    if not _EMAIL_RE.match(value):
        return (f"Μη έγκυρη διεύθυνση email: «{shown}». Χρειάζεται μορφή "
                f"όνομα@παροχέας.κατάληξη.")
    return None


def _normalize(s):
    """Πεζά, χωρίς τόνους — για σύγκριση ελληνικών ονομάτων."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.casefold()


class Customer:
    def __init__(self, first_name, last_name, phone, email, id=None):
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.email = email
        self.id = id

    def normalize(self):
        """Κανονικοποιεί ΕΠΙ ΤΟΠΟΥ τηλέφωνο/email και επιστρέφει τις τιμές όπως δόθηκαν.
        ΔΕΝ καλείται από την __init__: η Customer φτιάχνεται και από διαβάσματα της βάσης,
        και δεν θέλουμε να ξαναγράφονται σιωπηλά τιμές που κανείς δεν ζήτησε να αλλάξουν."""
        typed = (self.phone, self.email)
        self.phone = normalize_phone(self.phone)
        self.email = normalize_email(self.email)
        return typed

    def validate(self, typed_phone=None, typed_email=None):
        """Ελέγχει τη μορφή τηλεφώνου/email. Αναφέρει ΟΛΑ τα προβλήματα μαζί, ώστε ο
        χρήστης να μη διορθώνει ένα-ένα πεδίο σε διαδοχικά μηνύματα. Τα typed_* είναι
        ό,τι πληκτρολογήθηκε πριν την κανονικοποίηση και μπαίνουν στα μηνύματα."""
        problems = [msg for msg in (validate_phone(self.phone, typed_phone),
                                    validate_email(self.email, typed_email)) if msg]
        if problems:
            raise CustomerValidationError("\n".join(problems))

    def save_to_db(self, id=None):
    # Αποθηκεύει ή ενημερώνει τον πελάτη στη βάση δεδομένων βάσει του id
        # Κανονικοποίηση ΠΡΙΝ τον έλεγχο, ώστε αυτό που αποθηκεύεται να είναι ακριβώς
        # αυτό που ελέγχθηκε — αλλιώς το «  6910000006  » περνούσε τον έλεγχο και
        # αποθηκευόταν ΜΕ τα κενά. Έλεγχος μορφής στο μοναδικό σημείο εγγραφής πελάτη,
        # ίδιο μοτίβο με τον έλεγχο επικάλυψης της Appointment.save_to_db, και ισχύει
        # και για INSERT και για UPDATE.
        typed_phone, typed_email = self.normalize()
        self.validate(typed_phone, typed_email)
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
        except sqlite3.IntegrityError as e:
            # ΠΡΟΣΟΧΗ ΣΤΗ ΣΕΙΡΑ: το IntegrityError είναι υποκλάση του sqlite3.Error, οπότε
            # ΠΡΕΠΕΙ να πιάνεται ΠΡΙΝ από το γενικό except παρακάτω. Αν μπει από κάτω, το
            # γενικό το αρπάζει πρώτο και το ωμό αγγλικό κείμενο του sqlite
            # («UNIQUE constraint failed: customers.email») φτάνει στον χρήστη.
            reason = str(e)
            if "customers.phone" in reason:
                raise CustomerValidationError(
                    f"Υπάρχει ήδη πελάτης με αυτό το τηλέφωνο: «{self.phone}»."
                ) from e
            if "customers.email" in reason:
                raise CustomerValidationError(
                    f"Υπάρχει ήδη πελάτης με αυτό το email: «{self.email}»."
                ) from e
            # Άγνωστη σύγκρουση: γενικό ελληνικό μήνυμα αντί για διαρροή του ωμού κειμένου.
            raise CustomerValidationError(
                "Υπάρχει ήδη πελάτης με αυτά τα στοιχεία."
            ) from e
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
#Εύρεση του ονοματεπώνυμου πελάτη με βάση το ID του
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
        
    @classmethod
    def get_customer_by_id(self, customer_id):
#Εύερση όλων των στοιχείων του πελάτη μέσω του id του
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()
                c.execute("SELECT first_name, last_name, phone, email, id FROM customers WHERE id = ?", (customer_id,))
                result = c.fetchone()
                if result:
                        customer = Customer(first_name=result[0], last_name=result[1], phone=result[2], email=result[3], id=result[4])
                        return customer
                else:
                    customer = None
                    return customer
        except Exception as e:
            print(f"Error retrieving customer by ID: {e}")
            return None

    @staticmethod
    def matches(customer, term):
        """Έλεγχος αν ένας πελάτης ταιριάζει με τον όρο αναζήτησης.
        Ψάχνει σε όνομα, επώνυμο, τηλέφωνο και email, χωρίς ευαισθησία σε
        τόνους ή πεζά/κεφαλαία. Όροι με κενά (π.χ. ονοματεπώνυμο) σπάνε σε
        λέξεις και ΟΛΕΣ πρέπει να ταιριάζουν κάπου."""
        fields = [
            _normalize(customer.first_name),
            _normalize(customer.last_name),
            customer.phone or "",
            _normalize(customer.email),
        ]
        tokens = _normalize(term).split()
        return all(any(tok in f for f in fields) for tok in tokens)

    @staticmethod
    def search(term):
        """Επιστρέφει τους πελάτες που ταιριάζουν με τον όρο αναζήτησης."""
        return [c for c in Customer.get_all() if Customer.matches(c, term)]


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
        # Έλεγχος επικάλυψης πριν την αποθήκευση. Το id εξαιρείται από τον έλεγχο,
        # ώστε το update ενός ραντεβού να μην συγκρούεται με τον παλιό εαυτό του.
        conflict = Appointment.find_overlap(self.datetime, self.duration, exclude_id=id)
        if conflict:
            start_dt = datetime.strptime(conflict.datetime, "%Y-%m-%d %H:%M")
            end_dt = start_dt + timedelta(minutes=int(conflict.duration))
            raise AppointmentOverlapError(
                f"Η ώρα είναι κατειλημμένη: υπάρχει ήδη ραντεβού "
                f"{start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')} ({conflict.customer_name})."
            )
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()

                # Ελέγχει αν υπάρχει ραντεβού με το συγκεκριμένο id
                c.execute('SELECT * FROM appointments WHERE id = ?', (id,))
                existing_appointment = c.fetchone()

                if existing_appointment:
                    # Αν υπάρχει, ενημερώνει τα στοιχεία
                    c.execute('''
                        UPDATE appointments SET customer_id = ?, datetime = ?, services = ?, duration = ?, notes = ?
                        WHERE id = ?
                    ''', (self.customer_id, self.datetime, self.services, self.duration, self.notes, id))
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
    def find_overlap(datetime_str, duration, exclude_id=None):
        """
        Ελέγχει αν το διάστημα [datetime_str, datetime_str + duration) επικαλύπτεται
        με υπάρχον ραντεβού της ίδιας ημέρας. Επιστρέφει το πρώτο ραντεβού που
        επικαλύπτεται, αλλιώς None. Το exclude_id εξαιρεί ένα ραντεβού από τον
        έλεγχο (χρήσιμο κατά το update, για να μην συγκρούεται με τον εαυτό του).
        """
        new_start = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        new_end = new_start + timedelta(minutes=int(duration))

        for appt in Appointment.get_by_date(new_start.date().isoformat()):
            if exclude_id is not None and appt.id == exclude_id:
                continue
            start = datetime.strptime(appt.datetime, "%Y-%m-%d %H:%M")
            end = start + timedelta(minutes=int(appt.duration))
            # Δύο διαστήματα επικαλύπτονται όταν το καθένα ξεκινά πριν τελειώσει το άλλο
            if new_start < end and start < new_end:
                return appt
        return None

    @staticmethod
    def delete_from_db(appointment_id):
        # Διαγράφει ραντεβού από τη βάση δεδομένων βάσει του ID
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()
                c.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
                return c.rowcount > 0  # True αν διαγράφηκε έστω 1 γραμμή
        except sqlite3.Error as e:
            print(f"Σφάλμα διαγραφής ραντεβού στη βάση: {e}")
            return False
        
        
    @staticmethod
    def get_by_date(date):                                    
        #Επιστρέφει όλα τα ραντεβού μιας συγκεκριμένης ημέρας
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
    def get_by_customer_id(customer_id):                #επιστροφη ολων των ραντεβου βαση id πελατη
        try:
            with sqlite3.connect('salon_appointments.db') as conn:
                c = conn.cursor()
                c.execute("SELECT customer_id, datetime, services, duration, notes, id FROM appointments WHERE customer_id = ? ORDER BY datetime ASC", (customer_id,))
                appointments = c.fetchall()
                return [Appointment(customer_id=row[0], datetime=row[1], services=row[2], duration=row[3], notes=row[4], id=row[5]) for row in appointments]  # Correct Mapping
        except sqlite3.Error as e:
            print(f"Error fetching all appointments(get_by_customer_id): {e}")
            return []


