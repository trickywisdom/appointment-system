# pip install tkcalendar xlsxwriter smtplib pillow sv-ttk tkinter-tooltip
# import threading
import tkinter as tk
from tkinter import messagebox, ttk
# from tkinter import font as tkFont
import models_revised
from models_revised import Customer, Appointment
from tkcalendar import DateEntry
from tkcalendar import Calendar
from datetime import datetime, timedelta # ,date
from tktooltip import ToolTip
import sv_ttk
import locale
# Ορισμός ελληνικών για το strftime
locale.setlocale(locale.LC_TIME, "el_GR.UTF-8")  # Linux/macOS
locale.setlocale(locale.LC_TIME, "Greek_Greece.1253")  # Windows alternative

models_revised.setup_database()

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Κομμώσεις για όλα τα γούστα")
        self.geometry("900x600+250+150")
        sv_ttk.set_theme("light")

        # Header
        self.header = tk.Frame(self, bg="#2196F3", height=40)
        self.header.pack(side="top", fill="x")

        self.back_btn = tk.Button(
            self.header,
            text="←",
            font=("Ink Free", 12, "bold"),
            bg="#2196F3",
            fg="white",
            bd=0,
            command=lambda: self.show_frame("DashboardPage")
        )

        self.header_label = ttk.Label(
            self.header,
            text="Dashboard - Σημερινά Ραντεβού",
            font=("Segoe UI", 15),
            background="#2196F3",
            foreground="white"
        )
        self.header_label.pack(padx=20, pady=10, anchor="w", side="left")

        # Container για τις σελίδες
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}  # Θα αποθηκεύουμε τα frames εδώ
        self.current_frame = None  # Τρέχουσα σελίδα

        # Αρχικοποίηση μόνο της αρχικής σελίδας
        self.show_frame("DashboardPage")

    def show_frame(self, page_name):
        """Εμφανίζει τη σελίδα (με lazy loading)"""
        # Κρύψε το τρέχον frame
        if self.current_frame:
            self.current_frame.pack_forget()

        # Φόρτωσε τη σελίδα αν δεν υπάρχει ήδη
        if page_name not in self.frames:
            if page_name == "DashboardPage":
                self.frames[page_name] = DashboardPage(self.container, self)
            elif page_name == "NewAppointPage":
                self.frames[page_name] = NewAppointPage(self.container, self)
            elif page_name == "ClientsPage":
                self.frames[page_name] = ClientsPage(self.container, self)
            elif page_name == "NewClientPage":
                self.frames[page_name] = NewClientPage(self.container, self)
            elif page_name == "ShowClientPage":
                self.frames[page_name] = ShowClientPage(self.container, self)
            elif page_name == "RemindersPage":
                self.frames[page_name] = RemindersPage(self.container, self)

        # Εμφάνισε τη νέα σελίδα
        self.current_frame = self.frames[page_name]
        self.current_frame.pack(fill="both", expand=True)

        # Ενημέρωση τίτλου
        titles = {
            "DashboardPage": "Dashboard - Σημερινά Ραντεβού",
            "ClientsPage": "Διαχείριση Πελατών",
            "NewAppointPage": "Δημιουργία Νέου Ραντεβού",
            "NewClientPage": "Προσθήκη/Επεξεργασία Πελάτη",
            "ShowClientPage": "Ραντεβού του Πελάτη",
            "RemindersPage": "Υπενθύμιση & Εκτύπωση"
        }
        self.header_label.config(text=titles.get(page_name, ""))

        # Εμφάνιση/απόκρυψη πίσω κουμπιού
        if page_name == "DashboardPage":
            self.back_btn.pack_forget()
        else:
            self.back_btn.pack(side="right", padx=20, pady=10)

        # Κλήση μεθόδου refresh αν υπάρχει
        self.after(0, lambda: hasattr(self.current_frame, "on_show") and self.current_frame.on_show())

    def get_frame(self, page_name):
        """Ασφαλής πρόσβαση σε frame με lazy loading"""
        if page_name not in self.frames:
            if page_name == "NewAppointPage":
                self.frames[page_name] = NewAppointPage(self.container, self)
            elif page_name == "ClientsPage":
                self.frames[page_name] = ClientsPage(self.container, self)
            elif page_name == "NewClientPage":
                self.frames[page_name] = NewClientPage(self.container, self)
            elif page_name == "ShowClientPage":
                self.frames[page_name] = ShowClientPage(self.container, self)
            elif page_name == "RemindersPage":
                self.frames[page_name] = RemindersPage(self.container, self)
        return self.frames[page_name]

        
# class CalendarView(tk.Frame):
#     def __init__(self, parent, days=3):
#         super().__init__(parent, bg="#f8fafd")

#         self.days = days
#         self.hours = [f"{h:02}:00" for h in range(10, 20)]  # 10:00 - 20:00
#         self.rows = len(self.hours)
#         self.cols = self.days
        
#         self.build_grid()

#     def build_grid(self):
#         today = datetime.today()

#         # --- Top row: Dates ---
#         tk.Label(self, text="", bg="#f8fafd", font=('Segoe UI', 10)).grid(row=0, column=0)
#         for i in range(self.days):
#             day = today + timedelta(days=i)
#             lbl_month = tk.Label(self,text=day.strftime("%b"), font=('Segoe UI Variable Display', 15, "bold"), bg="#f8fafd", fg="#1F1F1F", padx=9)
#             lbl_day = tk.Label(self, text=day.strftime("%a %d"), font=('Segoe UI Semibold', 12), bg="#f8fafd", fg="#1F1F1F", pady=0)
#             lbl_month.grid(row=0, column=0, sticky="nw", columnspan=2, pady=(0,3))
#             lbl_day.grid(row=0, column=i+1, sticky="nsew")

#         # --- Rows: Hours ---
#         for i, hour in enumerate(self.hours):
#             tk.Label(self, text=hour, bg="#f8fafd", width=5, font=('Segoe UI', 10), fg="#444746").grid(row=i+1, column=0, sticky="w", padx=(7,0))
            
#             for j in range(self.days):
#                 cell = tk.Frame(self, width=200, height=49, bg="white")
#                 cell.grid(row=i+1, column=j+1, sticky="nsew")
#                 cell.grid_propagate(False)

#                 inner = tk.Frame(cell, bg="white")
#                 inner.place(relx=0, rely=0, relwidth=1, relheight=1)

#                 # Add bottom border unless it's the last row
#                 if i != self.rows - 1:
#                     tk.Frame(inner, bg="#dde3ea", height=1).pack(side="bottom", fill="x")

#                 # Add right border unless it's the last column
#                 if j != self.cols - 1:
#                     tk.Frame(inner, bg="#dde3ea", width=1).pack(side="right", fill="y")

#                 # example placeholder appointment at 12:00 today
#                 if self.hours[i] == "12:00" and j == 0:
#                     appt = tk.Label(cell, text="Μαρία Αντωνιάδου (Κ)", bg="#BBB9B4", fg="black", relief="flat", height=0, pady=0, font=('Segoe UI', 9), padx=3, anchor="w")
#                     appt.pack(fill="x", padx=(0,1), pady=(0,1), side="bottom")
#                 if self.hours[i] == "12:00" and j == 0:
#                     appt = tk.Label(cell, text="Αντουάν Μπισμπίκης (Χ)", bg="#F5F2E9", fg="black", relief="flat", height=0, pady=0, font=('Segoe UI', 9), padx=3, anchor="w")
#                     appt.pack(fill="x", padx=(0,1), pady=0, side="top")
#                 if self.hours[i] == "12:00" and j == 0:
#                     appt = tk.Label(cell, text="Γιώργος Τσανακλάκης (Λ)", bg="#e3f2fd", fg="black", relief="flat", height=0, pady=0, font=('Segoe UI', 9), padx=3, anchor="w")
#                     appt.pack(fill="x", padx=(0,1), pady=1)
#                 if self.hours[i] == "14:00" and j == 2:
#                     appt = tk.Label(cell, text="Αντουάν Μπισμπίκης (Β)", bg="#e3f2fd", fg="black", relief="flat", height=0, pady=0, font=('Segoe UI', 9), padx=3, anchor="w")
#                     appt.pack(fill="both", padx=(0,1), pady=(0,1), expand=1)
#                 if self.hours[i] == "19:00" and j == 1:
#                     appt = tk.Label(cell, text="Μαρία Αντωνιάδου (Κ)", bg="#F5F2E9", fg="black", relief="flat", height=2, pady=0, padx=3, anchor="w", font=('Segoe UI', 9))
#                     appt.pack(fill="x", padx=(0,1), pady=0, side="bottom")

