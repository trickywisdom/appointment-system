# kivy/screens/new_client_screen.py

from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.metrics import dp

# Import the Customer model
from models.customer import Customer

class NewClientScreen(Screen):
    # Kivy properties to bind with KV file TextInput widgets
    first_name_input = ObjectProperty(None)
    last_name_input = ObjectProperty(None)
    phone_input = ObjectProperty(None)
    email_input = ObjectProperty(None)
    notes_input = ObjectProperty(None)

    def on_kv_post(self, base_widget):
        """Called immediately after the KV file is loaded and processed."""
        self.clear_form_fields()

    def on_enter(self, *args):
        """Called when the screen becomes the current screen."""
        self.clear_form_fields()

    def save_client(self):
        """Gathers data from inputs and saves a new client to the database."""
        first_name = self.first_name_input.text.strip() if self.first_name_input else ""
        last_name = self.last_name_input.text.strip() if self.last_name_input else ""
        phone = self.phone_input.text.strip() if self.phone_input else ""
        email = self.email_input.text.strip() if self.email_input else ""
        notes = self.notes_input.text.strip() if self.notes_input else ""

        # Basic validation
        if not first_name or not last_name:
            self.show_popup("Σφάλμα", "Παρακαλώ συμπληρώστε Όνομα και Επώνυμο.")
            return
        
        # Optional: More rigorous validation for phone/email if needed
        # e.g., using regex for email format
        
        try:
            new_customer = Customer(
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                email=email,
                notes=notes
            )
            new_customer.save() # Use the save method from the Customer model

            self.show_popup("Επιτυχία", f"Ο πελάτης '{first_name} {last_name}' καταχωρήθηκε επιτυχώς!")
            self.clear_form_fields()
            # Optionally navigate back to dashboard or clients list
            # self.manager.current = 'dashboard_screen' 
        except Exception as e:
            self.show_popup("Σφάλμα Βάσης Δεδομένων", f"Αποτυχία καταχώρησης πελάτη: {e}")

    def clear_form_fields(self):
        """Clears all input fields."""
        if self.first_name_input:
            self.first_name_input.text = ""
        if self.last_name_input:
            self.last_name_input.text = ""
        if self.phone_input:
            self.phone_input.text = ""
        if self.email_input:
            self.email_input.text = ""
        if self.notes_input:
            self.notes_input.text = ""

    def show_popup(self, title, message):
        """Helper to show a simple Kivy popup."""
        popup = Popup(title=title,
                      content=Label(text=message, halign='center', valign='middle'),
                      size_hint=(None, None), size=(dp(400), dp(200)))
        popup.open()

    def go_back(self):
        """Navigates back to the Dashboard screen."""
        self.manager.current = 'dashboard_screen'