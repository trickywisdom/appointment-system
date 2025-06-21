# kivy/screens/dashboard_screen.py

from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.animation import Animation
from datetime import datetime, date, timedelta
from kivy.logger import Logger

from models.customer import Customer
from models.appointment import Appointment
from components.three_day_calendar_view import ThreeDayCalendarView
from uix.custom_date_picker import DatePickerPopup

class SearchModal(ModalView):
    search_results_container = ObjectProperty(None)
    search_input = ObjectProperty(None)

    def __init__(self, dashboard_screen, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.9, 0.7)
        self.pos_hint = {'center_x': 0.5, 'top': 0.95}
        self.background_color = [0, 0, 0, 0.5]
        self.dashboard_screen = dashboard_screen
        self.customers = Customer.get_all()
        self.bind(on_open=self.animate_open)
        self.bind(on_dismiss=self.animate_close)

    def animate_open(self, *args):
        self.opacity = 0
        self.pos_hint = {'center_x': 0.5, 'top': 0.6}
        anim = Animation(opacity=1, pos_hint={'center_x': 0.5, 'top': 0.95}, duration=0.3, transition='out_quad')
        anim.start(self)

    def animate_close(self, *args):
        anim = Animation(opacity=0, pos_hint={'center_x': 0.5, 'top': 0.6}, duration=0.2, transition='in_quad')
        anim.start(self)
        return False

    def filter_customers(self, search_text):
        if not self.search_results_container:
            Logger.warning("SearchModal: search_results_container is None")
            return

        self.search_results_container.clear_widgets()
        search_text = search_text.lower().strip()

        if not search_text:
            self.search_results_container.add_widget(
                Label(text="Πληκτρολογήστε όνομα ή τηλέφωνο", size_hint_y=None, height=dp(40))
            )
            return

        matching_customers = [
            c for c in self.customers
            if search_text in c.full_name.lower() or search_text in c.phone
        ]

        if not matching_customers:
            box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80))
            box.add_widget(
                Label(text="Δεν βρέθηκε ο πελάτης που ψάχνατε.", size_hint_y=None, height=dp(40))
            )
            btn = Button(
                text="Δημιουργία Νέου Πελάτη",
                size_hint_y=None,
                height=dp(40),
                background_color=[0.1, 0.5, 0.8, 1]
            )
            btn.bind(on_release=self.create_new_client)
            box.add_widget(btn)
            self.search_results_container.add_widget(box)
            return

        for customer in matching_customers:
            btn = Button(
                text=f"{customer.full_name} - {customer.phone}",
                size_hint_y=None,
                height=dp(50),
                background_normal='',
                background_color=[0.9, 0.9, 0.9, 1]
            )
            btn.customer = customer
            btn.bind(on_release=self.select_customer)
            self.search_results_container.add_widget(btn)

    def create_new_client(self, instance):
        self.dismiss()
        if self.dashboard_screen.manager:
            self.dashboard_screen.manager.current = 'new_client_screen'

    def select_customer(self, instance):
        self.dismiss()
        if self.dashboard_screen.manager:
            new_appt_screen = self.dashboard_screen.manager.get_screen('new_appointment_screen')
            new_appt_screen.customer_spinner.text = instance.customer.full_name
            self.dashboard_screen.manager.current = 'new_appointment_screen'

class DashboardScreen(Screen):
    month_display_label = ObjectProperty(None)
    current_display_date = ObjectProperty(date.today())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_modal = None
        self.date_picker_popup = None
        self.bind(current_display_date=self.update_calendar_view)

    def on_kv_post(self, base_widget):
        Clock.schedule_once(self.load_initial_data, 0)

    def load_initial_data(self, dt=0):
        self.load_3_day_appointments()

    def load_3_day_appointments(self):
        try:
            start_date = self.current_display_date
            appointments_data = []
            day_names = ['Δευ', 'Τρι', 'Τετ', 'Πεμ', 'Παρ', 'Σαβ', 'Κυρ']
            for i in range(3):
                current_date = start_date + timedelta(days=i)
                appointments = Appointment.get_by_date(current_date.strftime('%Y-%m-%d'))
                appt_list = [
                    {
                        'id': appt.id,
                        'customer_name': appt.customer_name,
                        'service_name': appt.services,
                        'datetime_obj': appt.datetime,
                        'duration': appt.duration
                    }
                    for appt in appointments
                ]
                appointments_data.append({
                    'date': current_date,
                    'day_name': day_names[current_date.weekday()],
                    'day_number': current_date.day,
                    'appointments': appt_list
                })
            if self.ids.three_day_view:
                self.ids.three_day_view.appointments_data = appointments_data
            else:
                Logger.warning("DashboardScreen: three_day_view not found in ids")
        except Exception as e:
            Logger.error(f"DashboardScreen: Error loading appointments: {e}")
            self.show_popup("Σφάλμα", f"Αποτυχία φόρτωσης ραντεβού: {e}")

    def update_calendar_view(self, instance, value):
        self.load_3_day_appointments()

    def open_search_modal(self):
        if not self.search_modal:
            self.search_modal = SearchModal(dashboard_screen=self)
        self.search_modal.open()

    def open_month_picker(self):
        if not self.date_picker_popup:
            self.date_picker_popup = DatePickerPopup(target_screen=self)
        self.date_picker_popup.selected_date = self.current_display_date
        self.date_picker_popup.open()

    def update_date_from_picker(self, selected_date):
        self.current_display_date = selected_date

    def animate_drawer_open(self, drawer):
        drawer.opacity = 0
        drawer.x = -drawer.width
        anim = Animation(opacity=1, x=0, duration=0.3, transition='out_quad')
        anim.start(drawer)

    def animate_drawer_close(self, drawer):
        anim = Animation(opacity=0, x=-drawer.width, duration=0.2, transition='in_quad')
        anim.start(drawer)

    def add_appointment_from_fab(self):
        if self.manager:
            self.manager.current = 'new_appointment_screen'

    def add_client_from_fab(self):
        if self.manager:
            self.manager.current = 'new_client_screen'

    def show_popup(self, title, message):
        popup = Popup(
            title=title,
            content=Label(text=message, halign='center', valign='middle'),
            size_hint=(None, None), size=(dp(400), dp(200))
        )
        popup.open()

    def show_coming_soon_popup(self, feature):
        self.show_popup("Υπό Κατασκευή", f"Η λειτουργία '{feature}' δεν είναι ακόμα διαθέσιμη.")