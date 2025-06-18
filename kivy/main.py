#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Σύστημα Διαχείρισης Ραντεβού - Κομμώσεις για όλα τα γούστα
Entry point της εφαρμογής (Kivy version)
"""

import sys
import os

# Kivy imports
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.logger import Logger
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder # <-- Βεβαιωθείτε ότι αυτό είναι εδώ

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your custom screens
from screens.new_appointment_screen import NewAppointmentScreen
from screens.new_client_screen import NewClientScreen
# from screens.dashboard_screen import DashboardScreen # Uncomment when you create this

# Import the DatabaseManager to initialize the database
from utils.db_manager import DatabaseManager

def show_error_popup(title, message):
    """Displays an error popup using Kivy."""
    layout = BoxLayout(orientation='vertical', padding='10dp', spacing='10dp')
    layout.add_widget(Label(text=message, size_hint_y=None, height='100dp', halign='center', valign='middle', text_size=(layout.width, None)))
    close_button = Button(text='OK', size_hint_y=None, height='40dp')
    layout.add_widget(close_button)

    popup = Popup(title=title, content=layout, size_hint=(0.8, 0.5), auto_dismiss=False)
    close_button.bind(on_release=popup.dismiss)
    popup.open()

def check_dependencies():
    """Checks that all necessary libraries are installed before Kivy's full initialization."""
    missing_modules = []
    required_modules = {
        'kivy': 'kivy',
        'xlsxwriter': 'xlsxwriter',
    }
    for module_name, pip_name in required_modules.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_modules.append(pip_name)
    
    if missing_modules:
        error_msg = f"Missing the following libraries:\n{', '.join(missing_modules)}\n\n"
        error_msg += "Please install them using:\n"
        error_msg += f"pip install {' '.join(missing_modules)}"
        
        Logger.error('DependencyCheck: ' + error_msg)
        print("\n" + "*"*50)
        print("CRITICAL ERROR: DEPENDENCIES MISSING")
        print(error_msg)
        print("*"*50 + "\n")
        sys.exit(1)

# Define a dummy DashboardScreen for testing purposes
class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding='20dp', spacing='10dp')
        layout.add_widget(Label(text="Κεντρικός Πίνακας Ελέγχου (Για Δοκιμή)", font_size='28sp'))
        
        btn_go_to_new_appt = Button(
            text="Πήγαινε στο Νέο Ραντεβού",
            size_hint=(0.6, 0.2),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        btn_go_to_new_appt.bind(on_release=lambda x: self.change_screen('new_appointment_screen'))
        layout.add_widget(btn_go_to_new_appt)

        # --- ΝΕΟ ΚΟΥΜΠΙ ΓΙΑ ΤΗ NEW CLIENT SCREEN ---
        btn_go_to_new_client = Button(
            text="Πήγαινε στον Νέο Πελάτη",
            size_hint=(0.6, 0.2),
            pos_hint={'center_x': 0.5, 'center_y': 0.3} # Adjust position as needed
        )
        btn_go_to_new_client.bind(on_release=lambda x: self.change_screen('new_client_screen'))
        layout.add_widget(btn_go_to_new_client)
        # --- ΤΕΛΟΣ ΝΕΟΥ ΚΟΥΜΠΙΟΥ ---

        self.add_widget(layout)

    def change_screen(self, screen_name):
        self.manager.current = screen_name


class AppointmentApp(App):
    def build(self):
        # Initialize the database
        try:
            DatabaseManager()
            Logger.info("Database: salon_appointments_app.db initialized successfully.")
        except Exception as e:
            Logger.critical(f"Database Initialization Failed: {e}")
            show_error_popup("Σφάλμα Βάσης Δεδομένων", f"Αποτυχία αρχικοποίησης βάσης δεδομένων: {e}\nΗ εφαρμογή θα κλείσει.")
            sys.exit(1)

        # --- ΣΗΜΑΝΤΙΚΗ ΔΙΟΡΘΩΣΗ ΕΔΩ: ΦΟΡΤΩΣΗ ΤΩΝ KV ΑΡΧΕΙΩΝ ΡΗΤΑ ---
        # Φορτώστε το KV αρχείο για κάθε οθόνη.
        # Βεβαιωθείτε ότι η διαδρομή είναι σωστή.
        # Αν τα KV αρχεία σας είναι στο `kivy/screens/`, τότε η διαδρομή είναι σωστή.
        try:
            Builder.load_file(os.path.join(os.path.dirname(__file__), 'screens', 'new_appointment.kv'))
            Builder.load_file(os.path.join(os.path.dirname(__file__), 'screens', 'new_client.kv')) # <-- Προσθήκη αυτής της γραμμής
            # Builder.load_file(os.path.join(os.path.dirname(__file__), 'screens', 'dashboard.kv')) # Uncomment if you have a dashboard.kv
            Logger.info("KV files loaded successfully.")
        except Exception as e:
            Logger.critical(f"KV File Loading Failed: {e}")
            show_error_popup("Σφάλμα Φόρτωσης Διάταξης", f"Αποτυχία φόρτωσης KV αρχείων: {e}\nΗ εφαρμογή θα κλείσει.")
            sys.exit(1)

        sm = ScreenManager()
        
        # Add your screens to the ScreenManager
        sm.add_widget(DashboardScreen(name='dashboard_screen'))
        sm.add_widget(NewAppointmentScreen(name='new_appointment_screen'))
        sm.add_widget(NewClientScreen(name='new_client_screen')) # <-- Προσθήκη αυτής της γραμμής
        
        sm.current = 'dashboard_screen' 
        return sm

if __name__ == '__main__':
    check_dependencies()
    try:
        AppointmentApp().run()
    except Exception as e:
        error_msg = f"Unhandled error during Kivy app runtime:\n{str(e)}"
        Logger.exception('AppRuntimeError: ' + error_msg)
        if App.get_running_app():
            show_error_popup("Σφάλμα Εφαρμογής", error_msg)
        else:
            print(error_msg)
        sys.exit(1)