#         for col in range(self.cols + 1):
#             self.grid_columnconfigure(col, weight=1)

#         for row in range(self.rows + 1):
#             self.grid_rowconfigure(row, weight=1)

class CalendarView(tk.Frame):
    def __init__(self, parent, days=3):
        super().__init__(parent, bg="#f8fafd")

        self.days = days
        self.hours = [f"{h:02}:00" for h in range(10, 20)]  # 10:00 - 20:00
        self.rows = len(self.hours) * 3  # 3 slots ανά ώρα
        self.cols = self.days
        self.slots = {}  # {(day, time): frame}

        self.bg_colors = ["#e3f2fd", "#F5F2E9", "#d2f6e6", "#fff2f7"]
        self.build_grid()
        self.load_appointments()

    def build_grid(self):
        today = datetime.today()

        tk.Label(self, text="", bg="#f8fafd", font=('Segoe UI', 10)).grid(row=0, column=0)
        self.day_refs = []
        # --- Top row: Dates ---
#         tk.Label(self, text="", bg="#f8fafd", font=('Segoe UI', 10)).grid(row=0, column=0)
#         for i in range(self.days):
#             day = today + timedelta(days=i)
#             lbl_month = tk.Label(self,text=day.strftime("%b"), font=('Segoe UI Variable Display', 15, "bold"), bg="#f8fafd", fg="#1F1F1F", padx=9)
#             lbl_day = tk.Label(self, text=day.strftime("%a %d"), font=('Segoe UI Semibold', 12), bg="#f8fafd", fg="#1F1F1F", pady=0)
#             lbl_month.grid(row=0, column=0, sticky="nw", columnspan=2, pady=(0,3))
#             lbl_day.grid(row=0, column=i+1, sticky="nsew")

#         # --- Rows: Hours ---
#         for i, hour in enumerate(self.hours):
#             tk.Label(self, text=hour, bg="#f8fafd", width=5, font=('Segoe UI', 10), fg="#444746").grid(row=i+1, column=0, sticky="w", padx=(7,0))

        for i in range(self.days):
            day = today + timedelta(days=i)
            self.day_refs.append(day)

            lbl_month = tk.Label(self, text=day.strftime("%b"), font=('Segoe UI Variable Display', 15, "bold"), bg="#f8fafd", fg="#1F1F1F", padx=9)
            lbl_day = tk.Label(self, text=day.strftime("%a %d"), font=('Segoe UI Semibold', 12), bg="#f8fafd", fg="#1F1F1F")
            # lbl_month.grid(row=0, column=i+1, sticky="nsew")
            lbl_month.grid(row=0, column=0, sticky="nw", columnspan=2, pady=(0,0))
            lbl_day.grid(row=0, column=i+1, sticky="nsew")

        for i, hour in enumerate(self.hours):
            tk.Label(self, text=hour, bg="#f8fafd", width=5, font=('Segoe UI', 10), fg="#444746").grid(
                row=i*3+2, column=0, rowspan=3, sticky="nsw", padx=(7, 0))

            for j in range(self.days):
                day = self.day_refs[j].date()

                # # Outer frame με μόνο ΠΑΝΩ και ΑΡΙΣΤΕΡΟ border
                # show_top_border = i > 0  # όχι στο πρώτο row
                # show_left_border = j > 0  # όχι στην πρώτη στήλη

                outer_frame = tk.Frame(self, bg="white")
                outer_frame.grid(row=i*3+2, column=j+1, rowspan=3, sticky="nsew")
                outer_frame.grid_propagate(False)

                # ΠΡΟΣΘΗΚΗ TOP BORDER
                # if show_top_border:
                top_border = tk.Frame(outer_frame, height=1, bg="#dde3ea")
                top_border.pack(side="top", fill="x")

                # Προσθήκη LEFT BORDER
                # if show_left_border:
                left_border = tk.Frame(outer_frame, width=1, bg="#dde3ea")
                left_border.pack(side="left", fill="y")

                # Εσωτερικό περιεχόμενο (τα slots των 20')
                inner_frame = tk.Frame(outer_frame, bg="white")
                inner_frame.pack(expand=True, fill="both")

                for k in range(3):
                    minutes = k * 20
                    time_slot = f"{int(hour[:2]) + minutes // 60:02}:{minutes % 60:02}"

                    slot = tk.Frame(inner_frame, height=17, bg="white", width=195)
                    slot.pack(fill="x", expand=True)
                    slot.pack_propagate(False)

                    self.slots[(day.isoformat(), time_slot)] = slot

                    if day.weekday() not in [6, 0]:
                        # Αλλαγή background στο hover
                        slot.bind("<Enter>", lambda e, s=slot: s.configure(bg="#f1f1f1"))
                        slot.bind("<Leave>", lambda e, s=slot: s.configure(bg="white"))

                        slot.bind("<Button-1>", lambda e, d=day, t=time_slot: self.create_new_appointment(d, t))

        # for col in range(self.cols + 1):
        #     self.grid_columnconfigure(col, weight=1)
        for col in range(self.cols + 1):
            self.grid_columnconfigure(col, weight=1)
        for row in range(self.rows + 1):
            self.grid_rowconfigure(row, weight=1)

    def create_new_appointment(self, date, time):
        print("Νέο ραντεβού για:", date, time)
        # Προσάρμοσε εδώ να ανοίγει την σελίδα NewAppointPage με τις αντίστοιχες παραμέτρους

    def load_appointments(self):
        for child in self.slots.values():
            for widget in child.winfo_children():
                widget.destroy()

        color_index = 0
        all_appointments = self.get_all()
        # print("all appointments", all_appointments)
        for app in all_appointments:
            dt = datetime.strptime(app[1], "%d-%m-%Y").date()
            t = app[2]
            slots_needed = int(app[4]) // 20
            if (dt.isoformat(), t) in self.slots:
                frame = self.slots[(dt.isoformat(), t)]
                try:
                    # customer = Customer.get_by_id(app[0])
                    # print("app", app[0])
                    name = Customer.get_name_by_id(app[0])
                except:
                    name = "Ο Κανένας"

                label = tk.Label(frame, text=f"{name}({app[3]})", bg=self.bg_colors[color_index % len(self.bg_colors)], fg="#1F1F1F", font=("Segoe UI", 9), anchor="w", width=15)
                label.pack(fill="both", expand=False)
                if slots_needed == 2:
                    frame = self.slots[dt.isoformat(), self.add_minutes(t, 20)]
                    frame.configure(height=17)
                    label2 = tk.Label(frame, text="", bg=self.bg_colors[color_index % len(self.bg_colors)], anchor="w", width=15, pady=5)
                    label2.pack(fill="both", expand=False)
                    label2.bind("<Button-1>", lambda e, a=app, n=name: self.show_appointment_popup(a, n))
                if slots_needed == 3:
                    frame = self.slots[dt.isoformat(), self.add_minutes(t, 20)]
                    frame.configure(height=17)
                    label2 = tk.Label(frame, text="", bg=self.bg_colors[color_index % len(self.bg_colors)], anchor="w", width=15, pady=5)
                    label2.pack(fill="both", expand=False)
                    label2.bind("<Button-1>", lambda e, a=app, n=name: self.show_appointment_popup(a, n))
                    frame = self.slots[dt.isoformat(), self.add_minutes(t, 40)]
                    frame.configure(height=17)
                    label3 = tk.Label(frame, text="", bg=self.bg_colors[color_index % len(self.bg_colors)], anchor="w", width=15, pady=1)
                    label3.pack(fill="both", expand=False)
                    label3.bind("<Button-1>", lambda e, a=app, n=name: self.show_appointment_popup(a, n))
                label.bind("<Button-1>", lambda e, a=app, n=name: self.show_appointment_popup(a, n))

            color_index += 1

        # for app_index, app in enumerate(all_appointments):
        #     day_str = app[1]
        #     start_time = app[2]
        #     duration = int(app[4])
        #     name = app[0]
        #     service = app[3]
        #     bg = self.bg_colors[app_index % len(self.bg_colors)]

        #     slots_needed = duration // 20
        #     hour, minute = map(int, start_time.split(":"))
        #     start_minutes = hour * 60 + minute

        #     for i in range(slots_needed):
        #         slot_time = start_minutes + i * 20
        #         slot_hour = slot_time // 60
        #         slot_minute = slot_time % 60
        #         time_str = f"{slot_hour:02}:{slot_minute:02}"
        #         key = (day_str, time_str)

        #         if key in self.slots:
        #             frame = self.slots[key]

        #             # Καθαρίζουμε το slot
        #             for widget in frame.winfo_children():
        #                 widget.destroy()

        #             # Προσθέτουμε το ίδιο "ραντεβού label" σε κάθε slot
        #             label = tk.Label(
        #                 frame,
        #                 text=f"{name} ({service})" if i == 0 else "",  # μόνο στο πρώτο slot το κείμενο
        #                 bg=bg,
        #                 fg="#1F1F1F",
        #                 font=("Segoe UI", 9),
        #                 anchor="w",
        #                 width=15
        #             )
        #             label.pack(fill="both", expand=True)

        #             # Όλα τα slots οδηγούν στο ίδιο popup
        #             frame.bind("<Button-1>", lambda e, app=app: self.show_popup(app))
        #             label.bind("<Button-1>", lambda e, app=app: self.show_popup(app))

    def add_minutes(self, time_str, mins_to_add):
        hour, minute = map(int, time_str.split(":"))
        total_minutes = hour * 60 + minute + mins_to_add
        new_hour = total_minutes // 60
        new_minute = total_minutes % 60
        return f"{new_hour:02d}:{new_minute:02d}"

    def get_all(self):
        try:
            appointments = [(a.customer_id, a.date, a.time, a.services, a.duration, a.notes, a.id) for a in Appointment.get_all()]
            # print("appointments", appointments)
            return appointments
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch appointments: {e}")
            return []

    def show_appointment_popup(self, appointment, customer_name):
        popup = tk.Toplevel(self)
        popup.title("Λεπτομέρειες Ραντεβού")
        popup.geometry("300x250")
        popup.configure(bg="white")

        info = f"""
                Ημερομηνία: {appointment[1]}
                Ώρα: {appointment[2]}
                Πελάτης: {customer_name}
                Υπηρεσία: {appointment[3]}
                Διάρκεια: {appointment[4]} λεπτά
                Σημείωση: {appointment[5] or '-'}
                """
        tk.Label(popup, text=info.strip(), justify="left", bg="white", font=("Segoe UI", 10)).pack(padx=10, pady=10)

        btn_frame = tk.Frame(popup, bg="white")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Επεξεργασία", command=lambda: print("Edit"), bg="#f0f0f0").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Διαγραφή", command=lambda: self.delete_appointment(popup, appointment[6])).pack(side="right", padx=5)

    def delete_appointment(self, popup, appointment_id):
        if messagebox.askyesno("Επιβεβαίωση", "Θέλεις σίγουρα να διαγράψεις αυτό το ραντεβού;"):
            Appointment.delete_from_db(appointment_id)
            popup.destroy()
            self.load_appointments()
        
class DashboardPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        
        # Left Side Menu
        self.left_menu = tk.Frame(self, bg="#F4F4F4", width=200)
        self.left_menu.pack(side="left", fill="y")

        # Calendar Mini with custom styling
        self.minical = Calendar(self.left_menu,
                             showweeknumbers=False, 
                             showothermonthdays=False, 
                             firstweekday='monday', 
                             selectmode='day', 
                             cursor="hand1", 
                             font=('Segoe UI Variable Text Semiligh', 10), 
                             locale="el_GR", 
                             selectbackground="#505E66",
                             borderwidth=0,
                             background="#505E66",
                             foreground="white",
                             headersbackground="#f1ede0",
                             headersforeground="#3F3F3F",
                             padding=0,
                             bordercolor="#F5F5F5",
                            weekendbackground="#F5F5F5",
                            normalbackground="#F5F5F5",
                            highlightthickness=1
                             )
        self.minical.pack(pady=(20,0), padx=(10,13), fill="both", expand=1, side="top", anchor="n")

        ttk.Separator(self.left_menu).pack(fill="both", ipady=1, padx=5)
        # === Search Entry ===
        search_client = tk.Entry(self.left_menu,
                                  font=('Segoe UI', 10),
                                    relief="flat",
                                      bg="white", fg="#444756",
                                        border=1, borderwidth=8,
                                            highlightbackground="#e9e9e9", highlightthickness=1, highlightcolor="#C3C6CA", insertbackground="#686868",
                                              width=15)
        search_client.insert(0, "🔍Επώνυμο ή Τηλ")
        search_client.bind("<FocusIn>", lambda args: search_client.delete('0', 'end'))
        search_client.bind("<FocusOut>", lambda args: search_client.insert(0, "🔍Επώνυμο ή Τηλ"))
        search_client.pack(anchor="nw", pady=(15,45), ipady=0, padx=10, expand=1)
        
        # New Appointment Button
        self.new_appt_btn = tk.Button(
            self.left_menu,
            text="Νέο Ραντεβού",
            bg="#4CAF50",
            fg="white",
            relief=tk.FLAT,
            padx=22,
            pady=3,
            cursor="hand2",
            width=9,
            font=('"Segoe UI Semibold" 10'),
                                 command=lambda: (
                                                    controller.show_frame("NewAppointPage")
                                                    # controller.get_frame("NewAppointPage").reset_fields()
                                                ))
        
        # Clients Button
        self.clients_btn = tk.Button(
            self.left_menu,
            text="Πελάτες",
            bg="#fd9827",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=22,
            pady=3,
            width=9,
            font=('"Segoe UI Semibold" 10'),
            command=lambda: controller.show_frame("ClientsPage")
        )
        
        # Reminders Button
        self.remind_btn = tk.Button(
            self.left_menu,
            text="Υπενθυμίσεις",
            bg="#e72565",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=22,
            pady=3,
            width=9,
            font=('"Segoe UI Semibold" 10'),
            command=lambda: (
                                                    controller.show_frame("RemindersPage")
                                                ))
        
        self.remind_btn.pack(pady=(8,25), padx=10, side="bottom", anchor="w")
        self.clients_btn.pack(pady=0, padx=10, side="bottom", anchor="w")
        self.new_appt_btn.pack(pady=8, padx=10, side="bottom", anchor="w")

        ToolTip(self.remind_btn, msg="- Αποστολή email σε όλους τους πελάτες που\nέχουν ραντεβού μια συγκεριμένη μέρα\n\n- Εκτύπωση των ραντεβού της ημέρας σε Excel", delay=1.0,
        parent_kwargs={"bg": "#202018", "padx": 2, "pady": 2},
        fg="#ffffff", bg="#636332", padx=7, pady=7)

       
        # Περιεχόμενο
        content = tk.Frame(self, bg="#f8fafd")
        content.pack(side="left", fill="both", expand=True, padx=0, pady=0)

        calendar = CalendarView(content, days=3)
        calendar.pack(side="left", fill="both", expand=True, padx=7, pady=(0,3))

class ClientsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        sv_ttk.set_theme("light")

        # === Content wrapper ===
        content = tk.Frame(self, padx=40, pady=20)
        content.pack(expand=1, fill="both")
        # === List Container Frame ===
        list_container = ttk.Frame(content, border=1, borderwidth=1, relief="sunken")
        # === Canvas and Scrollbar ===
        canvas_frame = tk.Frame(list_container, highlightbackground="gray", highlightthickness=1, background="#fdfdfd")
        canvas = tk.Canvas(canvas_frame)
        # === Scrollable Frame ===
        self.scrollable_frame = ttk.Frame(canvas)

        # Πεδίο αναζήτησης
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.search_customer)
        self.search_client = ttk.Entry(content, textvariable=self.search_var)
        self.search_client.insert(0, "   Αναζήτηση με όνομα ή τηλέφωνο...")
        self.search_client.bind("<FocusIn>", lambda args: self.search_client.delete('0', 'end'))

        self.search_client.pack(anchor="w", fill="x", pady=0, ipady=10)

        new_cli_btn = ttk.Button(content, text="+ Νέος πελάτης", style='Accent.TButton',
                                 command=lambda: (
                                                    controller.show_frame("NewClientPage")
                                                ))
        new_cli_btn.pack(anchor="w", pady=(20,0))

        list_container.pack(fill="both", expand=True, padx=(0), pady=(20), anchor="center")

        # === Header Row ===
        headers = ["Επώνυμο", "Όνομα", "Τηλέφωνο", "Email", "Ενέργειες"]
        header_row = tk.Frame(list_container, bg="#C2DFF7")
        for h in headers:
            label = tk.Label(header_row, text=h, font=("Segoe UI", 10, "bold"), fg="#242525", bg="#C2DFF7", width=18, anchor="w")
            label.pack(side="left",pady=(2,1), anchor="w", padx=(18,0))
        header_row.pack(fill="x", ipady=(2))


        # # === Canvas and Scrollbar ===
        canvas_frame.pack(fill="both", expand=True, pady=(0, 1))

        # canvas = tk.Canvas(canvas_frame)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y", pady=(4,1))
        canvas.configure(yscrollcommand=scrollbar.set)

        # # === Scrollable Frame ===
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # === Mousewheel scrolling ===
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.scrollable_frame.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.scrollable_frame.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # self.load_clients()

    def search_customer(self, *args):
        customer_list = self.show_all_customers()
        query = self.search_var.get().strip().lower()

        # Καθαρισμός παλιών widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Φιλτράρισμα
        filtered_customers = [
            customer for customer in customer_list
            if query in customer[1].lower() or query in customer[2]
        ]

        # Ταξινόμηση
        filtered_customers.sort(key=lambda x: (x[1] == "", x[1]))

        # === Εμφάνιση ===
        total_rows = max(len(filtered_customers), 10)

        for index in range(total_rows):
            if index < len(filtered_customers):
                customer = filtered_customers[index]
            else:
                customer = ("", "", "", "", "")  # Κενή γραμμή

            bg = "#e3f2fd" if index % 2 == 0 else "#F5F2E9"
            row = tk.Frame(self.scrollable_frame, background=bg, padx=4, pady=1)
            
            for i in (1,0,2,3):
                tk.Label(row, text=customer[i], font=("Segoe UI", 10), width=21, anchor="w", background=bg).pack(anchor="w", pady=2, padx=(14,2), side="left")
            
            if customer[1]:  # Αν έχει όνομα, δείξε κουμπιά
                tk.Button(row, text=" 🗑️", font=(18), fg="#242525", background=bg, command=lambda c=customer: self.delete_and_reload(c), width=3, relief="flat").pack(side="right", padx=2, anchor="center")
                tk.Button(row, text=" 🖋️", font=(18), fg="#242525", background=bg,  command=lambda c=customer:self.controller.get_frame("NewClientPage").edit_customer(c[0],c[1],c[2],c[3], c[4]), width=3, relief="flat").pack(side="right", padx=2)
                tk.Button(row, text="🔍", font=(18), fg="#242525", background=bg,  command=lambda c=customer:self.controller.get_frame("ShowClientPage").customer_info(c[0],c[1],c[2],c[3], c[4]), width=3, relief="flat").pack(side="right", padx=2)
            else:
                tk.Label(row, text=" ", background=bg, width=9).pack(side="right", padx=20, pady=(5,6), fill="x")

            row.pack(fill="x", pady=1)

    def load_clients(self):
        customer_list = self.show_all_customers()

        # Καθαρισμός παλιών widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        
        # Ταξινόμηση
        customer_list.sort(key=lambda x: (x[1] == "", x[1]))

        # === Εμφάνιση ===
        total_rows = max(len(customer_list), 10)

        for index in range(total_rows):
            if index < len(customer_list):
                customer = customer_list[index]
            else:
                customer = ("", "", "", "", "")  # Κενή γραμμή

            bg = "#e3f2fd" if index % 2 == 0 else "#F5F2E9"
            row = tk.Frame(self.scrollable_frame, background=bg, padx=4, pady=1)
            
            for i in (1,0,2,3):
                tk.Label(row, text=customer[i], font=("Segoe UI", 10), width=21, anchor="w", background=bg).pack(anchor="w", pady=2, padx=(14,2), side="left")
            
            if customer[1]:  # Αν έχει όνομα, δείξε κουμπιά
                tk.Button(row, text=" 🗑️", font=(18), fg="#242525", background=bg, command=lambda c=customer: self.delete_and_reload(c), width=3, relief="flat").pack(side="right", padx=2, anchor="center")
                tk.Button(row, text=" 🖋️", font=(18), fg="#242525", background=bg,  command=lambda c=customer:self.controller.get_frame("NewClientPage").edit_customer(c[0],c[1],c[2],c[3], c[4]), width=3, relief="flat").pack(side="right", padx=2)
                tk.Button(row, text="🔍", font=(18), fg="#242525", background=bg,  command=lambda c=customer:self.controller.get_frame("ShowClientPage").customer_info(c[0],c[1],c[2],c[3], c[4]), width=3, relief="flat").pack(side="right", padx=2)
            else:
                tk.Label(row, text=" ", background=bg, width=9).pack(side="right", padx=20, pady=(5,6), fill="x")

            row.pack(fill="x", pady=1)

    def delete_and_reload(self, client):
        if messagebox.askyesno("Επιβεβαίωση", f"Να διαγραφεί ο/η {client[0]} {client[1]};"):
            Customer.delete_from_db(client[2])
            self.load_clients()

    def show_all_customers(self):
        """
        All customers with details (name, surname, phone, email, id).
        """
        try:
            # all_customers = Customer.get_all()
            customers_list = [(c.first_name, c.last_name, c.phone, c.email, c.id) for c in Customer.get_all()]
            return customers_list
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch customers: {e}")
            return []
        
    def on_show(self):
    #     sv_ttk.set_theme("light")
        self.focus_set()  # Αφαιρεί το focus από το entry
        self.search_var.set("   Αναζήτηση με όνομα ή τηλέφωνο...")
        self.load_clients()
        # pass

class NewAppointPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        # sv_ttk.set_theme("light")

        self.content = ttk.Frame(self, padding=(260,25), border=5, borderwidth=3)
        self.content.pack(expand=1, ipady=10, fill="both")

        ttk.Label(self.content, text="Πελάτης:", anchor="w", width=20).grid(row=0, column=0, sticky="w", pady=10)

        # all_clients = self.show_all_customers()
  
        # self.client_map = {f"{c[0]} {c[1]}": c[4] for c in all_clients}
        # client_names = list(self.client_map.keys())

        
        # client_var = tk.StringVar(content)
        
        # self.selected_name = ttk.Combobox(content, textvariable=client_var, values=client_names, state="readonly", width=16)
        # self.selected_name.grid(row=0, column=1, sticky="w", pady=10)

        self.l1 = tk.Listbox(self.content, relief="flat", width=35, bg="#f0f0f0", borderwidth=1, highlightthickness=1, font=("Segoe UI", 10))
        # Πεδίο αναζήτησης
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.search_customer)
        self.search_client = ttk.Entry(self.content, textvariable=self.search_var)
        self.search_client.insert(0, "Επώνυμο 🔍 Τηλέφωνο")
        self.search_client.bind("<FocusIn>", lambda args: self.search_client.delete('0', 'end'))

        self.search_client.grid(row=0, column=1, sticky="w", pady=10)

        # Πρέπει να γίνει update για να ξέρουμε τις συντεταγμένες του entry
        self.search_client.update_idletasks()

        # self.l1 = tk.Listbox(self.content, relief="flat", width=35, bg="#f0f0f0", borderwidth=1, highlightthickness=1)
        # if self.query:
        #     print(self.query)
        #     self.l1.place(x=self.search_client.winfo_x() + 80, 
        #                 y=self.search_client.winfo_y() + self.search_client.winfo_height() - 100,
        #                 width=170, height=220)
        #     self.l1.lift()
        # else:
        #     self.l1.place_forget()

        ttk.Label(self.content, text="Ημερομηνία:", anchor="w", width=20).grid(row=1, column=0,sticky="w", pady=10)
        self.appoint_date = DateEntry(self.content, date_pattern='dd-mm-yyyy', width=16)
        self.appoint_date.grid(row=1, column=1, sticky="w", pady=10)
        
        ttk.Label(self.content, text="Ώρα:", anchor="w", width=20).grid(row=2, column=0, sticky="w", pady=10)
        # Ώρες που δεν είναι διαθέσιμες
        unavailable = set()
        if self.appoint_date:
            date_str = self.appoint_date.get()
            appointments_of_day = [(a.customer_id, a.date, a.time, a.services, a.duration, a.notes, a.id) for a in Appointment.get_by_date(date_str)]
            for app in appointments_of_day:
                hour, minute = map(int, app[2].split(":"))
                unavailable.add((hour, minute))
                if int(app[4]) == 40:
                    total_minutes = hour * 60 + (minute + 20)
                    h, m = divmod(total_minutes, 60)
                    # print("divmod1", h, m)
                    unavailable.add((h, m))
                if int(app[4]) == 60:
                    total_minutes = hour * 60 + (minute + 20)
                    h, m = divmod(total_minutes, 60)
                    # print("divmod1,5", h, m)
                    unavailable.add((h, m))
                    total_minutes = hour * 60 + (minute + 40)
                    h, m = divmod(total_minutes, 60)
                    # print("divmod2", h, m)
                    unavailable.add((h, m))

                # new_start = datetime.strptime(f"{self.time}", "%H:%M")
                # new_end = new_start + timedelta(minutes=app[5])
                # dt = datetime.strptime(app[1], "%d-%m-%Y").date()
                # print("dt", dt)
                t = app[2]
                # print("t", t)
                slots_needed = int(app[4]) // 20
                # print("slots_needed", slots_needed)
        # unavailable = {(10, 0), (11, 40), (15, 20)}  # Δηλαδή 10:00, 11:40, 15:20

        # Δημιουργούμε τις επιλογές
        time_options = [
            f"{h:02d}:{m:02d} ❌" if (h, m) in unavailable else f"{h:02d}:{m:02d}"
            for h in range(10, 20)
            for m in range(0, 60, 20)
        ]
        # time_options = [f"{h:02d}:{m:02d}" for h in range(10, 20) for m in range(0, 60, 20)]
        # if self.appoint_date:
        #     appointments_of_day = [(a.customer_id, a.date, a.time, a.services, a.duration, a.notes, a.id) for a in Appointment.get_by_date(self.appoint_date)]
        #     times_excluded = 
        time_var = tk.StringVar(self.content)
        self.time_dropdown = ttk.Combobox(self.content, textvariable=time_var, values=time_options, state="readonly", width=16)
        self.time_dropdown.grid(row=2, column=1, sticky="w", pady=10)
        
        ttk.Label(self.content, text="Διάρκεια:", anchor="w", width=20).grid(row=3, column=0, sticky="w", pady=10)
        duration_var = tk.StringVar(self.content, value="20")
        self.duration_dropdown = ttk.Combobox(self.content, textvariable=duration_var, values=["20","40","60"], state="readonly", width=16)
        self.duration_dropdown.grid(row=3, column=1, sticky="w", pady=10)
        
        ttk.Label(self.content, text="Είδος υπηρεσίας:", anchor="w", width=20).grid(row=4, column=0, sticky="w", pady=10) # multiple options? Checkbox?
        service_var = tk.StringVar(self.content, value="Κούρεμα")
        self.service_dropdown = ttk.Combobox(self.content, textvariable=service_var, values=["Κούρεμα","Βάψιμο","Χτένισμα"], state="readonly", width=16)
        self.service_dropdown.grid(row=4, column=1, sticky="w", pady=10)
        
        ttk.Label(self.content, text="Σημειώσεις:", anchor="w", width=20,).grid(row=5, column=0, sticky="w", pady=(10,10))
        self.notes = tk.Entry(self.content, bg="#fdfdfd", highlightbackground="white")
        self.notes.grid(row=6, column=0, columnspan=2, padx=0, ipady=35, ipadx=108, sticky="nw")

        # self.l1 = tk.Listbox(self.content, relief="flat", width=35, bg="#f0f0f0", borderwidth=1, highlightthickness=1, font=("Segoe UI", 10))
        
        # print(self.query)
        # self.l1.place(x=self.search_client.winfo_x() - 80, 
        #                 y=self.search_client.winfo_y() + self.search_client.winfo_height() - 60,
        #                 width=180, height=220)
        # self.l1.lift()
        
        # self.l1.place_forget()
        # Όταν χάνει το focus, κρύψε το Listbox
        self.search_client.bind("<FocusOut>", lambda e: self.hide_listbox_if_needed())
        self.l1.bind("<FocusOut>", lambda e: self.hide_listbox_if_needed())
        

        save_btn = ttk.Button(self.content, text="Αποθήκευση", width=12, underline=1, style='Accent.TButton', command=self.save_appoint).grid(row=7, column=1, pady=(40,15), sticky="w", padx=0)
        cancel_btn = ttk.Button(self.content, text="Ακύρωση", width=12, underline=1, command=lambda: self.controller.show_frame("DashboardPage")).grid(row=7, column=0, pady=(40,15), sticky="e", padx=15)

    def hide_listbox_if_needed(self):
        # Αν δεν έχει focus ούτε το Entry ούτε το Listbox, απόκρυψε
        if not self.search_client.focus_get() in [self.search_client, self.l1]:
            self.l1.place_forget()   

    def search_customer(self, *args):
        customer_list = self.show_all_customers()
        self.query = self.search_var.get().strip().lower()

        # Καθαρισμός παλιών widgets
        # for widget in self.scrollable_frame.winfo_children():
        #     widget.destroy()

        # Φιλτράρισμα
        filtered_customers = [
            customer for customer in customer_list
            if self.query in customer[1].lower() or self.query in customer[2]
        ]

        def my_upd(my_widget):
            my_w = my_widget.widget
            # print("my_w", my_w.get(0, "end"))
            index = int(my_w.curselection()[0])
            customer = filtered_customers[index]
            # print("index", index)
            # print("customer", customer)
            self.selected_id = customer[3] # είναι το customer_id που αντιστοιχεί στο συγκεκριμένο index της listbox
            # print("self.selected_id", self.selected_id)
            value = my_w.get(index).strip()
            self.selected_name = value
            # print("value", value)
            self.search_var.set(value)
            self.l1.place_forget()
            self.focus_set()
        # Ταξινόμηση
        # filtered_customers.sort(key=lambda x: (x[1] == "", x[1]))

        self.l1.delete(0, 'end')
        for customer in filtered_customers:
            full_name = f"{customer[0]} {customer[1]}"
            self.l1.insert(tk.END,f" {full_name}")
        self.l1.bind("<<ListboxSelect>>", my_upd)

        #Configure the listitems
        for row_index in range(len(filtered_customers)):
            bg = "#e3f2fd" if row_index % 2 == 0 else "#F5F2E9"
            self.l1.itemconfig(row_index,{'bg': bg})
            self.l1.itemconfig(row_index,{'bg': bg})

        
        # # Παίρνουμε συντεταγμένες του Entry
        # self.search_client.update_idletasks()
        # x = self.search_client.winfo_rootx()
        # y = self.search_client.winfo_rooty() + self.search_client.winfo_height()

        # if query:
        #     # Δημιουργία popup Listbox
        #     self.listbox_popup = tk.Toplevel(self.content)
        #     self.listbox_popup.wm_overrideredirect(True)  # Χωρίς τίτλο/πλαίσιο
        #     self.listbox_popup.attributes("-topmost", True)
        #     self.listbox_popup.attributes("-alpha", 0.95)  # 95% opacity

        #     # Τοποθέτηση πάνω από όλα
        #     self.listbox_popup.geometry(f"250x120+{x-10}+{y-5}")

        #     # Προσθήκη Listbox
        #     self.l1 = tk.Listbox(self.listbox_popup, width=35, bg="#f0f0f0")
        #     self.l1.pack(fill="both", expand=True)

        #     # Γέμισμα λίστας
        #     for customer in filtered_customers:
        #         name = f"{customer[0]} {customer[1]}"
        #         self.l1.insert(tk.END, name)
        # else:
        #     self.l1.pack_forget()
        # self.content.bind("<Button-1>", lambda e: self.listbox_popup.destroy())
        # === Εμφάνιση ===
        # total_rows = max(len(filtered_customers), 10)

        # for index in range(total_rows):
        #     if index < len(filtered_customers):
        #         customer = filtered_customers[index]
        #     else:
        #         customer = ("", "", "", "", "")  # Κενή γραμμή

        #     bg = "#e3f2fd" if index % 2 == 0 else "#F5F2E9"
        #     row = tk.Frame(self.scrollable_frame, background=bg, padx=4, pady=1)
            
        #     for i in (1,0,2,3):
        #         tk.Label(row, text=customer[i], font=("Segoe UI", 10), width=21, anchor="w", background=bg).pack(anchor="w", pady=2, padx=(14,2), side="left")
            
        #     if customer[1]:  # Αν έχει όνομα, δείξε κουμπιά
        #         tk.Button(row, text=" 🗑️", font=(18), fg="#242525", background=bg, command=lambda c=customer: self.delete_and_reload(c), width=3, relief="flat").pack(side="right", padx=2, anchor="center")
        #         tk.Button(row, text=" 🖋️", font=(18), fg="#242525", background=bg,  command=lambda c=customer:self.controller.get_frame("NewClientPage").edit_customer(c[0],c[1],c[2],c[3], c[4]), width=3, relief="flat").pack(side="right", padx=2)
        #         tk.Button(row, text="🔍", font=(18), fg="#242525", background=bg,  command=lambda c=customer:self.controller.get_frame("ShowClientPage").customer_info(c[0],c[1],c[2],c[3], c[4]), width=3, relief="flat").pack(side="right", padx=2)
        #     else:
        #         tk.Label(row, text=" ", background=bg, width=9).pack(side="right", padx=20, pady=(5,6), fill="x")

        #     row.pack(fill="x", pady=1)
        self.l1.place(x=self.search_client.winfo_x() - 80, 
                        y=self.search_client.winfo_y() + self.search_client.winfo_height() - 60,
                        width=215, height=220)

    # def reset_fields(self):
    #     """Καθαρίζει τα πεδία για νέο ραντεβού."""
    #     from datetime import date
    #     # self.selected_name.delete(0, "end")
    #     self.appoint_date.delete(0, tk.END)
    #     self.time_dropdown.delete(0, tk.END)
    #     self.service_dropdown.delete(0, tk.END)
    #     self.duration_dropdown.delete(0, tk.END)
    #     self.notes.delete(0, tk.END)
    #     self.appoint_date.set_date(date.today())

    def save_appoint(self):
        # print(self.selected_name.get())
        """
        Create, Save or Update a (new) appointment to the database.
        """
        # selected_name = self.selected_name.get()  # ΠΑΡΕ το string όνομα από το Combobox
        # selected_id = self.client_map.get(selected_name)
        selected_name = self.selected_name
        selected_id = self.selected_id
        appoint_date = self.appoint_date.get()
        time_dropdown = self.time_dropdown.get()
        service_dropdown = self.service_dropdown.get()
        duration_dropdown = self.duration_dropdown.get()
        notes = self.notes.get()
        # print("0", selected_name, selected_id, appoint_date, time_dropdown, service_dropdown, duration_dropdown, notes)
        # print(selected_id, appoint_date, time_dropdown, service_dropdown, duration_dropdown, notes)

        # Validate input fields

        if not selected_name or not appoint_date or not time_dropdown or not time_dropdown or not service_dropdown or not duration_dropdown.strip():
            messagebox.showerror("Σφάλμα", "Όλα τα πεδία (Πελάτης, Ημερομηνία, Ώρα, Διάρκεια και Είδος Υπηρεσίας) πρέπει να συμπληρωθούν")
            return

        try:
            # print("1", selected_name, selected_id, appoint_date, time_dropdown, service_dropdown, duration_dropdown, notes)
            # Create and save the appointment
            appointment = Appointment(selected_id, appoint_date, time_dropdown, service_dropdown, duration_dropdown, notes)
            # print("2", selected_id, appoint_date, time_dropdown, service_dropdown, duration_dropdown, notes)
            appointment.save_to_db() # IF ALREADY EXISTS WE SHOULD UPDATE
            # print("3", selected_id, appoint_date, time_dropdown, service_dropdown, duration_dropdown, notes)
            messagebox.showinfo("Επιτυχία", f"Αποθηκεύτηκε το ραντεβού για {selected_name}")

            # # Clear input fields
            # self.reset_fields()

            # Πηγαίνουμε στην DashboardPage
            self.controller.show_frame("DashboardPage")
        except Exception as e:
            messagebox.showerror("Παρουσιάστηκε σφάλμα", f"Αποτυχία στην αποθήκευση του ραντεβού: {e}")


    def show_all_customers(self):
        """
        All customers with details (name, surname, phone, email, id).
        """
        try:
            # all_customers = Customer.get_all()
            customers_list = [(c.first_name, c.last_name, c.phone, c.id) for c in Customer.get_all()]
            return customers_list
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch customers: {e}")
            return []
        

    def on_show(self):
        """Καθαρίζει τα πεδία όταν ανοίγει η σελίδα."""
        from datetime import date
        self.search_var.set("Επώνυμο 🔍 Τηλέφωνο")
        self.appoint_date.set_date(date.today())  # Επαναφέρει τη σημερινή ημερομηνία
        self.time_dropdown.set("")  # Καθαρίζει την ώρα
        self.service_dropdown.set("")  # Καθαρίζει την υπηρεσία
        self.duration_dropdown.set("")  # Καθαρίζει τη διάρκεια
        self.notes.delete(0, tk.END)  # Καθαρίζει το πεδίο σημειώσεων

        self.focus_set()  # Αφαιρεί focus από όποιο widget είχε focus
        
        # self.load_clients()
        self.l1.place_forget()  
        
    

