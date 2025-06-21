# kivy/main.py

import sys
import os
import kivy
# from kivy.app import App # <-- Αφαιρέθηκε
from kivymd.app import MDApp # <-- Χρησιμοποιούμε MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.uix.popup import Popup
from kivy.uix.label import Label
# from kivy.utils import get_color_from_hex # <-- Αφαιρέθηκε, δεν χρειάζεται πλέον
from datetime import date, datetime
from kivy.core.window import Window # Needed for Window.clearcolor and size, as well as SearchModal animation

# --- Import custom widgets (Python classes) so Kivy's Factory registers them ---
# This is CRUCIAL for Kivy to recognize the classes when used in KV files.
from components.three_day_calendar_view import ThreeDayCalendarView, AppointmentSlot

# Import necessary screens
from screens.dashboard_screen import DashboardScreen
from screens.new_appointment_screen import NewAppointmentScreen
from screens.new_client_screen import NewClientScreen
from screens.clients_screen import ClientsScreen
from screens.reminders_screen import RemindersScreen
# from screens.show_client_screen import ShowClientScreen # Commented out for now

# Import the DatabaseManager class from utils.db_manager
from utils.db_manager import DatabaseManager

# Import models (these will use the DatabaseManager internally)
from models.appointment import Appointment
from models.customer import Customer
# from kivymd.font_definitions import theme_font_styles
# print(theme_font_styles)
# Set the window size - useful for development
Window.size = (400, 700) # Typical phone aspect ratio

# Set Kivy minimum required version
kivy.require('2.3.0')

def show_error_popup(title, message):
    """Helper function to display an error popup."""
    popup = Popup(title=title,
                  content=Label(text=message, halign='center', valign='middle'),
                  size_hint=(None, None), size=(400, 200))
    popup.open()

def check_dependencies():
    """Placeholder for dependency checks if needed."""
    try:
        import openpyxl
        Logger.info("Dependency Check: openpyxl found.")
    except ImportError:
        Logger.warning("Dependency Check: openpyxl not found. Excel export will not work.")

# Add a simple KV string for MDApp, this is good practice for KivyMD apps
# It ensures that KivyMD's default components are properly initialized.
# We'll put our ScreenManager here.
kv_string = """
#:import FadeTransition kivy.uix.screenmanager.FadeTransition
ScreenManager:
    transition: FadeTransition()
    # Screens will be added dynamically in Python, or defined here directly
"""
class AppointmentApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"  # ή "Dark"
        self.theme_cls.primary_palette = "Indigo"
        # self.theme_cls.primary_palette = "Blue"
        # self.theme_cls.primary_hue = "500"
        # --- Set the background color of the window ---
        # RGBa values: (Red, Green, Blue, Alpha). Each from 0 to 1.
        # 0.9, 0.9, 0.9, 1 represents a light grey.
        Window.clearcolor = (0.9, 0.9, 0.9, 1) # <-- Εδώ ορίζουμε το φόντο

        try:
            db_instance = DatabaseManager()
            Logger.info("Database manager initialized and ready.")
        except Exception as e:
            Logger.critical(f"Database Manager Initialization Failed: {e}")
            show_error_popup("Σφάλμα Βάσης Δεδομένων", f"Αδυναμία σύνδεσης/εκκίνησης βάσης δεδομένων: {e}\nΗ εφαρμογή θα κλείσει.")
            sys.exit(1)

        self.format_date = lambda d: d.strftime("%d/%m/%Y") if isinstance(d, (date, datetime)) else ""

        # --- ΦΟΡΤΩΣΗ ΤΩΝ KV ΑΡΧΕΙΩΝ ΡΗΤΑ ---
        try:
            # IMPORTANT: Load component KV files BEFORE screen KV files that use them.
            # Use os.path.join(os.path.dirname(__file__), ...) to ensure correct paths.
            Builder.load_file(os.path.join(os.path.dirname(__file__), 'components', 'three_day_calendar_view.kv'))

            # with open('screens/dashboard.kv', 'r', encoding='utf-8') as f:
            #     Builder.load_string(f.read())
            # Now load screen KV files
            print("Φορτώνεται το dashboard.kv")
            # Builder.load_file(os.path.join(os.path.dirname(__file__), 'screens', 'dashboard.kv'))
            Builder.load_file('screens/dashboard.kv')
            Builder.load_file(os.path.join(os.path.dirname(__file__), 'screens', 'new_appointment.kv'))
            # Corrected syntax for new_client.kv: os.path.join(os.path.dirname(__file__), 'screens', 'new_client.kv')
            Builder.load_file(os.path.join(os.path.dirname(__file__), 'screens', 'new_client.kv')) 
            Builder.load_file(os.path.join(os.path.dirname(__file__), 'screens', 'clients.kv'))
            Builder.load_file(os.path.join(os.path.dirname(__file__), 'screens', 'reminders.kv'))

            Logger.info("KV files loaded successfully.")
        except Exception as e:
            Logger.critical(f"KV File Loading Failed: {e}")
            show_error_popup("Σφάλμα Φόρτωσης Διάταξης", f"Αποτυχία φόρτωσης KV αρχείων: {e}\nΗ εφαρμογή θα κλείσει.")
            sys.exit(1)

        sm = ScreenManager()

        sm.add_widget(DashboardScreen(name='dashboard_screen'))
        sm.add_widget(NewAppointmentScreen(name='new_appointment_screen'))
        sm.add_widget(NewClientScreen(name='new_client_screen'))
        sm.add_widget(ClientsScreen(name='clients_screen'))
        sm.add_widget(RemindersScreen(name='reminders_screen'))

        sm.current = 'dashboard_screen'
        return sm

    def on_stop(self):
        """Called when the application is stopped."""
        db_instance = DatabaseManager()
        db_instance.close_connection()
        Logger.info("Database connection closed.")

if __name__ == '__main__':
    check_dependencies()
    AppointmentApp().run()