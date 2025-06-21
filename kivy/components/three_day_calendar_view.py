# kivy/components/three_day_calendar_view.py

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.properties import ListProperty, ObjectProperty, StringProperty
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from datetime import datetime, date, timedelta

# Import the AppointmentSlot widget (which we'll define in KV/Python)
# from kivy.uix.floatlayout import FloatLayout # If AppointmentSlot becomes complex


class AppointmentSlot(Button):
    """
    A custom button to represent an appointment slot in the calendar view.
    It can represent either an empty slot or an existing appointment.
    """
    background_color_rgba = ListProperty([0, 0, 0, 0]) # Default transparent
    display_text = StringProperty("")
    
    # Properties to hold appointment data if this slot represents an actual appointment
    appointment_id = ObjectProperty(None) # None for empty slots
    slot_datetime = ObjectProperty(None) # The specific datetime this slot represents

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(on_release=self._on_slot_press)
        # Ensure that button background is not drawn by default Kivy button logic
        self.background_normal = ''
        self.background_down = '' # No change on press for now, handled by color

    def _on_slot_press(self, instance):
        if self.appointment_id:
            # If it's an existing appointment, open details/edit popup
            print(f"Clicked existing appointment: ID {self.appointment_id} at {self.slot_datetime.strftime('%H:%M')}")
            # This logic will be handled by the parent ThreeDayCalendarView or DashboardScreen
            if self.parent and hasattr(self.parent, 'on_appointment_clicked'):
                self.parent.on_appointment_clicked(self.appointment_id)
        else:
            # If it's an empty slot, navigate to NewAppointmentPage with pre-filled date/time
            print(f"Clicked empty slot: {self.slot_datetime.strftime('%Y-%m-%d %H:%M')}")
            # This logic will be handled by the parent ThreeDayCalendarView or DashboardScreen
            if self.parent and hasattr(self.parent, 'on_empty_slot_clicked'):
                self.parent.on_empty_slot_clicked(self.slot_datetime)


