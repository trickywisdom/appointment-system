# kivy/screens/dashboard_screen.py
# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kivy.logger import Logger
from kivy.uix.screenmanager import Screen
from kivymd.uix.behaviors import DeclarativeBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.properties import ObjectProperty, StringProperty, ListProperty, NumericProperty, BooleanProperty
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.utils import get_color_from_hex
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from datetime import datetime, date, timedelta
from kivy.animation import Animation

# Imports for modals
from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView
from kivy.animation import Animation
from kivy.uix.textinput import TextInput

# KivyMD Imports
# from kivymd.uix.screen import MDScreen
# from kivy.uix.screenmanager import Screen
from kivymd.uix.button import MDButton, MDIconButton, MDFabButton
from kivymd.uix.button import MDButtonText # Only MDButtonText is needed for composing text
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.navigationdrawer import MDNavigationDrawer, MDNavigationLayout # <-- ADDED THIS LINE (already there, just making sure)
# from kivymd.uix.navigationdrawer import MDNavigationDrawerHeader
# from kivymd.uix.navigationdrawer import MDNavigationDrawerItem
from kivy.uix.widget import Widget 

# Model and custom UI imports
from models.appointment import Appointment
from models.customer import Customer
from uix.custom_date_picker import DatePickerPopup

# Builder.load_string for small, contained KV for things like Modal Search
Builder.load_string("""
<SearchModal>:
    size_hint: 1, 1
    background_color: 0, 0, 0, 0.7
    orientation: 'vertical'

    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: self.minimum_height
        spacing: dp(10)
        padding: dp(10)
        canvas.before:
            Color:
                rgba: 0.93, 0.93, 0.93, 1
            Rectangle:
                pos: self.pos
                size: self.size

        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(10)
            TextInput:
                id: search_input
                hint_text: "Αναζήτηση πελάτη (όνομα/τηλέφωνο)"
                font_size: '18sp'
                padding: dp(10)
                multiline: False
                on_text: root.filter_customers(self.text)
            MDIconButton:
                icon: 'close'
                size_hint_x: None
                width: dp(48)
                on_release: root.dismiss()
                # theme_text_color: 'Custom' # This is for custom palette colors. Not for rgba.
                # text_color: 1, 1, 1, 1 # <--- REMOVED! Use theme_text_color or specific_text_color if customizing, or let theme handle.
                md_bg_color: 0.8, 0.2, 0.2, 1 # This is the background color of the button
        
        ScrollView:
            size_hint_y: None
            height: self.parent.height * 0.7 if self.children else 0
            do_scroll_y: True
            GridLayout:
                id: search_results_grid
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(2)
                padding: dp(2)
        
        MDLabel:
            id: no_results_label
            text: "Δεν βρέθηκε ο πελάτης που ψάχνατε."
            font_style: 'Body'
            role: 'medium'
            halign: 'center'
            valign: 'middle'
            size_hint_y: None
            height: dp(0)
            opacity: 0

        MDButton: # Changed from MDRaisedButton to MDButton with style="elevated"
            id: new_customer_button
            MDButtonText: # Text goes inside MDButtonText
                text: "Δημιουργία Νέου Πελάτη"
                style: "elevated" # KivyMD 2.x equivalent for a "raised" button
                size_hint_y: None
                height: dp(0)
                opacity: 0
                on_release: root.create_new_customer()
                md_bg_color: 0.2, 0.6, 0.2, 1
                # text_color: 1, 1, 1, 1 # <--- REMOVED! MDButton with style "elevated" handles text color automatically for contrast.
""")


