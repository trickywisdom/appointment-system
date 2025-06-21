# kivy/uix/custom_date_picker.py

from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.utils import get_color_from_hex
from datetime import datetime, date, timedelta

Builder.load_string("""
<DatePickerPopup>:
    size_hint: (0.9, 0.9)
    title: "Επιλογή Ημερομηνίας"
    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)

        Label:
            id: date_display
            text: root.app_instance.format_date(root.selected_date) if root.selected_date and root.app_instance else "Επιλέξτε Ημερομηνία"
            font_size: '20sp'
            size_hint_y: None
            height: dp(40)
            color: 0,0,0,1

        GridLayout:
            cols: 7
            spacing: dp(2)
            padding: dp(2)
            id: calendar_grid
            size_hint_y: 1 # Fill remaining space

            # Weekday Headers
            Label:
                text: "Κυρ"
                font_size: '12sp'
                color: 0.5, 0.5, 0.5, 1
            Label:
                text: "Δευ"
                font_size: '12sp'
                color: 0.5, 0.5, 0.5, 1
            Label:
                text: "Τρι"
                font_size: '12sp'
                color: 0.5, 0.5, 0.5, 1
            Label:
                text: "Τετ"
                font_size: '12sp'
                color: 0.5, 0.5, 0.5, 1
            Label:
                text: "Πεμ"
                font_size: '12sp'
                color: 0.5, 0.5, 0.5, 1
            Label:
                text: "Παρ"
                font_size: '12sp'
                color: 0.5, 0.5, 0.5, 1
            Label:
                text: "Σαβ"
                font_size: '12sp'
                color: 0.5, 0.5, 0.5, 1

        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(10)
            Button:
                text: "Προηγούμενος Μήνας"
                on_release: root.change_month(-1)
                background_normal: ''
                background_color: 0.1, 0.5, 0.8, 1
                color: 1,1,1,1
            Button:
                text: "Επόμενος Μήνας"
                on_release: root.change_month(1)
                background_normal: ''
                background_color: 0.1, 0.5, 0.8, 1
                color: 1,1,1,1
            Button:
                text: "Επιλογή"
                on_release: root.dismiss()
                background_normal: ''
                background_color: 0.2, 0.6, 0.2, 1
                color: 1,1,1,1
""")

class DatePickerPopup(Popup):
    selected_date = ObjectProperty(date.today())
    target_screen = ObjectProperty(None)
    app_instance = ObjectProperty(None) # Add this to pass the app instance for format_date

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(selected_date=self._update_display)
        self.generate_calendar_days()

    def on_open(self):
        from kivy.app import App
        self.app_instance = App.get_running_app() # Get the running app instance
        if self.target_screen:
            self.selected_date = self.target_screen.current_date
        self.generate_calendar_days()

    def generate_calendar_days(self):
        calendar_grid = self.ids.calendar_grid
        calendar_grid.clear_widgets()

        first_day_of_month = self.selected_date.replace(day=1)
        first_weekday_of_month = first_day_of_month.weekday()
        start_offset = (first_weekday_of_month + 1) % 7

        for _ in range(start_offset):
            calendar_grid.add_widget(Label())

        current_day = first_day_of_month
        while current_day.month == self.selected_date.month:
            btn = Button(text=str(current_day.day),
                         background_normal='',
                         color=(0,0,0,1))
            if current_day == self.selected_date:
                btn.background_color = get_color_from_hex("#ADD8E6")
            else:
                btn.background_color = get_color_from_hex("#F0F0F0")
            
            btn.bind(on_release=self.select_day)
            btn.date_value = current_day
            calendar_grid.add_widget(btn)
            current_day += timedelta(days=1)

    def select_day(self, instance):
        self.selected_date = instance.date_value
        self.generate_calendar_days()

    def change_month(self, direction):
        current_year = self.selected_date.year
        current_month = self.selected_date.month
        
        new_month = current_month + direction
        new_year = current_year

        if new_month > 12:
            new_month = 1
            new_year += 1
        elif new_month < 1:
            new_month = 12
            new_year -= 1
        
        try:
            self.selected_date = date(new_year, new_month, self.selected_date.day)
        except ValueError:
            last_day_of_new_month = (date(new_year, new_month + 1, 1) - timedelta(days=1)) if new_month < 12 else date(new_year + 1, 1, 1) - timedelta(days=1)
            self.selected_date = last_day_of_new_month
        
        self.generate_calendar_days()

    def _update_display(self, instance, value):
        if self.app_instance:
            self.ids.date_display.text = self.app_instance.format_date(value)

    def dismiss(self, *args, **kwargs):
        if self.target_screen:
            self.target_screen.update_date_from_picker(self.selected_date)
        super().dismiss(*args, **kwargs)