# models/appointment.py
from utils.db_manager import DatabaseManager # Import the new DatabaseManager
from models.customer import Customer # Import Customer to get customer details

class Appointment:
    def __init__(self, customer_id, datetime_str, services, duration=20, notes="", id=None):
        self.customer_id = customer_id
        self.datetime = datetime_str  # Stored as ISO format string "YYYY-MM-DD HH:MM"
        self.duration = duration
        self.services = services
        self.notes = notes
        self.id = id
        
        # These are not directly from the DB, but useful for display/logic
        self.customer_name = None
        self.customer_phone = None
        self.customer_email = None

        # Optionally load customer details if ID is provided
        if self.customer_id:
            self._load_customer_details()

    def _load_customer_details(self):
        customer = Customer.get_by_id(self.customer_id)
        if customer:
            self.customer_name = f"{customer.first_name} {customer.last_name}"
            self.customer_phone = customer.phone
            self.customer_email = customer.email

    def save(self):
        """Saves or updates the appointment in the database."""
        db = DatabaseManager()
        if self.id:
            # Update existing appointment
            db.execute_query(
                '''UPDATE appointments SET customer_id = ?, datetime = ?, services = ?, duration = ?, notes = ? WHERE id = ?''',
                (self.customer_id, self.datetime, self.services, self.duration, self.notes, self.id)
            )
        else:
            # Insert new appointment
            self.id = db.execute_query(
                '''INSERT INTO appointments (customer_id, datetime, services, duration, notes) VALUES (?, ?, ?, ?, ?)''',
                (self.customer_id, self.datetime, self.services, self.duration, self.notes)
            )
        return self.id

    @staticmethod
    def delete(appointment_id):
        """Deletes an appointment from the database by ID."""
        db = DatabaseManager()
        rows_affected = db.execute_query('DELETE FROM appointments WHERE id = ?', (appointment_id,))
        return rows_affected > 0 # True if at least one row was deleted

    @classmethod
    def get_by_date(cls, date_str):
        """Returns a list of Appointment objects for a specific date (YYYY-MM-DD)."""
        db = DatabaseManager()
        # Query to fetch appointment details along with customer information
        rows = db.fetch_all('''
            SELECT a.id, a.customer_id, a.datetime, a.services, a.duration, a.notes,
                   c.first_name, c.last_name, c.phone, c.email
            FROM appointments a
            JOIN customers c ON a.customer_id = c.id
            WHERE date(a.datetime) = date(?)
            ORDER BY a.datetime ASC
        ''', (date_str,))
        
        appointments = []
        for row in rows:
            # Create an Appointment object, passing only direct appointment fields
            appt = cls(
                id=row[0],
                customer_id=row[1],
                datetime_str=row[2],
                services=row[3],
                duration=row[4],
                notes=row[5]
            )
            # Manually set customer details for display purposes, as they are not part of the Appointment model itself
            appt.customer_name = f"{row[6]} {row[7]}"
            appt.customer_phone = row[8]
            appt.customer_email = row[9]
            appointments.append(appt)
        return appointments

    @classmethod
    def get_by_customer_id(cls, customer_id):
        """Returns a list of Appointment objects for a specific customer ID."""
        db = DatabaseManager()
        rows = db.fetch_all("SELECT id, customer_id, datetime, services, duration, notes FROM appointments WHERE customer_id = ? ORDER BY datetime ASC", (customer_id,))
        return [cls(id=row[0], customer_id=row[1], datetime_str=row[2], services=row[3], duration=row[4], notes=row[5]) for row in rows]

    @classmethod
    def get_all(cls):
        """Returns a list of all Appointment objects."""
        db = DatabaseManager()
        rows = db.fetch_all("SELECT id, customer_id, datetime, services, duration, notes FROM appointments ORDER BY datetime ASC")
        return [cls(id=row[0], customer_id=row[1], datetime_str=row[2], services=row[3], duration=row[4], notes=row[5]) for row in rows]