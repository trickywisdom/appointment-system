# kivy/screens/reminders_screen.py

from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, ListProperty, StringProperty, NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput # Added for date input display
from kivy.app import App

# --- Import the DatePickerPopup from its new location ---
from uix.custom_date_picker import DatePickerPopup

# # Imports for a basic DatePicker Popup (simplified)
# from kivy.uix.gridlayout import GridLayout
# from kivy.uix.floatlayout import FloatLayout
# from kivy.lang import Builder
# from kivy.core.window import Window
# from kivy.utils import get_color_from_hex

# Database Models
from models.appointment import Appointment # Keep this
from models.customer import Customer       # Keep this

from datetime import datetime, date, timedelta
import os # Needed for file operations (Excel export)
# For email and Excel, you'd typically need external libraries:
# import smtplib # For sending emails
# import openpyxl # For Excel export (pip install openpyxl)
# import pandas as pd # Alternative for Excel export (pip install pandas)

class ReminderListItem(ButtonBehavior, BoxLayout):
    # ... (no changes here, same as before) ...
    appointment_id = NumericProperty(0)
    time_slot = StringProperty('')
    customer_name = StringProperty('')
    service_name = StringProperty('')
    row_index = NumericProperty(-1)

    def show_appointment_details(self):
        print(f"Showing details for appointment ID: {self.appointment_id}")
        screen = self.parent.parent.parent.parent
        screen.show_popup("Λεπτομέρειες Ραντεβού",
            f"Ωράριο: {self.time_slot}\n"
            f"Πελάτης: {self.customer_name}\n"
            f"Υπηρεσία: {self.service_name}")


class RemindersScreen(Screen):
    appointment_list_rv = ObjectProperty(None)
    rv_data = ListProperty([])
    selected_date_input = ObjectProperty(None)
    current_date = ObjectProperty(date.today())

    def on_kv_post(self, base_widget):
        self.app = App.get_running_app()  # <-- σταθερό, χωρίς εξάρτηση από manager
        self.update_date_display()

    def on_enter(self, *args):
        self.update_date_display()
        self.load_appointments_for_date()

    def update_date_display(self):
        if self.selected_date_input:
            self.selected_date_input.text = self.app.format_date(self.current_date)

    def open_date_picker(self):
        # Pass the current screen as target_screen
        picker = DatePickerPopup(target_screen=self)
        picker.open()

    def update_date_from_picker(self, new_date):
        self.current_date = new_date
        self.update_date_display()
        self.load_appointments_for_date()

    def load_appointments_for_date(self):
        # ... (no changes here, same as before) ...
        try:
            all_appointments = Appointment.get_all()
            
            appointments_for_selected_date = []
            for appt in all_appointments:
                appt_datetime_obj = datetime.strptime(appt.datetime, "%Y-%m-%d %H:%M")
                
                if appt_datetime_obj.date() == self.current_date:
                    appointments_for_selected_date.append(appt)
            
            appointments_for_selected_date.sort(key=lambda x: datetime.strptime(x.datetime, "%Y-%m-%d %H:%M"))

            self.rv_data = []
            for i, appt in enumerate(appointments_for_selected_date):
                customer_full_name = "Άγνωστος Πελάτης"
                
                if appt.customer_id:
                    customer = Customer.get_by_id(appt.customer_id)
                    if customer:
                        customer_full_name = f"{customer.first_name} {customer.last_name}"
                
                start_dt = datetime.strptime(appt.datetime, "%Y-%m-%d %H:%M")
                end_dt = start_dt + timedelta(minutes=appt.duration)
                
                time_slot_str = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"

                self.rv_data.append({
                    'appointment_id': appt.id,
                    'time_slot': time_slot_str,
                    'customer_name': customer_full_name,
                    'service_name': appt.services,
                    'row_index': i
                })
            
            print(f"Loaded {len(self.rv_data)} appointments for {self.current_date}")

        except Exception as e:
            self.show_popup("Σφάλμα Φόρτωσης Ραντεβού", f"Αποτυχία φόρτωσης ραντεβού: {e}")
            self.rv_data = []

    def send_email_reminders(self):
        # ... (no changes here, same as before) ...
        if not self.rv_data:
            self.show_popup("Προσοχή", "Δεν υπάρχουν ραντεβού για αποστολή υπενθυμίσεων.")
            return

        email_count = len(self.rv_data)
        self.show_popup("Αποστολή Email", f"Θα αποσταλούν {email_count} email υπενθυμίσεις για την {self.app.format_date(self.current_date)}.")
        print(f"Would send emails for appointments on {self.current_date}")

    def export_to_excel(self):
        # ... (no changes here, same as before) ...
        if not self.rv_data:
            self.show_popup("Προσοχή", "Δεν υπάρχουν ραντεβού για εξαγωγή σε Excel.")
            return

        try:
            import openpyxl
            from openpyxl.styles import Font, Alignment

            headers = ["Ωριαίο Διάστημα", "Ονοματεπώνυμο Πελάτη", "Υπηρεσία"]
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = f"Appointments_{self.current_date.strftime('%Y%m%d')}"

            ws.append(headers)
            header_font = Font(bold=True)
            for cell in ws[1]:
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')

            for row_data in self.rv_data:
                ws.append([row_data['time_slot'], row_data['customer_name'], row_data['service_name']])
            
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.2
                ws.column_dimensions[column].width = adjusted_width

            reports_dir = os.path.join(self.app.user_data_dir, "reports")
            os.makedirs(reports_dir, exist_ok=True)
            file_path = os.path.join(reports_dir, f"Ραντεβού_{self.current_date.strftime('%Y-%m-%d')}.xlsx")
            
            wb.save(file_path)
            self.show_popup("Επιτυχία", f"Το αρχείο Excel δημιουργήθηκε:\n{file_path}")
            print(f"Excel file created: {file_path}")
            
        except ImportError:
            self.show_popup("Σφάλμα", "Η βιβλιοθήκη 'openpyxl' δεν βρέθηκε. Παρακαλώ εγκαταστήστε την (pip install openpyxl).")
        except Exception as e:
            self.show_popup("Σφάλμα Εξαγωγής Excel", f"Αποτυχία δημιουργίας αρχείου Excel: {e}")

    def show_popup(self, title, message):
        popup = Popup(title=title,
                      content=Label(text=message, halign='center', valign='middle'),
                      size_hint=(None, None), size=(dp(400), dp(200)))
        popup.open()

    def go_back(self):
        self.manager.current = 'dashboard_screen'