class ThreeDayCalendarView(BoxLayout):
    """
    A custom widget that displays appointments for three consecutive days,
    mimicking the Google Calendar 3-day view.
    """
    appointments_data = ListProperty([]) # Will receive data from DashboardScreen

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal' # This is already set in KV, but good practice
        self.bind(appointments_data=self.on_appointments_data_changed)
        self.app = None # Reference to the Kivy App instance
        self.dashboard_screen = None # Reference to the DashboardScreen instance

        # Define salon operating hours
        self.start_hour = 10
        self.end_hour = 20 # Up to 20:00 (8 PM)
        self.hour_step = 60 # Minutes per slot (e.g., 60 for hourly, 30 for half-hourly)

        # New lists to store references to the day name and number labels
        self.day_name_labels = []
        self.day_num_labels = []

        self.setup_calendar_grid()

    def on_kv_post(self, base_widget):
        # We need a reference to the app and dashboard screen for navigation
        # This will be set by the DashboardScreen itself after it's built.
        pass # The setup_calendar_grid is called in __init__ for initial layout

    def setup_calendar_grid(self):
        """
        Sets up the static time labels and the dynamic day columns.
        This method is called once to build the basic structure.
        """
        self.clear_widgets() # Clear any existing widgets
        self.day_name_labels = [] # Clear previous references
        self.day_num_labels = []  # Clear previous references


        # 1. Time Column (Left side, fixed)
        time_column = BoxLayout(orientation='vertical', size_hint_x=None, width=dp(50))
        time_column.add_widget(Label(text='', size_hint_y=None, height=dp(40))) # Empty space for day headers
        for hour in range(self.start_hour, self.end_hour + 1): # Include end_hour for 20:00
            time_column.add_widget(Label(text=f'{hour:02d}:00', size_hint_y=None, height=dp(50), color=(0,0,0,1))) # 50dp per hour slot
        self.add_widget(time_column)

        # 2. Three Day Columns (Dynamic content will be added here)
        self.day_columns = []
        for i in range(3):
            day_column_container = BoxLayout(orientation='vertical', size_hint_x=1)
            
            # Create Labels and store references, WITHOUT 'id' property
            day_name_label = Label(text='', size_hint_y=None, height=dp(20), color=(0,0,0,1), font_size='13sp')
            day_num_label = Label(text='', size_hint_y=None, height=dp(20), color=(0,0,0,1), font_size='16sp', bold=True)
            
            day_column_container.add_widget(day_name_label)
            day_column_container.add_widget(day_num_label)
            
            self.day_name_labels.append(day_name_label) # Store reference
            self.day_num_labels.append(day_num_label)   # Store reference
            
            # ScrollView for the actual appointment slots
            scroll_view = ScrollView(do_scroll_y=True, do_scroll_x=False)
            
            # Grid for hour slots (rows will be hours, 1 column for appts)
            day_grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(1), padding=dp(2))
            day_grid.bind(minimum_height=day_grid.setter('height')) # Auto-adjust height based on content
            
            # Add placeholder slots for all hours, initially empty
            for hour in range(self.start_hour, self.end_hour + 1):
                slot_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(50)) # 50dp per hour slot
                slot_box.add_widget(Label(text='', size_hint_y=1)) # Placeholder for potential appointment
                slot_box.hour = hour # Store hour for easy reference
                day_grid.add_widget(slot_box)

            scroll_view.add_widget(day_grid)
            day_column_container.add_widget(scroll_view)
            self.add_widget(day_column_container)
            self.day_columns.append({'container': day_column_container, 'grid': day_grid, 'scroll_view': scroll_view})

    def on_appointments_data_changed(self, instance, value):
        """
        Called when appointments_data property changes.
        This method updates the visual representation of appointments.
        """
        self.refresh_appointments(value)

    def refresh_appointments(self, data):
        """
        Populates the calendar grid with appointment data.
        `data` is expected to be a list of dictionaries, one for each of the 3 days.
        e.g., [{'date': date_obj, 'day_name': 'Mon', 'day_number': 23, 'appointments': [...]}, ...]
        """
        if not data:
            return

        for i, day_data in enumerate(data):
            if i >= len(self.day_columns):
                print(f"Warning: Data for day {i} exceeds available columns. Skipping.")
                continue

            # Access labels using the stored references, not IDs
            day_name_label = self.day_name_labels[i]
            day_num_label = self.day_num_labels[i]
            day_grid = self.day_columns[i]['grid']

            day_name_label.text = day_data['day_name']
            day_num_label.text = str(day_data['day_number'])

            # Clear previous appointment slots but keep the time grid structure
            for hour_slot_box in day_grid.children: # Iterate through the BoxLayouts for each hour
                if isinstance(hour_slot_box, BoxLayout): # Make sure it's an hour slot container
                    # Clear only the appointment widgets within this hour slot
                    for widget in list(hour_slot_box.children):
                        if isinstance(widget, AppointmentSlot): # Only remove AppointmentSlot instances
                            hour_slot_box.remove_widget(widget)
                    # Add back a placeholder if nothing else is there
                    if not hour_slot_box.children:
                        hour_slot_box.add_widget(Label(text='', size_hint_y=1))
            
            # Now add new appointments
            for appt in day_data['appointments']:
                appt_start_dt = appt['datetime_obj']
                appt_end_dt = appt_start_dt + timedelta(minutes=appt['duration'])

                # Find the hour slot where this appointment belongs
                start_hour_index = appt_start_dt.hour - self.start_hour # Index based on 10:00 as start
                
                if 0 <= start_hour_index < len(day_grid.children):
                    target_hour_slot_box = None
                    for box in day_grid.children:
                        if hasattr(box, 'hour') and box.hour == appt_start_dt.hour:
                            target_hour_slot_box = box
                            break
                    
                    if target_hour_slot_box:
                        # Clear placeholder label
                        if target_hour_slot_box.children:
                            target_hour_slot_box.clear_widgets()

                        # Calculate height based on duration (assuming 50dp per hour)
                        # A 30-minute appointment would be 25dp
                        slot_height = (appt['duration'] / self.hour_step) * dp(50)
                        
                        display_text = appt['customer_name']
                        if appt['service_name'] and appt['service_name'] != "None": # Check if service name is present
                            display_text += f"\n({appt['service_name']})" # Add service on new line if it fits

                        appt_slot = AppointmentSlot(
                            display_text=display_text,
                            background_color_rgba=get_color_from_hex("#BBDEFB"), # Light blue for appointments
                            appointment_id=appt['id'],
                            slot_datetime=appt_start_dt,
                            size_hint_y=None,
                            height=slot_height # Set calculated height
                        )
                        target_hour_slot_box.add_widget(appt_slot)
                    else:
                        print(f"Error: Could not find slot for hour {appt_start_dt.hour} on day {day_data['date']}")
                else:
                    print(f"Appointment outside defined hours: {appt_start_dt.hour}: {appt['customer_name']}")

            # Add time indicators (current time line)
            # This is more complex and will involve drawing on canvas based on current time
            # For now, we'll skip it, but keep it in mind.

    def on_appointment_clicked(self, appointment_id):
        """Called when an existing appointment slot is clicked."""
        print(f"Appointment ID {appointment_id} clicked.")
        # Trigger popup with details and edit/delete options
        if self.app and hasattr(self.app, 'show_appointment_details_popup'):
            self.app.show_appointment_details_popup(appointment_id) # Assume app has this method
        else:
            print("Warning: app or show_appointment_details_popup not available.")


    def on_empty_slot_clicked(self, selected_datetime):
        """Called when an empty slot is clicked."""
        print(f"Empty slot at {selected_datetime.strftime('%Y-%m-%d %H:%M')} clicked.")
        # Navigate to NewAppointmentScreen and pre-fill date/time
        if self.dashboard_screen and self.dashboard_screen.manager:
            new_appt_screen = self.dashboard_screen.manager.get_screen('new_appointment_screen')
            new_appt_screen.prefill_date = selected_datetime.strftime('%Y-%m-%d')
            new_appt_screen.prefill_time = selected_datetime.strftime('%H:%M')
            self.dashboard_screen.manager.current = 'new_appointment_screen'