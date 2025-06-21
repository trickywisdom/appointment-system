# kivy/screens/clients_screen.py

from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, ListProperty, StringProperty, NumericProperty # <-- Προσθέσαμε NumericProperty αν χρειαστεί
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.button import Button

# Import the Customer model
from models.customer import Customer

# Define a custom Widget for RecycleView items
class ClientListItem(ButtonBehavior, BoxLayout):
    client_id = NumericProperty(0) # Changed to NumericProperty for IDs
    client_first_name = StringProperty('') # New property
    client_last_name = StringProperty('')  # New property
    client_phone = StringProperty('')
    client_email = StringProperty('')
    # Προσθήκη νέας ιδιότητας για τον δείκτη της γραμμής
    row_index = NumericProperty(-1) # <-- ΝΕΑ ΙΔΙΟΤΗΤΑ
    

    # Methods for action buttons
    def show_details(self):
        # Implement navigation to a Client Details screen here
        print(f"Showing details for client ID: {self.client_id}")
        self.parent.parent.parent.parent.show_popup("Πληροφορίες Πελάτη", 
            f"ID: {self.client_id}\nΕπώνυμο: {self.client_last_name}\nΌνομα: {self.client_first_name}\nΤηλέφωνο: {self.client_phone}\nEmail: {self.client_email}")

    def edit_client(self):
        # Implement navigation to a Client Edit screen (e.g., reuse NewClientScreen)
        print(f"Editing client ID: {self.client_id}")
        # To navigate to NewClientScreen for editing, you'd pass the client_id
        # and modify NewClientScreen to handle existing client data.
        self.parent.parent.parent.parent.show_popup("Επεξεργασία Πελάτη", 
            f"Θα ανοίξει οθόνη επεξεργασίας για τον πελάτη: {self.client_last_name} {self.client_first_name}")

    def delete_client(self):
        # Implement client deletion logic with confirmation
        print(f"Deleting client ID: {self.client_id}")
        # It's good practice to ask for confirmation before deleting
        self.parent.parent.parent.parent.confirm_delete_client(self.client_id, f"{self.client_last_name} {self.client_first_name}")


class ClientsScreen(Screen):
    client_list_rv = ObjectProperty(None)
    rv_data = ListProperty([])
    # Property to hold the current search text for dynamic filtering
    search_text = StringProperty('') 
    search_input = ObjectProperty(None)
    def on_kv_post(self, base_widget):
        self.load_clients()

    def on_enter(self, *args):
        self.load_clients()
        # Ensure search input is cleared when entering the screen
        if self.search_input: # Check if search_input exists
            self.search_input.text = ''
        self.search_text = '' # Clear search filter

    def load_clients(self):
        """Loads all clients from the database and populates the RecycleView data."""
        try:
            customers = Customer.get_all()
            customers_sorted = sorted(customers, key=lambda c: c.last_name.lower())
            
            self.rv_data = []
            for i, customer in enumerate(customers_sorted): # <-- Χρησιμοποιούμε enumerate για τον δείκτη
                if self.search_text.strip() == '' or \
                   self.search_text.lower() in customer.last_name.lower() or \
                   self.search_text.lower() in customer.phone.lower():
                    
                    self.rv_data.append({
                        'client_id': customer.id,
                        'client_first_name': customer.first_name,
                        'client_last_name': customer.last_name,
                        'client_phone': customer.phone if customer.phone else 'Δεν υπάρχει',
                        'client_email': customer.email if customer.email else 'Δεν υπάρχει',
                        'row_index': i # <-- Περνάμε τον δείκτη (index)
                    })
        except Exception as e:
            self.show_popup("Σφάλμα Φόρτωσης", f"Αποτυχία φόρτωσης πελατών: {e}")
            self.rv_data = []

    def on_search_text(self, instance, value):
        """Called automatically when search_text property changes."""
        self.load_clients() # Re-load clients with the new filter

    # Changed from search_clients to update_search_text
    def update_search_text(self, text_input_instance):
        """Updates the search_text property when TextInput changes."""
        self.search_text = text_input_instance.text # This will trigger on_search_text

    def confirm_delete_client(self, client_id, client_name):
        """Shows a confirmation popup before deleting a client."""
        content = BoxLayout(orientation='vertical', padding='10dp', spacing='10dp')
        content.add_widget(Label(text=f"Είστε σίγουροι ότι θέλετε να διαγράψετε τον πελάτη '{client_name}';"))
        
        button_layout = BoxLayout(spacing='10dp')
        btn_yes = Button(text="Ναι", size_hint_y=None, height='40dp')
        btn_no = Button(text="Όχι", size_hint_y=None, height='40dp')
        button_layout.add_widget(btn_yes)
        button_layout.add_widget(btn_no)
        content.add_widget(button_layout)

        popup = Popup(title="Επιβεβαίωση Διαγραφής", content=content, size_hint=(0.8, 0.4), auto_dismiss=False)
        
        btn_yes.bind(on_release=lambda x: self._execute_delete_client(client_id, popup))
        btn_no.bind(on_release=popup.dismiss)
        popup.open()

    def _execute_delete_client(self, client_id, popup):
        """Executes the client deletion."""
        try:
            Customer.delete_by_id(client_id)
            self.show_popup("Επιτυχία", "Ο πελάτης διαγράφηκε επιτυχώς.")
            self.load_clients() # Refresh the list
        except Exception as e:
            self.show_popup("Σφάλμα Διαγραφής", f"Αποτυχία διαγραφής πελάτη: {e}")
        finally:
            popup.dismiss()

    def show_popup(self, title, message):
        """Helper to show a simple Kivy popup."""
        popup = Popup(title=title,
                      content=Label(text=message, halign='center', valign='middle'),
                      size_hint=(None, None), size=(dp(400), dp(200)))
        popup.open()

    def go_to_new_client_screen(self):
        """Navigates to the New Client screen."""
        self.manager.current = 'new_client_screen'

    def go_back(self):
        """Navigates back to the Dashboard screen."""
        self.manager.current = 'dashboard_screen'