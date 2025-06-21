# kivy/utils/db_manager.py

import sqlite3
from kivy.logger import Logger # Corrected Kivy Logger Import

class DatabaseManager:
    _instance = None
    _conn = None
    _cursor = None
    _db_path = 'salon_appointments_app.db' # Ensure this path is correct for your project

    def __new__(cls):
        """Ensures only one instance of DatabaseManager exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize_db()
        return cls._instance

    def _initialize_db(self):
        """Initializes the database connection and sets up tables."""
        if self._conn is None:
            try:
                self._conn = sqlite3.connect(self._db_path)
                # Enable foreign key support (important for ON DELETE CASCADE)
                self._cursor = self._conn.cursor()
                self._cursor.execute("PRAGMA foreign_keys = ON;") 
                self._setup_tables()
                Logger.info(f"DatabaseManager: Successfully connected to {self._db_path} and tables set up.")
            except sqlite3.Error as e:
                Logger.error(f"DatabaseManager: Database connection error: {e}")
                # Consider showing a popup or handling this critical error in the UI

    def _setup_tables(self):
        """Creates the necessary tables if they don't exist."""
        # Create customers table
        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE, -- Προστέθηκε NOT NULL και UNIQUE
                email TEXT UNIQUE,           -- Προστέθηκε UNIQUE (επιτρέπει NULL)
                notes TEXT
            )
        ''')

        # Create appointments table
        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                datetime TEXT NOT NULL, 
                duration INTEGER NOT NULL DEFAULT 20, 
                services TEXT NOT NULL,      -- Προστέθηκε NOT NULL
                notes TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
            )
        ''')
        self._conn.commit()
        Logger.info("DatabaseManager: Tables checked/created successfully.")

    def get_connection(self):
        """Returns the active database connection."""
        return self._conn

    def get_cursor(self):
        """Returns the active database cursor."""
        return self._cursor

    def fetch_all(self, query, params=()):
        """Executes a SELECT query and returns all results."""
        try:
            self.get_cursor().execute(query, params)
            return self.get_cursor().fetchall()
        except sqlite3.Error as e:
            Logger.error(f"DatabaseManager: Error fetching all data: {e}")
            return []

    def fetch_one(self, query, params=()):
        """Executes a SELECT query and returns a single result."""
        try:
            self.get_cursor().execute(query, params)
            return self.get_cursor().fetchone()
        except sqlite3.Error as e:
            Logger.error(f"DatabaseManager: Error fetching one row: {e}")
            return None

    def execute_query(self, query, params=()):
        """Executes an INSERT, UPDATE, or DELETE query and commits."""
        try:
            self.get_cursor().execute(query, params)
            self.get_connection().commit()
            return self.get_cursor().lastrowid # Returns ID for inserts
        except sqlite3.IntegrityError as e:
            Logger.warning(f"DatabaseManager: Integrity error during query execution: {e} | Query: {query} | Params: {params}")
            raise ValueError(f"Database integrity error: {e}. Data might be duplicated or invalid.")
        except sqlite3.Error as e:
            Logger.error(f"DatabaseManager: SQLite error during query execution: {e} | Query: {query} | Params: {params}")
            raise RuntimeError(f"Database operation failed: {e}")

    def close_connection(self):
        """Closes the database connection and resets the singleton instance."""
        if self._conn:
            self._conn.close()
            DatabaseManager._conn = None
            DatabaseManager._cursor = None
            DatabaseManager._instance = None # Reset instance on close
            Logger.info("DatabaseManager: Database connection closed and instance reset.")