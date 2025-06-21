# models/appointment.py
from utils.db_manager import DatabaseManager # Import the DatabaseManager singleton
from models.customer import Customer # Import Customer to get customer details (no circular import now)
from datetime import datetime, timedelta # Import datetime and timedelta
from kivy.logger import Logger # Import Kivy Logger

class Appointment:
    def __init__(self, customer_id, datetime_obj, services, duration=20, notes="", id=None):
        self.id = id
        self.customer_id = customer_id
        self.datetime = datetime_obj  # This is now expected to be a datetime object
        self.duration = duration      # In minutes
        self.services = services
        self.notes = notes
        
        # These are not directly from the DB, but useful for display/logic
        self.customer_name = None
        self.customer_phone = None
        self.customer_email = None

        # Optionally load customer details if ID is provided
        # This will be done on initialization if customer_id is present
        self._load_customer_details()

    def _load_customer_details(self):
        """Loads customer details based on customer_id."""
        if self.customer_id:
            customer = Customer.get_by_id(self.customer_id)
            if customer:
                self.customer_name = f"{customer.first_name} {customer.last_name}"
                self.customer_phone = customer.phone
                self.customer_email = customer.email
            else:
                Logger.warning(f"Appointment Model: Customer ID {self.customer_id} not found for appointment ID {self.id}.")
        else:
            Logger.warning(f"Appointment Model: No customer_id provided for appointment ID {self.id}.")


    def save(self):
        """Saves or updates the appointment in the database."""
        db = DatabaseManager()
        try:
            # Convert datetime object to string for storage
            if not isinstance(self.datetime, datetime):
                raise ValueError("Appointment datetime must be a datetime object.")
            datetime_str = self.datetime.strftime("%Y-%m-%d %H:%M")

            if self.id:
                # Update existing appointment
                db.execute_query(
                    '''UPDATE appointments SET customer_id = ?, datetime = ?, services = ?, duration = ?, notes = ? WHERE id = ?''',
                    (self.customer_id, datetime_str, self.services, self.duration, self.notes, self.id)
                )
                Logger.info(f"Appointment Model: Appointment ID {self.id} updated.")
            else:
                # Insert new appointment
                self.id = db.execute_query(
                    '''INSERT INTO appointments (customer_id, datetime, services, duration, notes) VALUES (?, ?, ?, ?, ?)''',
                    (self.customer_id, datetime_str, self.services, self.duration, self.notes)
                )
                Logger.info(f"Appointment Model: New appointment for customer ID {self.customer_id} at {datetime_str} added with ID: {self.id}")
            return self.id
        except (ValueError, RuntimeError) as e:
            Logger.error(f"Appointment Model: Error saving appointment for customer ID {self.customer_id}: {e}")
            return None

    @classmethod
    def delete(cls, appointment_id):
        """Deletes an appointment from the database by ID."""
        db = DatabaseManager()
        try:
            rows_affected = db.execute_query('DELETE FROM appointments WHERE id = ?', (appointment_id,))
            if rows_affected > 0:
                Logger.info(f"Appointment Model: Appointment ID {appointment_id} deleted.")
                return True
            Logger.warning(f"Appointment Model: No appointment found with ID {appointment_id} to delete.")
            return False
        except (ValueError, RuntimeError) as e:
            Logger.error(f"Appointment Model: Error deleting appointment ID {appointment_id}: {e}")
            return False

    @classmethod
    def get_by_date(cls, date_str):
        """Returns a list of Appointment objects for a specific date (YYYY-MM-DD)."""
        db = DatabaseManager()
        # Query to fetch appointment details. Customer details are loaded by the Appointment constructor.
        rows = db.fetch_all('''
            SELECT id, customer_id, datetime, services, duration, notes
            FROM appointments
            WHERE date(datetime) = date(?)
            ORDER BY datetime ASC
        ''', (date_str,))
        
        appointments = []
        for row in rows:
            try:
                # Convert datetime string from DB to datetime object for the model
                datetime_obj = datetime.strptime(row[2], "%Y-%m-%d %H:%M")
                appt = cls(
                    id=row[0],
                    customer_id=row[1],
                    datetime_obj=datetime_obj, # Pass as datetime object
                    services=row[3],
                    duration=row[4],
                    notes=row[5]
                )
                appointments.append(appt)
            except ValueError as e:
                Logger.error(f"Appointment Model: Error parsing datetime for appointment ID {row[0]}: {e}")
                continue # Skip this appointment if date parsing fails
        return appointments

    @classmethod
    def get_by_customer_id(cls, customer_id):
        """Returns a list of Appointment objects for a specific customer ID."""
        db = DatabaseManager()
        rows = db.fetch_all("SELECT id, customer_id, datetime, services, duration, notes FROM appointments WHERE customer_id = ? ORDER BY datetime ASC", (customer_id,))
        appointments = []
        for row in rows:
            try:
                datetime_obj = datetime.strptime(row[2], "%Y-%m-%d %H:%M")
                appointments.append(cls(id=row[0], customer_id=row[1], datetime_obj=datetime_obj, services=row[3], duration=row[4], notes=row[5]))
            except ValueError as e:
                Logger.error(f"Appointment Model: Error parsing datetime for appointment ID {row[0]} (customer {customer_id}): {e}")
                continue
        return appointments

    @classmethod
    def get_all(cls):
        """Returns a list of all Appointment objects."""
        db = DatabaseManager()
        rows = db.fetch_all("SELECT id, customer_id, datetime, services, duration, notes FROM appointments ORDER BY datetime ASC")
        appointments = []
        for row in rows:
            try:
                datetime_obj = datetime.strptime(row[2], "%Y-%m-%d %H:%M")
                appointments.append(cls(id=row[0], customer_id=row[1], datetime_obj=datetime_obj, services=row[3], duration=row[4], notes=row[5]))
            except ValueError as e:
                Logger.error(f"Appointment Model: Error parsing datetime for appointment ID {row[0]}: {e}")
                continue
        return appointments

    @classmethod
    def get_by_id(cls, appointment_id):
        """Returns an Appointment object by its ID."""
        db = DatabaseManager()
        row = db.fetch_one("SELECT id, customer_id, datetime, services, duration, notes FROM appointments WHERE id = ?", (appointment_id,))
        if row:
            try:
                datetime_obj = datetime.strptime(row[2], "%Y-%m-%d %H:%M")
                return cls(id=row[0], customer_id=row[1], datetime_obj=datetime_obj, services=row[3], duration=row[4], notes=row[5])
            except ValueError as e:
                Logger.error(f"Appointment Model: Error parsing datetime for appointment ID {row[0]}: {e}")
                return None
        return None

