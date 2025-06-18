# utils/db_manager.py
import sqlite3

class DatabaseManager:
    _instance = None
    _conn = None
    _cursor = None
    _db_path = 'salon_appointments_app.db'

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize_db()
        return cls._instance

    def _initialize_db(self):
        """Initializes the database connection and sets up tables."""
        if self._conn is None:
            try:
                self._conn = sqlite3.connect(self._db_path)
                self._cursor = self._conn.cursor()
                self._setup_tables()
            except sqlite3.Error as e:
                print(f"Database connection error: {e}")
                # Handle this error appropriately in your application (e.g., show a popup)

    def _setup_tables(self):
        """Creates the necessary tables if they don't exist."""
        # Create customers table
        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                notes TEXT -- Added notes field, as it's common for customers too
            )
        ''')

        # Create appointments table
        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                datetime TEXT NOT NULL,
                services TEXT NOT NULL,
                duration INTEGER NOT NULL DEFAULT 20,
                notes TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
            )
        ''')
        # Added ON DELETE CASCADE to automatically delete appointments if a customer is deleted
        self._conn.commit()

    def get_connection(self):
        """Returns the active database connection."""
        return self._conn

    def get_cursor(self):
        """Returns the active database cursor."""
        return self._cursor

    def fetch_all(self, query, params=()):
        """Executes a SELECT query and returns all results."""
        self.get_cursor().execute(query, params)
        return self.get_cursor().fetchall()

    def fetch_one(self, query, params=()):
        """Executes a SELECT query and returns a single result."""
        self.get_cursor().execute(query, params)
        return self.get_cursor().fetchone()

    def execute_query(self, query, params=()):
        """Executes an INSERT, UPDATE, or DELETE query and commits."""
        try:
            self.get_cursor().execute(query, params)
            self.get_connection().commit()
            return self.get_cursor().lastrowid # Returns ID for inserts
        except sqlite3.IntegrityError as e:
            # Handle unique constraint errors or foreign key violations
            raise ValueError(f"Database integrity error: {e}")
        except sqlite3.Error as e:
            # Catch all other SQLite errors
            raise RuntimeError(f"Database operation failed: {e}")

    def close_connection(self):
        """Closes the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            self._cursor = None
            DatabaseManager._instance = None # Reset instance on close

# Usage example:
if __name__ == '__main__':
    db_manager = DatabaseManager() # This will create and setup the db
    # You can now use db_manager.execute_query, db_manager.fetch_all, etc.
    # To ensure it's a singleton:
    another_db_manager = DatabaseManager()
    print(db_manager is another_db_manager) # Should print True
    db_manager.close_connection()