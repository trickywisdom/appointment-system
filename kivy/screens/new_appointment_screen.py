# screens/new_appointment_screen.py

from datetime import datetime, timedelta
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.metrics import dp

# Import models and utilities
from models.customer import Customer
from models.appointment import Appointment

class NewAppointmentScreen(Screen):
    # Kivy Properties for UI elements (bind to KV file)
    customer_spinner = ObjectProperty(None)
    service_spinner = ObjectProperty(None)
    duration_spinner = ObjectProperty(None)
    date_input = ObjectProperty(None)
    time_input = ObjectProperty(None)
    notes_input = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.customers_data = {} # To store {full_name: customer_id}
        self.services_data = {} # To store {service_name: duration_in_minutes}
    
    # --- Η ΣΗΜΑΝΤΙΚΗ ΔΙΟΡΘΩΣΗ ΕΔΩ: ΧΡΗΣΗ on_kv_post ---
    def on_kv_post(self, base_widget):
        """Called immediately after the KV file for this widget is loaded and processed.
        This is the safest place to initialize widgets defined in KV."""
        self.load_initial_data()
        self.clear_form_fields()
        
    def on_enter(self, *args):
        """Called when the screen becomes the current screen.
        This will ensure data is refreshed if the screen is revisited."""
        # We call load_initial_data and clear_form_fields directly here as well,
        # but the on_kv_post ensures initial setup even if on_enter isn't triggered
        # immediately (e.g., if it's the first screen).
        # It's okay to call them again, they'll just re-set the values.
        self.load_initial_data()
        self.clear_form_fields()

    def load_initial_data(self):
        """Loads customers and services from the database."""
        # Load Customers
        try:
            customers = Customer.get_all()
            self.customers_data = {f"{c.first_name} {c.last_name}": c.id for c in customers}
            
            # Ensure customer_spinner is not None before accessing its properties
            if self.customer_spinner:
                self.customer_spinner.values = sorted(self.customers_data.keys())
                if self.customer_spinner.values:
                    self.customer_spinner.text = self.customer_spinner.values[0] # Set default
                else:
                    self.customer_spinner.text = "Δεν βρέθηκαν Πελάτες"
                    # If no customers, keep values empty to prevent issues
                    self.customer_spinner.values = [] 
            else:
                print("Warning: customer_spinner is None during load_initial_data.") # For debugging
        except Exception as e:
            self.show_popup("Σφάλμα Φόρτωσης", f"Αποτυχία φόρτωσης πελατών: {e}")
            if self.customer_spinner: # Still check in case of error
                self.customer_spinner.values = []
                self.customer_spinner.text = "Σφάλμα Φόρτωσης"

        # Load Services (hardcoded for now, can be dynamic from DB later)
        self.services_data = {
            "Κούρεμα": 30,
            "Βαφή": 60,
            "Χτένισμα": 45,
            "Περιποίηση προσώπου": 90,
            "Μανικιούρ": 40
        }
        
        # Ensure service_spinner is not None
        if self.service_spinner:
            self.service_spinner.values = sorted(self.services_data.keys())
            if self.service_spinner.values:
                self.service_spinner.text = self.service_spinner.values[0] # Set default
                self.update_duration_spinner(self.service_spinner.text)
            else:
                self.service_spinner.text = "Δεν βρέθηκαν Υπηρεσίες"
                self.service_spinner.values = []
                if self.duration_spinner: # Ensure duration_spinner is also checked
                    self.duration_spinner.values = []
                    self.duration_spinner.text = "0"
        else:
            print("Warning: service_spinner is None during load_initial_data.") # For debugging


    def update_duration_spinner(self, service_name):
        """Updates the duration spinner based on the selected service."""
        duration = self.services_data.get(service_name, 0)
        durations = [15, 20, 30, 40, 45, 50, 60, 75, 90, 105, 120]
        all_durations = sorted(list(set(durations + [duration])))
        
        if self.duration_spinner: # Ensure duration_spinner is not None
            self.duration_spinner.values = [str(d) for d in all_durations if d >= duration]
            
            if str(duration) in self.duration_spinner.values:
                self.duration_spinner.text = str(duration)
            elif self.duration_spinner.values:
                self.duration_spinner.text = self.duration_spinner.values[0]
            else:
                self.duration_spinner.text = "0"
        else:
            print("Warning: duration_spinner is None during update_duration_spinner.") # For debugging

    def save_appointment(self):
        """Saves a new appointment to the database."""
        customer_name = self.customer_spinner.text
        service_name = self.service_spinner.text
        date_text = self.date_input.text
        time_text = self.time_input.text
        duration_text = self.duration_spinner.text
        notes = self.notes_input.text

        # 1. Validation
        if not all([customer_name, service_name, date_text, time_text, duration_text]):
            self.show_popup("Σφάλμα", "Παρακαλώ συμπληρώστε όλα τα απαραίτητα πεδία (Πελάτης, Υπηρεσία, Ημερομηνία, Ώρα, Διάρκεια).")
            return
        
        if customer_name == "Δεν βρέθηκαν Πελάτες":
            self.show_popup("Σφάλμα", "Δεν έχετε επιλέξει έγκυρο πελάτη. Παρακαλώ προσθέστε πελάτες πρώτα.")
            return

        try:
            customer_id = self.customers_data.get(customer_name)
            if customer_id is None:
                self.show_popup("Σφάλμα", f"Ο πελάτης '{customer_name}' δεν βρέθηκε ή δεν έχει επιλεγεί σωστά.")
                return

            appointment_datetime_str = f"{date_text} {time_text}"
            appointment_datetime_obj = datetime.strptime(appointment_datetime_str, "%d-%m-%Y %H:%M")
            duration_minutes = int(duration_text)

        except ValueError as e:
            self.show_popup("Σφάλμα Μορφής", f"Λάθος μορφή ημερομηνίας/ώρας/διάρκειας. Παρακαλώ ελέγξτε: {e}")
            return
        except Exception as e:
            self.show_popup("Γενικό Σφάλμα", f"Προέκυψε ένα απροσδόκητο σφάλμα: {e}")
            return

        # 2. Save to DB using the Appointment model
        try:
            new_appointment = Appointment(
                customer_id=customer_id,
                datetime_str=appointment_datetime_obj.isoformat(sep=' ', timespec='minutes'), # "YYYY-MM-DD HH:MM"
                services=service_name,
                duration=duration_minutes,
                notes=notes
            )
            new_appointment.save()
            self.show_popup("Επιτυχία", "Το ραντεβού καταχωρήθηκε επιτυχώς!")
            self.clear_form_fields() # Clear after successful save
            # Potentially refresh data if you are staying on this screen, otherwise navigate
            # self.load_initial_data() # Uncomment if you want to reload spinner data (e.g. if a new customer was added)
            # self.manager.current = 'dashboard_screen' 
        except Exception as e:
            self.show_popup("Σφάλμα Βάσης Δεδομένων", f"Αποτυχία καταχώρησης ραντεβού: {e}")

    def clear_form_fields(self):
        """Clears all input fields and resets date/time to current.
        Ensures widgets are not None before accessing them."""
        # Added checks for None before accessing .text property
        if self.date_input:
            self.date_input.text = datetime.now().strftime("%d-%m-%Y")
        if self.time_input:
            self.time_input.text = datetime.now().strftime("%H:%M")
        if self.notes_input:
            self.notes_input.text = ""

        # For spinners, if you want to reset them to default prompt text after clearing:
        if self.customer_spinner:
            self.customer_spinner.text = "Επιλέξτε Πελάτη"
            # And re-load initial data to ensure values are there for next entry
            # self.load_initial_data() # This might cause loop if called here
        if self.service_spinner:
            self.service_spinner.text = "Επιλέξτε Υπηρεσία"
        if self.duration_spinner:
            self.duration_spinner.text = "Επιλέξτε Διάρκεια" # Or "0" as default

    def show_popup(self, title, message):
        """Helper to show a simple Kivy popup."""
        popup = Popup(title=title,
                      content=Label(text=message, halign='center', valign='middle'),
                      size_hint=(None, None), size=(dp(400), dp(200)))
        popup.open()

    def go_back(self):
        """Navigates back to the Dashboard screen."""
        self.manager.current = 'dashboard_screen'