# Add test usage example if you want to run this file directly for testing
if __name__ == '__main__':
    from datetime import datetime, timedelta
    Logger.info("--- Testing Appointment Model (from appointment.py) ---")
    
    # Initialize DB (the singleton will handle it)
    db = DatabaseManager()

    # Ensure a customer exists for testing appointments
    existing_customers = Customer.get_all()
    customer_for_test_id = None
    if not existing_customers:
        Logger.info("No customers found, creating one for appointment testing.")
        temp_customer = Customer("Temp", "Customer", "9999999999", "temp@example.com", "Temp Address", "Temp Notes")
        customer_for_test_id = temp_customer.save()
    else:
        customer_for_test_id = existing_customers[0].id
        Logger.info(f"Using existing customer ID: {customer_for_test_id} for appointment testing.")

    if customer_for_test_id:
        # Test Add Appointment
        now = datetime.now().replace(second=0, microsecond=0)
        new_appointment = Appointment(customer_for_test_id, now + timedelta(days=1, hours=10), "Haircut", 60, "First haircut")
        appointment_id = new_appointment.save()
        if appointment_id:
            Logger.info(f"Added appointment with ID: {appointment_id}")
        else:
            Logger.error("Failed to add appointment.")

        # Test Get All Appointments
        all_appointments = Appointment.get_all()
        Logger.info(f"All appointments: {len(all_appointments)}")
        for appt in all_appointments:
            cust_details = appt.customer_name if appt.customer_name else "Unknown Customer"
            Logger.info(f"  ID: {appt.id}, Customer: {cust_details}, Time: {appt.datetime.strftime('%Y-%m-%d %H:%M')}, Service: {appt.services}")

        # Test Get By Date
        today_str = datetime.now().strftime("%Y-%m-%d")
        appointments_today = Appointment.get_by_date(today_str)
        Logger.info(f"Appointments for {today_str}: {len(appointments_today)}")

        # Test Get By ID
        if appointment_id:
            retrieved_appt = Appointment.get_by_id(appointment_id)
            if retrieved_appt:
                Logger.info(f"Retrieved appointment by ID {appointment_id}: Customer {retrieved_appt.customer_name}, Service: {retrieved_appt.services}")
                
                # Test Update Appointment
                retrieved_appt.notes = "Updated notes: Second visit expected."
                if retrieved_appt.save():
                    Logger.info(f"Appointment ID {retrieved_appt.id} updated.")
                else:
                    Logger.error(f"Failed to update appointment ID {retrieved_appt.id}.")
            else:
                Logger.warning(f"Could not retrieve appointment by ID {appointment_id}.")

        # Test Delete Appointment (Use with caution in real apps!)
        # if appointment_id:
        #     if Appointment.delete(appointment_id):
        #         Logger.info(f"Appointment ID {appointment_id} deleted successfully.")
        #     else:
        #         Logger.error(f"Failed to delete appointment ID {appointment_id}.")
    else:
        Logger.error("Could not set up customer for appointment testing.")

    db.close_connection()