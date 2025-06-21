# models/customer.py
from utils.db_manager import DatabaseManager # Import the DatabaseManager singleton
from kivy.logger import Logger # Import Kivy Logger

class Customer:
    def __init__(self, first_name, last_name, phone, email, notes=None, id=None):
        self.id = id # ID should be initialized first if it exists
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.email = email
        self.notes = notes

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self):
        """Saves or updates the customer in the database."""
        db = DatabaseManager() # Get the singleton instance
        try:
            if self.id:
                # Update existing customer
                db.execute_query(
                    '''UPDATE customers SET first_name = ?, last_name = ?, phone = ?, email = ?, notes = ? WHERE id = ?''',
                    (self.first_name, self.last_name, self.phone, self.email, self.notes, self.id)
                )
                Logger.info(f"Customer Model: Customer ID {self.id} updated.")
            else:
                # Insert new customer
                self.id = db.execute_query(
                    '''INSERT INTO customers (first_name, last_name, phone, email, notes) VALUES (?, ?, ?, ?, ?)''',
                    (self.first_name, self.last_name, self.phone, self.email, self.notes)
                )
                Logger.info(f"Customer Model: New customer '{self.full_name}' added with ID: {self.id}")
            return self.id
        except (ValueError, RuntimeError) as e:
            Logger.error(f"Customer Model: Error saving customer '{self.full_name}': {e}")
            return None

    @classmethod
    def delete(cls, customer_id):
        """Deletes a customer by ID. Appointments are deleted automatically due to ON DELETE CASCADE."""
        db = DatabaseManager()
        try:
            rows_affected = db.execute_query('DELETE FROM customers WHERE id = ?', (customer_id,))
            if rows_affected > 0:
                Logger.info(f"Customer Model: Customer ID {customer_id} deleted (and cascade deleted appointments).")
                return True
            Logger.warning(f"Customer Model: No customer found with ID {customer_id} to delete.")
            return False
        except (ValueError, RuntimeError) as e:
            Logger.error(f"Customer Model: Error deleting customer ID {customer_id}: {e}")
            return False

    @classmethod
    def get_all(cls):
        """Returns a list of all Customer objects."""
        db = DatabaseManager()
        # Αφαιρέθηκε το 'address' από το SELECT
        rows = db.fetch_all("SELECT id, first_name, last_name, phone, email, notes FROM customers ORDER BY last_name ASC")
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
        # Αφαιρέθηκε το 'address' από το SELECT
        result = db.fetch_one("SELECT id, first_name, last_name, phone, email, notes FROM customers WHERE id = ?", (customer_id,))
        if result:
            return cls(id=result[0], first_name=result[1], last_name=result[2], phone=result[3], email=result[4], notes=result[5])
        return None

    @classmethod
    def get_by_phone(cls, phone):
        """Returns a Customer object by their phone number."""
        db = DatabaseManager()
        # Αφαιρέθηκε το 'address' από το SELECT
        result = db.fetch_one("SELECT id, first_name, last_name, phone, email, notes FROM customers WHERE phone = ?", (phone,))
        if result:
            return cls(id=result[0], first_name=result[1], last_name=result[2], phone=result[3], email=result[4], notes=result[5])
        return None

# Add test usage example if you want to run this file directly for testing
if __name__ == '__main__':
    from datetime import datetime
    Logger.info("--- Testing Customer Model (from customer.py) ---")
    
    # Initialize DB (the singleton will handle it)
    db = DatabaseManager() 

    # Test Add Customer
    # Αφαιρέθηκε το 'address'
    new_customer = Customer("Test", "Customer1", "1234567890", "test1@example.com", "Notes for Test 1")
    customer_id = new_customer.save()
    if customer_id:
        Logger.info(f"Added customer: {new_customer.full_name} with ID: {customer_id}")
    else:
        Logger.error("Failed to add customer.")

    # Test Get All Customers
    all_customers = Customer.get_all()
    Logger.info(f"All customers: {len(all_customers)}")
    for cust in all_customers:
        # Αφαιρέθηκε το 'address' από την εκτύπωση
        Logger.info(f"  ID: {cust.id}, Name: {cust.full_name}, Phone: {cust.phone}, Email: {cust.email}, Notes: {cust.notes}")

    # Test Get By ID
    if customer_id:
        retrieved_customer = Customer.get_by_id(customer_id)
        if retrieved_customer:
            Logger.info(f"Retrieved customer by ID {customer_id}: {retrieved_customer.full_name}")
            
            # Test Update Customer
            retrieved_customer.notes = "Updated notes for Test 1"
            # Αφαιρέθηκε η ενημέρωση address
            if retrieved_customer.save():
                Logger.info(f"Customer ID {retrieved_customer.id} updated.")
            else:
                Logger.error(f"Failed to update customer ID {retrieved_customer.id}.")
        else:
            Logger.warning(f"Could not retrieve customer by ID {customer_id}.")
    
    # Test Get By Phone
    if new_customer.phone:
        retrieved_customer_by_phone = Customer.get_by_phone(new_customer.phone)
        if retrieved_customer_by_phone:
            Logger.info(f"Retrieved customer by phone {new_customer.phone}: {retrieved_customer_by_phone.full_name}")
        else:
            Logger.warning(f"Could not retrieve customer by phone {new_customer.phone}.")

    db.close_connection()