# models/customer.py
from utils.db_manager import DatabaseManager # Import the new DatabaseManager

class Customer:
    def __init__(self, first_name, last_name, phone, email, notes=None, id=None):
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.email = email
        self.notes = notes # Added notes
        self.id = id

    def save(self):
        """Saves or updates the customer in the database."""
        db = DatabaseManager() # Get the singleton instance
        if self.id:
            # Update existing customer
            db.execute_query(
                '''UPDATE customers SET first_name = ?, last_name = ?, phone = ?, email = ?, notes = ? WHERE id = ?''',
                (self.first_name, self.last_name, self.phone, self.email, self.notes, self.id)
            )
        else:
            # Insert new customer
            self.id = db.execute_query(
                '''INSERT INTO customers (first_name, last_name, phone, email, notes) VALUES (?, ?, ?, ?, ?)''',
                (self.first_name, self.last_name, self.phone, self.email, self.notes)
            )
        return self.id

    @staticmethod
    def delete(phone):
        """Deletes a customer and their appointments based on phone number."""
        db = DatabaseManager()
        # Find customer ID first
        customer_id = db.fetch_one("SELECT id FROM customers WHERE phone = ?", (phone,))
        if customer_id:
            # Appointments are deleted automatically due to ON DELETE CASCADE
            # But it's good practice to clarify
            db.execute_query('DELETE FROM customers WHERE phone = ?', (phone,))
            return True
        return False

    @classmethod
    def get_all(cls):
        """Returns a list of all Customer objects."""
        db = DatabaseManager()
        rows = db.fetch_all("SELECT id, first_name, last_name, phone, email, notes FROM customers ORDER BY last_name ASC")
        # Ensure 'notes' is passed correctly to the constructor
        return [cls(id=row[0], first_name=row[1], last_name=row[2], phone=row[3], email=row[4], notes=row[5]) for row in rows]

    @classmethod
    def get_name_by_id(cls, customer_id):
        """Returns the full name of a customer by their ID."""
        db = DatabaseManager()
        result = db.fetch_one("SELECT first_name, last_name FROM customers WHERE id = ?", (customer_id,))
        if result:
            return f"{result[0]} {result[1]}"
        return ""

    @classmethod
    def get_by_id(cls, customer_id):
        """Returns a Customer object by their ID."""
        db = DatabaseManager()
        result = db.fetch_one("SELECT id, first_name, last_name, phone, email, notes FROM customers WHERE id = ?", (customer_id,))
        if result:
            return cls(id=result[0], first_name=result[1], last_name=result[2], phone=result[3], email=result[4], notes=result[5])
        return None

    @classmethod
    def get_by_phone(cls, phone):
        """Returns a Customer object by their phone number."""
        db = DatabaseManager()
        result = db.fetch_one("SELECT id, first_name, last_name, phone, email, notes FROM customers WHERE phone = ?", (phone,))
        if result:
            return cls(id=result[0], first_name=result[1], last_name=result[2], phone=result[3], email=result[4], notes=result[5])
        return None