class SearchModal(ModalView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auto_dismiss = False
        self.dashboard_screen = None

    def on_open(self):
        self.y = Window.height
        anim = Animation(y=0, duration=0.3, transition='out_quad')
        anim.start(self)
        self.ids.search_input.focus = True

    def dismiss(self, *largs, **kwargs):
        anim = Animation(y=Window.height, duration=0.3, transition='in_quad')
        anim.bind(on_complete=super().dismiss)
        anim.start(self)
    
    def filter_customers(self, query):
        grid = self.ids.search_results_grid
        grid.clear_widgets()
        
        no_results_label = self.ids.no_results_label
        new_customer_button = self.ids.new_customer_button

        no_results_label.height = dp(0)
        no_results_label.opacity = 0
        new_customer_button.height = dp(0)
        new_customer_button.opacity = 0
        self.ids.search_results_grid.parent.height = 0

        if not query:
            return

        all_customers = Customer.get_all()

        query = query.lower()
        
        found_customers = []
        for customer in all_customers:
            if query in customer.first_name.lower() or \
               query in customer.last_name.lower() or \
               query in (customer.phone or "").lower():
                found_customers.append(customer)
        
        if found_customers:
            for customer in found_customers:
                btn = MDButton( # Changed to MDButton
                    MDButtonText(text=f"{customer.first_name} {customer.last_name} - {customer.phone or ''}"), # Text now goes inside MDButtonText
                    style="text", # This makes it a "flat" button in MD3
                    size_hint_y=None,
                    height=dp(48),
                    # halign and valign are properties of MDButtonText inside MDButton
                    # text_size is also a property of MDButtonText
                )
                # Accessing the MDButtonText child to set alignment and text_size
                if btn.children and isinstance(btn.children[0], MDButtonText):
                    btn.children[0].halign = 'left'
                    btn.children[0].valign = 'middle'
                    btn.children[0].text_size = (grid.width - dp(20), None) # Added some padding
                
                btn.customer_id = customer.id
                btn.bind(on_release=self.select_customer)
                grid.add_widget(btn)
            self.ids.search_results_grid.parent.height = min(dp(300), self.ids.search_results_grid.minimum_height) # Max height 300dp
        else:
            no_results_label.height = dp(40)
            no_results_label.opacity = 1
            new_customer_button.height = dp(48)
            new_customer_button.opacity = 1


    def select_customer(self, instance):
        customer_id = instance.customer_id
        if self.dashboard_screen:
            if self.dashboard_screen.manager.has_screen('new_appointment_screen'):
                self.dashboard_screen.manager.get_screen('new_appointment_screen').selected_customer_id = customer_id
                self.dashboard_screen.manager.current = 'new_appointment_screen'
            else:
                Logger.warning("SearchModal: 'new_appointment_screen' not found in manager.")
        self.dismiss()

    def create_new_customer(self):
        if self.dashboard_screen:
            if self.dashboard_screen.manager.has_screen('new_client_screen'):
                self.dashboard_screen.manager.current = 'new_client_screen'
            else:
                Logger.warning("SearchModal: 'new_client_screen' not found in manager.")
        self.dismiss()

class FABMenu(FloatLayout):
    is_open = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # We don't set initial opacity/disabled here, KV handles it.
        # self.closed_y is not strictly needed if we calculate based on current state.

    def toggle_menu(self):
        # Access the main FAB button to change its icon
        main_fab = self.ids.main_fab
        
        # Access the container for the menu items
        menu_content = self.ids.menu_items_container

        # Ensure menu_content's height is correctly calculated before animation
        menu_content.height = menu_content.minimum_height

        # Define initial FABMenu height (when closed, it's just the FAB's height)
        # This assumes the main FAB button inside FABMenu has a size of dp(56), dp(56)
        initial_fab_menu_height = dp(56)
        
        # Define the target height for FABMenu when open
        # This is main FAB height + spacing + menu items height + some bottom padding
        target_fab_menu_height = initial_fab_menu_height + dp(10) + menu_content.height + dp(10)

        # Define the initial y-position of FABMenu (from the KV's parent FloatLayout)
        # This needs to match the 'pos: ..., dp(20)' in dashboard.kv for the FABMenu instance.
        initial_fab_menu_y = dp(20) # This is the y in the parent FloatLayout

        if not self.is_open:
            # When opening:
            self.opacity = 1
            self.disabled = False
            
            # Animate FABMenu's height and y-position to slide up
            anim_fab_menu = Animation(
                y=initial_fab_menu_y + (target_fab_menu_height - initial_fab_menu_height),
                height=target_fab_menu_height,
                duration=0.2,
                transition='out_quad'
            )
            anim_fab_menu.start(self)

            # Change icon for the main FAB button
            main_fab.icon = "close"
            
        else:
            # When closing:
            # Animate FABMenu's height and y-position back to initial state
            anim_fab_menu = Animation(
                y=initial_fab_menu_y,
                height=initial_fab_menu_height,
                opacity=0, # Hide FABMenu
                duration=0.2,
                transition='in_quad'
            )
            # Disable FABMenu when animation completes (so it doesn't receive touch events when hidden)
            anim_fab_menu.bind(on_complete=lambda *args: setattr(self, 'disabled', True))
            anim_fab_menu.start(self)
            
            # Change icon back to plus
            main_fab.icon = "plus"
            
        self.is_open = not self.is_open


class DashboardScreen(DeclarativeBehavior, Screen): # Συνδυάζουμε MD συμπεριφορά με Screen
    current_display_date = ObjectProperty(date.today())
    appointments_data = ListProperty([])
    month_display_label = ObjectProperty(None)
    # No longer need to define navigation_drawer as an ObjectProperty here,
    # as it's directly accessed via self.ids from KV.
    drawer_blocker = None  # το ModalView που μπλοκάρει τις αλληλεπιδράσεις
    drawer_is_open = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.swipe_start_x = 0
        self.swipe_threshold = 0.2
        self.bind(current_display_date=self.on_current_display_date_changed)
        # self.swipe_enabled = True
        # self.bind(drawer_is_open=self.on_drawer_toggle)
        
    def on_kv_post(self, base_widget):
        Logger.info("DashboardScreen: on_kv_post called.")
        
        # Pass dashboard_screen reference to three_day_view
        if 'three_day_view' in self.ids:
            self.ids.three_day_view.dashboard_screen = self
            Logger.info("DashboardScreen: DashboardScreen reference passed to three_day_view.")
        else:
            Logger.warning("DashboardScreen: 'three_day_view' not found in self.ids after kv_post.")
        
        # Ensure month_display_label is an MDLabel instance from KV
        # This part might need adjustment if month_display_label is defined in dashboard.kv
        # and you want to ensure it's an MDLabel. Assuming it's already an MDLabel via KV.
        # If it's a simple Label in KV, change it to MDLabel in dashboard.kv
        # self.month_display_label refers to the Button with id: month_label_id in KV.
        # Its text is set via its MDButtonText child.
        if isinstance(self.month_display_label, Button): # It's a Button in KV!
            Logger.info("DashboardScreen: month_display_label is a Kivy Button. Attempting to update its text via its child MDButtonText.")
        
        self.update_top_bar_month()

    def on_enter(self, *args):
        Logger.info("DashboardScreen: on_enter called.")
        self.update_top_bar_month()
        self.load_3_day_appointments()

    def on_current_display_date_changed(self, instance, value):
        Logger.info(f"DashboardScreen: current_display_date changed to {value}. Reloading appointments.")
        self.update_top_bar_month()
        self.load_3_day_appointments()

    def update_top_bar_month(self):
        if self.month_display_label:
            new_text = self.current_display_date.strftime("%B").capitalize()
            self.month_display_label.text = new_text
            Logger.info(f"DashboardScreen: TopAppBar title updated to {new_text}")
        else:
            Logger.warning("DashboardScreen: month_display_label not found, cannot update title")

    def open_nav_drawer(self):
        Logger.info("DashboardScreen: Attempting to open Navigation Drawer")
        try:
            self.ids.nav_drawer.set_state("toggle")
            self.print_nav_layout_z_order()
            Logger.info("DashboardScreen: Navigation Drawer toggled")
            # self.ids.three_day_view.disabled = True  # Απενεργοποιεί όλα τα touches
            # self.ids.nav_drawer.set_state("open")
        except Exception as e:
            Logger.error(f"DashboardScreen: Failed to open Navigation Drawer: {e}")

    def print_nav_layout_z_order(self):
        print("Z-Index rendering order (last is on top):")
        for i, child in enumerate(self.ids.nav_layout.children[::-1]):
            print(f"Z {i}: {child.__class__.__name__} | id: {getattr(child, 'id', 'n/a')}")

    # def animate_drawer_content(self):
    #     Logger.info("DashboardScreen: Animating drawer content")
    #     button_ids = [
    #         'new_appointment_btn', 'new_client_btn', 'clients_list_btn',
    #         'daily_appointments_btn', 'reports_btn', 'settings_btn'
    #     ]
    #     for idx, btn_id in enumerate(button_ids):
    #         btn = self.ids.get(btn_id)
    #         if btn:
    #             anim = Animation(opacity=1, duration=0.3 + idx * 0.05, transition='out_quad')
    #             anim.start(btn)
    #         else:
    #             Logger.warning(f"DashboardScreen: Button ID '{btn_id}' not found")

    # def on_drawer_state_change(self, state):
    #     if state == "open":
    #         Logger.info("DashboardScreen: Drawer opened")
    #         self.swipe_enabled = False
    #     elif state == "close":
    #         Logger.info("DashboardScreen: Drawer closed")
    #         self.swipe_enabled = True

    # def on_drawer_state_change(self, state):
    #     Logger.info(f"Drawer state changed to: {state}")
    #     if state == "open":
    #         # Άνοιγμα ModalView για block interaction
    #         self.drawer_blocker = ModalView(auto_dismiss=False, background_color=(0, 0, 0, 0))
    #         self.drawer_blocker.open()
    #     elif state == "close" and self.drawer_blocker:
    #         # Κλείσιμο ModalView
    #         self.drawer_blocker.dismiss()
    #         self.drawer_blocker = None

    # def on_drawer_state_change(self, state):
    #     if state == "open":
    #         # Απενεργοποίηση του κύριου περιεχομένου
    #         self.ids.three_day_view.disabled = True
    #         self.ids.top_app_bar_id.disabled = True
    #     else:
    #         # Επανενεργοποίηση
    #         self.ids.three_day_view.disabled = False
    #         self.ids.top_app_bar_id.disabled = False

    # def on_drawer_toggle(self, instance, value):
    #     # Αυτόματα τρέχει όταν αλλάζει το drawer_is_open
    #     Logger.info(f"Drawer toggle: {value}")
    #     if hasattr(self, 'three_day_view'):
    #         self.ids.three_day_view.disabled = value

    def on_drawer_state_change(self, state):
        Logger.info(f"Drawer state changed to: {state}")
        if state == "open":
            self.drawer_is_open = True
            Logger.info("DashboardScreen: Navigation Drawer opened")
            # # Απενεργοποίηση του background
            # if 'three_day_view' in self.ids:
            #     self.ids.three_day_view.disabled = True
            #     Logger.info("DashboardScreen: Main content disabled")
        elif state == "close":
            Logger.info("DashboardScreen: Navigation Drawer closed")
            self.drawer_is_open = False
            # # Ενεργοποίηση του background
            # if 'three_day_view' in self.ids:
            #     self.ids.three_day_view.disabled = False
            #     Logger.info("DashboardScreen: Main content enabled")

    def change_screen_and_dismiss_drawer(self, screen_name):
        print(f"IDS: {self.ids.keys()}")
        print("hello1")
        print(f"Switching to screen: {screen_name}")
        print(f"Available screens: {[screen.name for screen in self.ids.screen_manager.screens]}")
        self.ids.screen_manager.current = screen_name
        if 'nav_layout' in self.ids:
            self.ids.nav_layout.toggle_nav_drawer()
            # self.ids.three_day_view.disabled = False
            # self.ids.nav_drawer.set_state("close")
            print("hello2")
    
    # def printme(self):
    #     print("Hello3")

    def open_month_picker(self):
        Logger.info("DashboardScreen: Opening Month Picker.")
        picker = DatePickerPopup(target_screen=self)
        picker.current_date = self.current_display_date
        picker.open()
        
    def update_date_from_picker(self, new_date):
        Logger.info(f"DashboardScreen: Date selected from picker: {new_date}.")
        self.current_display_date = new_date

    def increment_display_date(self, days=3):
        self.current_display_date += timedelta(days=days)

    def decrement_display_date(self, days=3):
        self.current_display_date -= timedelta(days=days)

    def open_search_modal(self):
        Logger.info("DashboardScreen: Opening Search Modal.")
        search_modal = SearchModal()
        search_modal.dashboard_screen = self
        search_modal.open()

    def add_appointment_from_fab(self):
        Logger.info("DashboardScreen: Navigating to New Appointment Screen from FAB.")
        self.ids.screen_manager.current = 'new_appointment_screen'

    def add_client_from_fab(self):
        Logger.info("DashboardScreen: Navigating to New Client Screen from FAB.")
        self.ids.screen_manager.current = 'new_client_screen'

    def load_3_day_appointments(self):
        Logger.info(f"DashboardScreen: Loading 3-day appointments starting from {self.current_display_date}.")
        
        start_date = self.current_display_date
        three_days_data = []
            
        all_appointments = Appointment.get_all()

        for i in range(3):
            day_date = start_date + timedelta(days=i)
            day_appointments_list = []
            
            for appt in all_appointments:
                if isinstance(appt.datetime, datetime) and appt.datetime.date() == day_date:
                    customer_name = appt.customer_name if appt.customer_name else "Άγνωστος Πελάτης"
                    
                    day_appointments_list.append({
                        'id': appt.id,
                        'datetime_obj': appt.datetime,
                        'start_time': appt.datetime.strftime('%H:%M'),
                        'end_time': (appt.datetime + timedelta(minutes=appt.duration)).strftime('%H:%M'),
                        'customer_name': customer_name,
                        'service_name': appt.services if appt.services and appt.services != "None" else "Δεν ορίστηκε υπηρεσία",
                        'duration': appt.duration
                    })
            
            day_appointments_list.sort(key=lambda x: x['datetime_obj'])
            
            three_days_data.append({
                'date': day_date,
                'day_name': self.get_day_name_in_greek(day_date.weekday()),
                'day_number': day_date.day,
                'appointments': day_appointments_list
            })
        
        if 'three_day_view' in self.ids:
            self.ids.three_day_view.appointments_data = three_days_data
            Logger.info(f"DashboardScreen: Sent {len(three_days_data)} days of data to three_day_view.")
        else:
            Logger.error("DashboardScreen: 'three_day_view' ID not found in DashboardScreen. Cannot update calendar.")


    def get_day_name_in_greek(self, weekday_int):
        day_names = ["Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή", "Σάββατο", "Κυριακή"]
        return day_names[weekday_int]

    def show_popup(self, title, message):
        # Now using MDDialog for consistency
        dialog = MDDialog(
            title=title,
            text=message,
            buttons=[
                MDButton( # Changed to MDButton
                    MDButtonText(text="OK"), # Text goes inside MDButtonText
                    style="text", # This gives it the "flat" button appearance
                    on_release=lambda x: dialog.dismiss()
                )
            ],
        )
        dialog.open()
    
    # def on_touch_down(self, touch):
    #     if 'three_day_view' in self.ids and self.ids.three_day_view.collide_point(*touch.pos):
    #         self._touch_down_pos = touch.pos
    #         return True
    #     return super().on_touch_down(touch)
    # def on_touch_down(self, touch):
    #     if 'three_day_view' in self.ids and self.ids.three_day_view.collide_point(*touch.pos):
    #             self._touch_down_pos = touch.pos
    #             # ΜΗΝ επιστρέφεις True εδώ!
    #     return super().on_touch_down(touch)
    
    # def on_touch_down(self, touch):
    #     print("Touch down at:", touch.pos)
    #     for widget in self.ids.nav_layout.children:
    #         if widget.collide_point(*touch.pos):
    #             print(f"Touched: {widget.__class__.__name__} (id: {getattr(widget, 'id', 'n/a')})")
    #             break
    #     return super().on_touch_down(touch)

    # def on_touch_up(self, touch):
    #     if hasattr(self, '_touch_down_pos'):
    #         if 'three_day_view' in self.ids and self.ids.three_day_view.collide_point(*touch.pos):
    #             dx = touch.x - self._touch_down_pos[0]
    #             if abs(dx) > dp(50) and abs(touch.y - self._touch_down_pos[1]) < dp(50):
    #                 if dx > 0:
    #                     Logger.info("DashboardScreen: Swipe Right detected.")
    #                     self.current_display_date -= timedelta(days=3)
    #                 else:
    #                     Logger.info("DashboardScreen: Swipe Left detected.")
    #                     self.current_display_date += timedelta(days=3)
    #             del self._touch_down_pos
    #             return True
    #     return super().on_touch_up(touch)
    
    def on_touch_down(self, touch):
        print("Touch down at:", touch.pos)

        for widget in self.ids.nav_layout.children:
            if widget.collide_point(*touch.pos):
                print(f"Touched: {widget.__class__.__name__} (id: {getattr(widget, 'id', 'n/a')})")
                break

        if 'three_day_view' in self.ids and self.ids.three_day_view.collide_point(*touch.pos):
            self._touch_down_pos = touch.pos
            print(f"Touched2: {widget.__class__.__name__} (id: {getattr(widget, 'id', 'n/a')})")
            # ΜΗΝ επιστρέφεις True εδώ!
        return super().on_touch_down(touch)

    # def on_touch_down(self, touch):
    #     print(f"Touch down at: {touch.pos}")
    #     for widget in self.ids.nav_layout.children:
    #         if widget.collide_point(*touch.pos):
    #             print(f"Touched: {widget.__class__.__name__} (id: {getattr(widget, 'id', 'n/a')})")
    #             break

    #     # Πριν κάνουμε swipe check, δες αν το calendar το λαμβάνει
    #     if 'three_day_view' in self.ids:
    #         cal = self.ids.three_day_view
    #         print(f"ThreeDayCalendarView pos={cal.pos}, size={cal.size}")
    #         print(f"Touch inside calendar: {cal.collide_point(*touch.pos)}")

    #     # Αφήνουμε το touch να περάσει προς τα κάτω
    #     return super().on_touch_down(touch)
        
    
    def on_touch_up(self, touch):
    # Επιτρέπουμε πρώτα στα children να χειριστούν το touch
        if super().on_touch_up(touch):
            return True

        if hasattr(self, '_touch_down_pos'):
            if 'three_day_view' in self.ids and self.ids.three_day_view.collide_point(*touch.pos) and not self.drawer_is_open:
                dx = touch.x - self._touch_down_pos[0]
                dy = touch.y - self._touch_down_pos[1]
                if abs(dx) > dp(50) and abs(dy) < dp(50):  # swipe μόνο οριζόντια
                    if dx > 0:
                        Logger.info("DashboardScreen: Swipe Right detected.")
                        print("DashboardScreen: Swipe Right detected.")
                        self.current_display_date -= timedelta(days=3)
                    else:
                        Logger.info("DashboardScreen: Swipe Left detected.")
                        print("DashboardScreen: Swipe Left detected.")
                        self.current_display_date += timedelta(days=3)
                del self._touch_down_pos
                return True

        return False

    def show_appointment_details_popup(self, appointment_id):
        Logger.info(f"DashboardScreen: Showing details for appointment ID: {appointment_id}")
        appointment = Appointment.get_by_id(appointment_id)
        if appointment:
            customer_name = appointment.customer_name if appointment.customer_name else "Άγνωστος Πελάτης"
            service_name = appointment.services if appointment.services and appointment.services != "None" else "Δεν ορίστηκε υπηρεσία"

            popup_content = f"Πελάτης: {customer_name}\n" \
                            f"Υπηρεσία: {service_name}\n" \
                            f"Ώρα: {appointment.datetime.strftime('%H:%M')} - {(appointment.datetime + timedelta(minutes=appointment.duration)).strftime('%H:%M')}\n" \
                            f"Σημειώσεις: {appointment.notes or 'Καμία'}"
            
            # Using MDDialog for appointment details popup
            # Create content as a separate widget to pass to content_cls
            content_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
            content_layout.add_widget(MDLabel(text=popup_content, halign='left', valign='top', text_size=(dp(380), None), font_style='Body', role='medium'))
            
            # Button for the dialog. Use MDButton with style="text" for flat appearance inside dialogs
            btn_close = MDButton( # Changed from MDFlatButton to MDButton
                MDButtonText(text='Κλείσιμο'), # Text goes inside MDButtonText
                style="text" # This gives it the "flat" button appearance
            )

            dialog = MDDialog(
                title='Λεπτομέρειες Ραντεβού',
                type="custom", # Use "custom" type to put your own content
                content_cls=content_layout, # Pass the BoxLayout directly as content_cls
                buttons=[btn_close] # Buttons go here if not part of content_cls
            )
            btn_close.bind(on_release=dialog.dismiss)
            dialog.open()
        else:
            Logger.warning(f"Appointment with ID {appointment_id} not found.")