class NewClientPage(tk.Frame):

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        sv_ttk.set_theme("light")
        self.editing = False # Flag για όταν κάνουμε new client και θέλουμε reset_fields, και edit client που εννοείται δεν θέλουμε reset_fields

        content = ttk.Frame(self, padding=(35,10))
        content.pack(expand=1, ipady=10)

        ttk.Label(content, text="Όνομα:").grid(row=0, column=0, sticky="w", pady=(25,10))
        self.entry_name = ttk.Entry(content)
        self.entry_name.grid(row=0, column=1, sticky="w", pady=(25,10))

        ttk.Label(content, text="Επώνυμο:").grid(row=1, column=0, sticky="w", pady=10)
        self.entry_surname = ttk.Entry(content)
        self.entry_surname.grid(row=1, column=1, sticky="w", pady=10)

        ttk.Label(content, text="Τηλέφωνο:").grid(row=2, column=0, sticky="w", pady=10)
        self.entry_phone = ttk.Entry(content)
        self.entry_phone.grid(row=2, column=1, sticky="w", pady=10)

        ttk.Label(content, text="Email:").grid(row=3, column=0, sticky="w", pady=10)
        self.entry_email = ttk.Entry(content)
        self.entry_email.grid(row=3, column=1, sticky="w", pady=10)

        self.id = None

        cancel_btn = ttk.Button(content, text="Ακύρωση", width=12, command=lambda: controller.show_frame("ClientsPage")).grid(row=6, column=0, pady=(50,0), sticky="e", padx=15)
        save_btn = ttk.Button(content, text="Αποθήκευση", width=12, style='Accent.TButton', command=self.save_customer).grid(row=6, column=1, pady=(50,0), sticky="w", padx=15)

    def reset_fields(self):
        """Καθαρίζει τα πεδία για νέο πελάτη."""
        self.entry_name.delete(0, tk.END)
        self.entry_surname.delete(0, tk.END)
        self.entry_phone.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)

    def save_customer(self):
            """
            Save a new customer to the database.
            """
            first_name = self.entry_name.get()
            last_name = self.entry_surname.get()
            phone = self.entry_phone.get()
            email = self.entry_email.get()
            id = self.id

            # Validate input fields
            if not first_name.strip() or not last_name.strip() or not phone.strip() or not email.strip():
                messagebox.showerror("Σφάλμα", "Όλα τα πεδία (Όνομα, Επώνυμο, Τηλέφωνο, Email) πρέπει να συμπληρωθούν")
                return

            try:
                # Create and save the customer
                customer = Customer(first_name, last_name, phone, email, id)
                customer.save_to_db(id) # IF ALREADY EXISTS WE SHOULD UPDATE
                messagebox.showinfo("Επιτυχία", f"Αποθηκεύτηκε: {customer.first_name} {customer.last_name}")

                # Clear input fields
                self.reset_fields()

                # Καλεί την load_clients για να καθαρίσει το all clients table και να το ξαναγεμίσει περιέχοντας τον καινούργιο customer
                self.controller.get_frame("ClientsPage").load_clients()
                # Πηγαίνουμε στην ClientsPage
                self.controller.show_frame("ClientsPage")
            except Exception as e:
                messagebox.showerror("Παρουσιάστηκε σφάλμα", f"Αποτυχία στην αποθήκευση του πελάτη: {e}")

    

    def edit_customer(self, first_name, last_name, phone, email, id):
            # print(first_name, last_name, phone, email, id)
            # print("edit_customer")
            """
            Επεξεργασία πελάτη και update database
            """
            self.editing = True

            self.controller.show_frame("NewClientPage")
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, first_name)

            self.entry_surname.delete(0, tk.END)
            self.entry_surname.insert(0, last_name)

            self.entry_phone.delete(0, tk.END)
            self.entry_phone.insert(0, phone)

            self.entry_email.delete(0, tk.END)
            self.entry_email.insert(0, email)

            self.id = id

    def on_show(self):
        # print("on show")
        if not self.editing:
            self.reset_fields()
        self.editing = False

class ShowClientPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        content = ttk.Frame(self)
        content.pack(fill="both", expand=True, padx=(150,150), pady=10, anchor="center")
        
        self.client_name = ttk.Label(content, text="", font=('Segoe UI Variable Display Semib', 20), foreground="#1F1F1F")
        self.client_name.pack(pady=(0,0), padx=2, anchor="nw")
        
        self.contact_phone = ttk.Label(content, text="", font=('Segoe UI Variable Display', 10), foreground="#1F1F1F")
        self.contact_phone.pack(pady=3, padx=3, anchor="nw")

        self.contact_email = ttk.Label(content, text="", font=('Segoe UI Variable Display', 10), foreground="#1F1F1F")
        self.contact_email.pack(padx=4, pady=(0,22), anchor="nw")

        list_container = ttk.Frame(content, border=1, borderwidth=1, relief="sunken")
        list_container.pack(fill="both", expand=True, padx=0, pady=(0, 5), anchor="center")

        # === Header Row ===
        headers = ["Ημερομηνία", "Ώρα", "Υπηρεσία"]
        header_row = tk.Frame(list_container, bg="#C2DFF7")
        header_row.pack(fill="x")

        for col, h in enumerate(headers):
            label = tk.Label(header_row, text=h, font=("Segoe UI", 10, "bold"),
                            fg="#242525", bg="#C2DFF7", anchor="w", padx=3, pady=5)
            label.grid(row=0, column=col, sticky="ew", padx=(20,0))
            header_row.grid_columnconfigure(col, weight=col+1)  # stretch equally

        # === Canvas and Scrollbar ===
        canvas_frame = tk.Frame(list_container, highlightbackground="#A1A1A1", highlightthickness=1)
        canvas_frame.pack(fill="both", expand=True, pady=(0, 1))

        self.canvas = tk.Canvas(canvas_frame)
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y", pady=(4, 1), padx=0)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # === Scrollable Frame ===
        self.scrollable_frame = ttk.Frame(self.canvas)

        # This line ensures the inner frame will stretch horizontally
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=canvas_frame.winfo_width())
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", tags="frame")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfig("frame", width=event.width))

        # === Mousewheel scrolling ===
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units") #????

        self.scrollable_frame.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.scrollable_frame.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        self.appoints_list = [] 

        # Stretch οι στήλες του scrollable frame
        for col in range(3):
            self.scrollable_frame.grid_columnconfigure(col, weight=col+1)

        ttk.Button(content, text="⬅️ Επιστοφή στη Διαχείριση Πελατών", command=lambda: controller.show_frame("ClientsPage")).pack(anchor="s", pady=(15,10)) # .grid(row=4, column=0, sticky="S", pady=(15,10))

    def find_best_matching_item(self, today):
        future_dates = sorted([x for x in self.items if x[0] >= today], key=lambda x: x[0])
        if future_dates:
            return future_dates[0][1]   # επιστρέφει το item_id της πιο κοντινής μελλοντικής
        past = sorted([x for x in self.items if x[0] < today], key=lambda x: x[0], reverse=True)
        if past:
            return past[0][1] # αλλιώς πάρε την τελευταία διαθέσιμη (πιο κοντινή παρελθοντική)
        return None

    def scroll_to_target(self):
        # print(self.target_index)

        if self.target_index is None:
            return

        visible_rows = 10  # Πόσες σειρές χωράει το frame ορατές
        total_rows = max(len(self.appoints_list), 1)
        max_index = total_rows - 1

        # Υπολόγισε τον μεγαλύτερο δυνατό index που μπορεί να είναι στην κορυφή
        max_top_index = max_index - (visible_rows - 1)

        # Διάλεξε είτε το target index είτε το max_top_index (όποιο είναι μικρότερο)
        top_index = min(self.target_index, max_top_index)
        top_index = max(0, top_index)  # Ασφάλεια: να μην είναι αρνητικός

        # Μετατροπή σε fraction για χρήση στο yview_moveto
        fraction = top_index / total_rows
        self.canvas.yview_moveto(fraction)

        # if self.target_index is None:
        #     return
        # visible_rows = 10
        # max_index = len(self.appoints_list) - 1
        # max_top_index = max_index - (visible_rows - 1)

        # # Το row που θα εμφανιστεί στην κορυφή
        # top_index = min(self.target_index, max_top_index)
        # top_index = max(0, top_index)  # safety
        # # fraction = row_index / total_rows
        # target_fraction = top_index / max_index if max_index > 0 else 0
        # current_fraction = self.canvas.yview()[0]

        # self.animate_scroll(current_fraction, target_fraction)

    def show_appointments(self):
        from datetime import date
        self.items = []  # καθάρισε την παλιά λίστα (αν υπάρχει)
        today = date.today()

        # Καθαρισμός παλιών widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        for i in range(10 - len(self.appoints_list)):
            self.appoints_list.append(["", "", ""])

        # Sort με ημερομηνία
        self.appoints_list.sort(key=lambda x: self.parse_date(x[0]))
       
        # Εμφάνιση
        for row_index, appoint in enumerate(self.appoints_list):
            bg = "#e3f2fd" if row_index % 2 == 0 else "#F5F2E9"
            # if row_index == self.target_index:
            #     bg = "#FFD700"  # highlight today's row
            for col_index, value in enumerate(appoint):
                tk.Label(self.scrollable_frame, text=value, font=("Segoe UI", 10),
                        bg=bg, anchor="w", padx=23, pady=6).grid(
                    row=row_index, column=col_index, sticky="ew"
                )
            # Αν η ημερομηνία είναι στο appoint[0]
            try:
                date_obj = datetime.strptime(appoint[0], "%d-%m-%Y").date()
                self.items.append((date_obj, row_index))  # κρατάμε το index ή row_id
            except Exception:
                continue

        # Βρες το κατάλληλο index, κάνε το κατάλληλο scroll, highlight τη σωστή γραμμή
        self.target_index = self.find_best_matching_item(today)
        self.after(100, self.scroll_to_target)
        self.highlight_target_row()
                

    # Μετατροπή ημερομηνίας για να μπορεί να γίνει sorting
    def parse_date(self, date_str):
        try:
            return datetime.strptime(date_str, "%d-%m-%Y")
        except ValueError:
            return datetime.max

    def customer_info(self, first_name, last_name, phone, email, id):
        # print(first_name, last_name, phone, email, id)
        """
        Επεξεργασία πελάτη και update database
        """
        # print(first_name, last_name, phone, email, id)
        full_name = f"{first_name} {last_name}"
        # show_page = self.controller.frames["ShowClientPage"]
        self.client_name.config(text=full_name)
        # self.controller.show_frame("ShowClientPage")
        self.contact_phone.config(text=phone)
        self.contact_email.config(text=email)
        
        self.appoints_list = self.get_appoints_from_id(id)
        self.show_appointments()
        self.controller.show_frame("ShowClientPage")


    def get_appoints_from_id(self, customer_id):
        try:
            appoints_list = [(a.date, a.time, a.services) for a in Appointment.get_by_customer_id(customer_id)]
            return appoints_list      
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch customers: {e}")
            return []
        
    # def animate_scroll(self, current, target, steps=40, delay=10):
    #     diff = target - current
    #     if abs(diff) < 0.001:
    #         self.canvas.yview_moveto(target)
    #         return

    #     step = diff / steps
    #     next_position = current + step
    #     self.canvas.yview_moveto(next_position)
    #     self.after(delay, lambda: self.animate_scroll(next_position, target, steps, delay))

    def highlight_target_row(self):
        if self.target_index is None:
            return

        for widget in self.scrollable_frame.winfo_children():
            info = widget.grid_info()
            if int(info["row"]) == self.target_index:
                widget.configure(bg="#C6C8E2")  # highlight τη γραμμή
        # self.bg_colors = ["#cbe6ff", "#ffe8cc", "#d2f6e6", "#f5d3f5"]C6C8E2


            
class RemindersPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # === Content Frame ===
        content = ttk.Frame(self, border=1, borderwidth=1, relief="sunken")
        content.pack(fill="both", expand=True, padx=(120,120), pady=20, anchor="center")

        # === Date Picker ===
        self.top_bar = tk.Frame(content, bg="#C2DFF7")
        self.top_bar.pack(fill="x", ipadx=10, ipady=(2))

        # self.get_all()
        self.date_entry = DateEntry(self.top_bar, date_pattern='dd-mm-yyyy', selectbackground="#A1795A", background="#A1795A", headersbackground="#f1ede0", headersforeground="#3F3F3F", showweeknumbers=False, showothermonthdays=False, font=('Segoe UI Variable Text Semiligh', 10),
                               bordercolor="#FDFDFD", weekendbackground="#FDFDFD", normalbackground="#FDFDFD" )
        self.date_entry.pack(side="right", padx=(10,40), pady=(2,1))
        ttk.Label(self.top_bar, text="Όλα τα ραντεβού για:", background="#C2DFF7").pack(side="right", pady=(2,1))

        # sv_ttk.set_theme("light")

        # === Canvas and Scrollbar ===
        canvas_frame = tk.Frame(content, highlightbackground="gray", highlightthickness=1, background="#fdfdfd")
        canvas_frame.pack(fill="both", expand=True, pady=(0, 1))

        canvas = tk.Canvas(canvas_frame)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y", pady=(4,1))
        canvas.configure(yscrollcommand=scrollbar.set)

        # === Scrollable Frame ===
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # === Mousewheel scrolling ===
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units") # -1* DELTA??

        self.scrollable_frame.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.scrollable_frame.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # self.date_entry.bind("<<DateEntrySelected>>", self.load_appoinments)
        
        # self.load_appoinments()

        new_cli_btn = ttk.Button(self, text="Αποστολή Email", style='Accent.TButton', padding=(6,6), width=15)
        new_cli_btn.pack(padx=(300,0), pady=(10,20), side="left")
        new_cli_btn2 = ttk.Button(self, text="Εκτύπωση σε Excel", style='Accent.TButton', padding=(6,6), width=15)
        new_cli_btn2.pack(padx=(0,300), pady=(10,20), side="right")

        # self.update_idletasks()  # Αναγκαστικό redraw πριν εμφανιστεί
        

    def load_appoinments(self, event=None):
        # 1. Καθάρισε όλα τα προηγούμενα rows
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        appoints_by_date = self.get_appointments_by_date()
        if appoints_by_date:     
            if ((len(appoints_by_date)-10) < 10):
                for i in range((12-len(appoints_by_date))):
                    appoints_by_date.append(("","","","", "", "", ""))
            # === Example appointments ===
            for i, appoint in enumerate(appoints_by_date):
                bg = "#e3f2fd" if i % 2 == 0 else "#F5F2E9"
                # Δημιουργία χρονικού διαστήματος
                time_range = ""
                if appoint[2] and appoint[4]:
                    start_time = datetime.strptime(appoint[2], "%H:%M")
                    end_time = start_time + timedelta(minutes=int(appoint[4]))
                    time_range = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"

                # Δημιουργία Frame για κάθε γραμμή
                row_frame = ttk.Frame(self.scrollable_frame)
                row_frame.pack(fill="x", pady=1)

                # Στήλη 1: Χρονικό διάστημα (width=15)
                ttk.Label(
                    row_frame,
                    text=time_range,
                    background=bg,
                    width=14,
                    anchor="w",
                    padding=(12, 7)
                ).pack(side="left")

                # Στήλη 2: Όνομα πελάτη (width=25)
                customer_name = Customer.get_name_by_id(appoint[0]) if appoint[0] else ""
                ttk.Label(
                    row_frame,
                    text=customer_name,
                    background=bg,
                    width=26,
                    anchor="w",
                    padding=(0, 7)
                ).pack(side="left", ipadx=7)

                # Στήλη 3: Υπηρεσία (width=20)
                service = str(appoint[3]) if appoint[3] else ""
                ttk.Label(
                    row_frame,
                    text=service,
                    background=bg,
                    width=12,
                    anchor="w",
                    padding=(0, 7)
                ).pack(side="left", ipadx=(10))

                # Στήλη 4: Σημειώσεις (width=30)
                notes = str(appoint[5]) if appoint[5] else ""
                ttk.Label(
                    row_frame,
                    text=notes,
                    background=bg,
                    width=30,
                    anchor="w",
                    padding=(0, 7)
                ).pack(side="left")                
        else:
            for i in range((12-len(appoints_by_date))):
                appoints_by_date.append(("","","","", "", "", ""))
            for i, appoint in enumerate(appoints_by_date):
                    bg = "#e3f2fd" if i % 2 == 0 else "#F5F2E9"
                    if (i==0):
                        ttk.Label(
                                self.scrollable_frame,
                                text=f"Δεν υπάρχουν ραντεβού για αυτή τη μέρα",
                                background=bg,
                                padding=(12,7),
                                width=94
                                ).pack(anchor="w", pady=1, padx=0)
                    else:
                        ttk.Label(
                                self.scrollable_frame,
                                text="",
                                background=bg,
                                padding=(12,7),
                                width=94
                                ).pack(anchor="w", pady=1, padx=0)
        # sv_ttk.set_theme("light")

    def get_appointments_by_date(self):

        date = self.date_entry.get()  # Get the date from an input field
        try:
            appointments = [(a.customer_id, a.date, a.time, a.services, a.duration, a.notes, a.id) for a in Appointment.get_by_date(date)]
            # print("appointments by date", date, appointments)

            return appointments
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch appointments: {e}")
            return []
        
    # def get_all(self):
    #     try:
    #         appointments = [(a.customer_id, a.date, a.time, a.services, a.duration, a.notes, a.id) for a in Appointment.get_all()]
    #         # print("all appointments", appointments)
    #         return appointments
    #     except Exception as e:
    #         messagebox.showerror("Error", f"Failed to fetch appointments: {e}")
    #         return []

    def on_show(self):
        from datetime import date
        self.date_entry.set_date(date.today())
        self.load_appoinments()
        self.date_entry.bind("<<DateEntrySelected>>", self.load_appoinments)
        


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
    