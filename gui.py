import os
import tkinter as tk
from tkinter import messagebox, ttk, PhotoImage
import database
import models
from models import Customer, Appointment, AppointmentOverlapError
from tkcalendar import DateEntry
from tkcalendar import Calendar
from datetime import datetime, timedelta
from tktooltip import ToolTip
import sv_ttk
from emails_utils import EmailSender
import export_excel
import locale
import platform

def set_greek_locale():
    """
    Ρυθμίζει το ελληνικό locale για την εμφάνιση ημερομηνιών στα ελληνικά.
    Δοκιμάζει διάφορες επιλογές locale ανάλογα με το λειτουργικό σύστημα.
    """
    system = platform.system().lower()
    
    if system == 'windows':
        locales_to_try = ['greek', 'Greek_Greece.1253', 'el_GR']
    else:  # linux/macOS
        locales_to_try = ['el_GR.UTF-8', 'el_GR', 'greek']

    # Δοκιμάζει κάθε locale μέχρι να βρει ένα που δουλεύει
    for loc in locales_to_try:
        try:
            locale.setlocale(locale.LC_TIME, loc)
            # print(f"Eπιτυχία! Tο locale είναι: {loc}")
            return True
        except locale.Error:
            continue
    
    print("Προσοχή! Το Greek locale δεν είναι διαθέσιμο, θα χρησιμοποιηθεί το default...")
    return False

# Εφαρμογή των ελληνικών ρυθμίσεων locale
set_greek_locale()

# Αρχικοποίηση της βάσης δεδομένων
database.setup_database()

class MainApp(tk.Tk):
    """
    Κύρια κλάση της εφαρμογής που διαχειρίζεται το κεντρικό παράθυρο
    και την πλοήγηση μεταξύ των διαφορετικών σελίδων.
    """
    def __init__(self):
        super().__init__()
        self.title("Hairway to heaven")
        self.geometry("900x600+250+150")
        # Κεντράρισμα παραθύρου     ### Κώδικας Σοφοκλή από main.py
        self.update_idletasks()   # Ενημέρωση για να πάρουμε τις σωστές διαστάσεις
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'900x600+{x}+{y}') ###
        sv_ttk.set_theme("light") # Εφαρμογή του light theme από το sv_ttk
        self.resizable(False, False) # δεν επιτρέπει το resize του παραθύρου...
        
        # Φόρτωση - αντικατάσταση favicon
        try:
            current_dir = os.path.dirname(__file__)  # Τρέχων φάκελος του αρχείου
            image_path = os.path.join(current_dir, "images", "favicon.png")
            self.favicon = PhotoImage(file=image_path)
            self.iconphoto(False, self.favicon)
        except:
            print("Πρόβλημα με την φόρτωση εικόνας favicon.png")
            self.favicon = None  # πρέπει να οριστεί στο instance: τα popups το ελέγχουν

        # Header
        self.header = tk.Frame(self, bg="#2196F3", height=40)
        self.header.pack(side="top", fill="x")

        # Κουμπί επιστροφής (εμφανίζεται μόνο όταν δεν είμαστε στο Dashboard)
        self.back_btn = tk.Button(
            self.header,
            text="←",
            font=("Ink Free", 12, "bold"),
            bg="#2196F3",
            activebackground="#2196F3",
            fg="white",
            activeforeground= "#CFE5F8",
            bd=0,
            cursor= "hand2",
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

        self.frames = {}  # Dictionary για αποθήκευση των frames/σελίδων (lazy loading)
        self.current_frame = None  # Τρέχουσα σελίδα

        # Αρχικοποίηση μόνο της αρχικής σελίδας
        self.show_frame("DashboardPage")

    def show_frame(self, page_name):
        """
        Εμφανίζει την επιλεγμένη σελίδα με lazy loading.
        Δημιουργεί τη σελίδα μόνο όταν χρειάζεται για πρώτη φορά.
        """
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

        # Ενημέρωση του τίτλου στο header ανάλογα με τη σελίδα
        titles = {
            "DashboardPage": "Dashboard - Σημερινά Ραντεβού",
            "ClientsPage": "Διαχείριση Πελατών",
            "NewAppointPage": "Δημιουργία Νέου Ραντεβού / Επεξεργασία Ραντεβού",
            "NewClientPage": "Προσθήκη/Επεξεργασία Πελάτη",
            "ShowClientPage": "Ραντεβού του Πελάτη",
            "RemindersPage": "Υπενθύμιση & Εκτύπωση"
        }
        self.header_label.config(text=titles.get(page_name, ""))

        # Εμφάνιση/απόκρυψη κουμπιού επιστροφής
        if page_name == "DashboardPage":
            self.back_btn.pack_forget()
        else:
            self.back_btn.pack(side="right", padx=20, pady=10)

        # Κλήση μεθόδου refresh αν υπάρχει - αν παρουσιαστεί πρόβλημα, αυξάνουμε το χρόνο στο 50, μετά 100 κτλ
        self.after(0, lambda: hasattr(self.current_frame, "on_show") and self.current_frame.on_show())

    def get_frame(self, page_name):
        """
        Επιστρέφει την αναφορά σε μια σελίδα, δημιουργώντας την αν χρειάζεται.
        Χρησιμοποιείται για ασφαλή πρόσβαση σε frames με lazy loading.
        """
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


class CalendarView(tk.Frame):
    """
    Κλάση που δημιουργεί ένα custom ημερολόγιο (σαν το custom Google Calendar) με time slots
    για την εμφάνιση ραντεβού σε μορφή πλέγματος.
    """
    def __init__(self, parent, controller, days=3, dashboard_ref=None):
        super().__init__(parent, bg="#f8fafd")
        self.controller = controller
        self.dashboard_ref = dashboard_ref

        self.days = days # Πόσες ημέρες να εμφανίζει το ημερολόγιο (default: 3)
        self.hours = [f"{h:02}:00" for h in range(10, 20)]  # 10:00 - 20:00
        self.rows = len(self.hours) * 3  # 3 slots ανά ώρα
        self.cols = self.days
        self.slots = {}  # Dictionary: {(day, time): frame}
        self.day_labels = []  # Λίστα για τις ετικέτες ημερών
        self.inner_frames = []  # Λίστα για όλα τα inner frames

        self.bg_colors = ["#e3f2fd", "#F5F2E9", "#d2f6e6", "#fff2f7"] # τα εναλλασσόμενα bg χρώματα στα ραντεβού του custom calendar

        # Flag για την πρώτη εκτέλεση (αποφυγή καθαρισμού-on_show στην αρχή)
        self.first_time = True
        # Δημιουργία του πλέγματος και φόρτωση ραντεβού
        self.build_grid()
        self.load_appointments()

    def build_grid(self, start_date=datetime.today().date()):
        """
        Δημιουργεί το πλέγμα του ημερολογίου με time slots.

        """
        if self.first_time == False:
        # Καθαρισμός παλιών στοιχείων
            for widget in self.winfo_children():
                widget.destroy()

            self.day_labels.clear()
            self.inner_frames.clear()
            self.slots = {}

        self.first_time = False

        # Δημιουργία νέων ημερών
        tk.Label(self, text="", bg="#f8fafd").grid(row=0, column=0)
        # Ετικέτα μήνα
        self.lbl_month = tk.Label(self, text=start_date.strftime("%b"), 
                                font=('Segoe UI Variable Display', 15, "bold"), 
                                bg="#f8fafd", fg="#1F1F1F", padx=9)
        self.lbl_month.grid(row=0, column=0, sticky="nw", columnspan=2, pady=(0,0))

        # Ετικέτες ημερών
        for i in range(self.days):
            day = start_date + timedelta(days=i)
            lbl_day = tk.Label(self, text=day.strftime("%a %d"), 
                             font=('Segoe UI Semibold', 12), 
                             bg="#f8fafd", fg="#1F1F1F")
            lbl_day.grid(row=0, column=i+1, sticky="nsew")
            self.day_labels.append(lbl_day)

        # Δημιουργία slots
        for i, hour in enumerate(self.hours):
            tk.Label(self, text=hour, bg="#f8fafd", width=5, 
                   font=('Segoe UI', 10), fg="#444746").grid(
                row=i*3+2, column=0, rowspan=3, sticky="nsw", padx=(7, 0))
            # Δημιουργία slots για κάθε ημέρα
            for j in range(self.days):
                day = (start_date + timedelta(days=j))
                if hasattr(day, 'date'):
                    day = day.date()

                # Εξωτερικά - εσωτερικά πλαίσια και borders
                outer_frame = tk.Frame(self, bg="white")
                outer_frame.grid(row=i*3+2, column=j+1, rowspan=3, sticky="nsew")
                outer_frame.grid_propagate(False)

                top_border = tk.Frame(outer_frame, height=1, bg="#dde3ea")
                top_border.pack(side="top", fill="x")
                left_border = tk.Frame(outer_frame, width=1, bg="#dde3ea")
                left_border.pack(side="left", fill="y")

                inner_frame = tk.Frame(outer_frame, bg="white")
                inner_frame.pack(expand=True, fill="both")
                self.inner_frames.append(inner_frame)

                # Δημιουργία 3 slots ανά ώρα (κάθε 20 λεπτά)
                for k in range(3):
                    minutes = k * 20
                    time_slot = f"{int(hour[:2]) + minutes // 60:02}:{minutes % 60:02}"
                    # Το πραγματικό slot frame
                    slot = tk.Frame(inner_frame, height=17, bg="white", width=195)
                    slot.pack(fill="x", expand=True)
                    slot.pack_propagate(False)
                    # Αποθήκευση του slot στο dictionary για εύκολη πρόσβαση
                    self.slots[(day.isoformat(), time_slot)] = slot

                    # Προσθήκη hover effects και click events (εκτός Κυριακής-Δευτέρας)
                    if day.weekday() not in [6, 0]:
                        # Αλλαγή background στο hover
                        slot.bind("<Enter>", lambda e, s=slot: s.configure(bg="#f1f1f1"))
                        slot.bind("<Leave>", lambda e, s=slot: s.configure(bg="white"))
                        # Click event για δημιουργία νέου ραντεβού
                        slot.bind("<Button-1>", lambda e, d=day, t=time_slot: self.controller.get_frame("NewAppointPage").create_new_appointment(d, t))

        # # Ρύθμιση του grid layout
        for col in range(self.days + 1):
            self.grid_columnconfigure(col, weight=1)
        for row in range(len(self.hours)*3 + 1):
            self.grid_rowconfigure(row, weight=1)

        def raise_search_list():
            """
            Εσωτερική συνάρτηση που φέρνει το search listbox στο προσκήνιο (lift).
            Χρησιμοποιείται για να διορθώσει θέματα z-order μετά την κατασκευή του grid.
            """
            try:
                dashboard = self.controller.get_frame("DashboardPage")
                if hasattr(dashboard, 'l1'):
                    dashboard.l1.lift()
            except Exception as e:
                print(f"Λάθος στην προσπάθεια lift του listbox: {e}")

        # Προσθήκη καθυστέρησης (1000ms = 1 δευτερόλεπτo) για να καλέσουμε την παραπάνω συνάρτηση αφού έχει φορτώσει η σελίδα
        self.controller.after(2000, raise_search_list)

    def load_appointments(self, start_date=datetime.today().date()):
        """Φορτώνει και εμφανίζει τα ραντεβού στο ημερολόγιο"""

        # Ανάκτηση όλων των ραντεβού για τις εμφανιζόμενες ημέρες
        appointments = []
        for i in range(self.days):
            day_str = (start_date + timedelta(days=i))
            appointments.extend(Appointment.get_by_date(day_str))

        color_index = 0

        for i, app in enumerate(appointments):

            dt, t = app.datetime.split()

            slots_needed = int(app.duration) // 20

            if (dt, t) in self.slots:

                frame = self.slots[(dt, t)]
                try:
                    name = Customer.get_name_by_id(app.customer_id)
                except:
                    name = "Ο Κανένας"
            
                # Δημιουργία ετικέτας για το ραντεβού
                label = tk.Label(frame, text=f"{name}({app.services})", bg=self.bg_colors[color_index % len(self.bg_colors)], fg="#1F1F1F", font=("Segoe UI", 9), anchor="w", width=15)
                label.pack(fill="both", expand=False)
                # Αν το ραντεβού χρειάζεται παραπάνω από 1 slot
                if slots_needed == 2:
                    frame = self.slots[dt, self.add_minutes(t, 20)]
                    frame.configure(height=17)
                    label2 = tk.Label(frame, text="", bg=self.bg_colors[color_index % len(self.bg_colors)], anchor="w", width=15, pady=5)
                    label2.pack(fill="both", expand=False)
                    label2.bind("<Button-1>", lambda e, a=app, n=name: self.controller.get_frame("DashboardPage").show_appointment_popup(a, n))
                if slots_needed == 3:
                    frame = self.slots[dt, self.add_minutes(t, 20)]
                    frame.configure(height=17)
                    label2 = tk.Label(frame, text="", bg=self.bg_colors[color_index % len(self.bg_colors)], anchor="w", width=15, pady=5)
                    label2.pack(fill="both", expand=False)
                    label2.bind("<Button-1>", lambda e, a=app, n=name: self.controller.get_frame("DashboardPage").show_appointment_popup(a, n))
                    frame = self.slots[dt, self.add_minutes(t, 40)]
                    frame.configure(height=17)
                    label3 = tk.Label(frame, text="", bg=self.bg_colors[color_index % len(self.bg_colors)], anchor="w", width=15, pady=1)
                    label3.pack(fill="both", expand=False)
                    label3.bind("<Button-1>", lambda e, a=app, n=name: self.controller.get_frame("DashboardPage").show_appointment_popup(a, n))
                # Κλικ για προβολή λεπτομερειών
                label.bind("<Button-1>", lambda e, a=app, n=name: self.controller.get_frame("DashboardPage").show_appointment_popup(a, n))

                color_index += 1 # Αλλαγή χρώματος για το επόμενο ραντεβού
            else:
                print("❌ ΔΕΝ βρέθηκε στο self.slots!")

    def add_minutes(self, time_str, mins_to_add):
        """Προσθέτει λεπτά σε μια ώρα και επιστρέφει νέα ώρα ως string"""
        hour, minute = map(int, time_str.split(":"))
        total_minutes = hour * 60 + minute + mins_to_add
        new_hour = total_minutes // 60
        new_minute = total_minutes % 60
        return f"{new_hour:02d}:{new_minute:02d}"

    def delete_appointment(self, popup, appointment_id):
        """Διαγράφει ένα ραντεβού από τη βάση δεδομένων"""
        if not messagebox.askyesno("Επιβεβαίωση", "Θέλεις σίγουρα να διαγράψεις αυτό το ραντεβού;"):
            return
    
        try:
            # Διαγραφή από τη βάση
            success = Appointment.delete_from_db(appointment_id)
            if not success:
                messagebox.showerror("Σφάλμα", "Αποτυχία διαγραφής")
                return

            # Επαναφόρτωση του ημερολογίου
            self.controller.get_frame("DashboardPage").on_minical_date_selected()
            
            # Κλείσιμο popup
            popup.destroy()

        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Σφάλμα κατά τη διαγραφή: {str(e)}")

    def rebuild_calendar(self, start_date):
        """Επαναδημιουργεί ολόκληρο το ημερολόγιο για νέα ημερομηνία"""
        # Επαναδημιουργία πλέγματος
        self.build_grid(start_date)
        self.load_appointments(start_date)
        

class DashboardPage(tk.Frame):
    """Κύρια σελίδα εφαρμογής που εμφανίζει το ημερολόγιο και τα σημερινά ραντεβού."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.open_for_first_time = True
        # Φόρτωση εικόνας
        try:
            current_dir = os.path.dirname(__file__) 
            image_path = os.path.join(current_dir, "images", "closebtn_square.png")
            self.closebtn_square = PhotoImage(file=image_path)
        except:
            print("Πρόβλημα με την φόρτωση εικόνας closebtn_square.png")
            self.closebtn_square = None
        
        # Left Side Menu
        self.left_menu = tk.Frame(self, bg="#F4F4F4", width=224)
        self.left_menu.pack(side="left", fill="y")
        self.left_menu.pack_propagate(False)

        # Mini Calendar
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
                             headersforeground="#505E66",
                             padding=0,
                             bordercolor="#F5F5F5",
                            weekendbackground="#F5F5F5",
                            normalbackground="#F5F5F5",
                            highlightthickness=1
                             )
        self.minical.pack(pady=(20,0), padx=(10,13), fill="both", expand=1, side="top", anchor="n")

        self.minical.bind("<<CalendarSelected>>", self.on_minical_date_selected)
        # Διαχωριστική γραμμή
        ttk.Separator(self.left_menu).pack(fill="both", ipady=1, padx=5)

        # === Search πελατών ===
        # Search Listbox
        # exportselection=0: το listbox δεν διεκδικεί το PRIMARY selection, ώστε να μη χάνει
        # την επιλογή του (και να μη στέλνει κενό <<ListboxSelect>>) όταν επιλέγει ο χρήστης αλλού
        self.l1 = tk.Listbox(self, relief="flat", width=1, bg="#f0f0f0", borderwidth=1, highlightthickness=1, font=("Segoe UI", 10), exportselection=0)
        
        # Κουμπί κλεισίματος λίστας  
        self.close_btn = tk.Button(
            self,
            image=self.closebtn_square,
            text="" if self.closebtn_square else "X",  # Fallback
            bg=self["bg"] if self.closebtn_square else"#e3f2fd",
            activebackground=self["bg"],
            borderwidth=0,
            highlightthickness=0,
            border=0,
            relief="flat",
            cursor="hand2",
            command=lambda: (self.l1.place_forget(), self.close_btn.place_forget(), self.scrollbar.place_forget(), self.newclient_btn.place_forget())
        )
        # Scrollbar για τη λίστα
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.l1.yview)
        self.l1.configure(yscrollcommand=self.scrollbar.set)
        self.newclient_btn = tk.Button(
            self.l1,
            text="Δημιουργία Νέου Πελάτη",
            cursor="hand2",
            bg="white", # "#83b3db" bg = "#e3f2fd" if row_index % 2 == 0 else "#F5F2E9"
            # highlightcolor="#ffa82e",
            # activebackground="#fc962a",
            activeforeground="#000000",
            fg="#505E66",
            # relief=tk.FLAT,
            relief="ridge",
            borderwidth=0,
            highlightthickness=0,
            border=0,
            bd=1,
            padx=6,
            pady=5,
            width=21,
            font=('"Segoe UI Semibold" 10'),
            # anchor="w",
            command=lambda: self.show_new_client_popup()
        )
        # Search Entry
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.search_customer)
        self.search_client = tk.Entry(self.left_menu,
                                textvariable=self.search_var,
                                  font=('Segoe UI', 10),
                                    relief="flat",
                                      bg="white", fg="#444756",
                                        border=1, borderwidth=8,
                                            highlightbackground="#e9e9e9", highlightthickness=1, highlightcolor="#C3C6CA", insertbackground="#686868",
                                              width=25)
        self.search_client.insert(0, "🔍 Επώνυμο & Τηλέφωνο")
        self.search_client.bind("<FocusIn>", lambda args: self.search_client.delete('0', 'end'))
        # self.search_client.bind("<FocusOut>", lambda args: self.search_client.insert(0, "🔍Επώνυμο ή Τηλ"))
        self.search_client.pack(anchor="nw", pady=(15,45), ipady=0, padx=13, expand=1)

        def add_hover_effect(button, base_color, hover_color, active_color, hover_fg=None):
            button.configure(bg=base_color, activebackground=active_color)

            def on_enter(e):
                button['background'] = hover_color
                button['fg'] = hover_fg

            def on_leave(e):
                button['background'] = base_color

            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)
        
        add_hover_effect(
            self.newclient_btn,
            base_color="#FFFFFF",      # λευκό
            hover_color="#F8F8F8",     # λίγο πιο σκοτεινό άσπρο
            active_color="#ECECEC",     # ακόμα λίγο πιο σκοτεινό άσπρο
            hover_fg = "#000000",
        )
        # Νέο Ραντεβού Button
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
            command=lambda: controller.show_frame("NewAppointPage")
        )
        add_hover_effect(
            self.new_appt_btn,
            base_color="#4CAF50",      # πράσινο
            hover_color="#4ebb4e",     # λίγο πιο φωτεινό
            active_color="#4FB154"     # πιο σκούρο
        )

        # Πελάτες Button
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
        add_hover_effect(
            self.clients_btn,
            base_color="#fd9827",
            hover_color="#ffa82e",     # πιο φωτεινό πορτοκαλί
            active_color="#fc962a"     # πιο σκούρο πορτοκαλί
        )

        # Email/Print Button
        self.remind_btn = tk.Button(
            self.left_menu,
            text="Email/Print",
            bg="#e72565",  # ροζ
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=22,
            pady=3,
            width=9,
            font=('"Segoe UI Semibold" 10'),
            command=lambda: controller.show_frame("RemindersPage")
        )
        add_hover_effect(
            self.remind_btn,
            base_color="#e72565",
            hover_color="#f5417d",     # πιο φωτεινό ροζ
            active_color="#d12c5d"     # πιο σκούρο ροζ
        )
        # Τοποθέτηση κουμπιών
        self.remind_btn.pack(pady=(8,25), padx=13, side="bottom", anchor="w")
        self.clients_btn.pack(pady=0, padx=13, side="bottom", anchor="w")
        self.new_appt_btn.pack(pady=8, padx=13, side="bottom", anchor="w")
        # Tooltip για το κουμπί Email/Print
        ToolTip(self.remind_btn, msg="- Αποστολή email σε όλους τους πελάτες που\nέχουν ραντεβού μια συγκεριμένη μέρα\n\n- Εκτύπωση των ραντεβού της ημέρας σε Excel", delay=0.8,
        parent_kwargs={"bg": "#FFFFFF", "padx": 0, "pady": 0},
        fg="#ffffff", bg="#505E66", padx=7, pady=7)
        # Υπήρχε πρόβλημα με το listbox κι έτσι επιστρατεύθηκαν η hide_listbox_if_needed και τα binds
        self.search_client.bind("<FocusOut>", lambda e: self.hide_listbox_if_needed())
        self.l1.bind("<B1-Motion>", lambda e: "break")  # Αριστερό κλικ drag
        self.l1.bind("<B3-Motion>", lambda e: "break")  # Μεσαίο κλικ drag
        self.l1.bind("<B3-Motion>", lambda e: "break")  # Δεξί κλικ drag
        self.l1.bind("<FocusOut>", lambda e: self.hide_listbox_if_needed())

        # Περιεχόμενο
        content = tk.Frame(self, bg="#f8fafd")
        content.pack(side="left", fill="both", expand=True, padx=0, pady=0)

        self.calendar_view = CalendarView(content, controller, days=3)
        self.calendar_view.pack(side="left", fill="both", expand=True, padx=7, pady=(0,3))

        self.l1.place_forget()
        self.close_btn.place_forget()
        self.scrollbar.place_forget()
        self.newclient_btn.place_forget()

    def on_minical_date_selected(self, event=None):
        """Επαναφόρτωση ημερολογίου όταν επιλέγεται νέα ημερομηνία"""
        try:
            selected_date = self.minical.selection_get()
            self.calendar_view.rebuild_calendar(selected_date)
        except:
            selected_date = datetime.now().date()  # Fallback σε σημερινή ημερομηνία
            self.calendar_view.rebuild_calendar(selected_date)

    def hide_listbox_if_needed(self, event=None):
        """Κρύβει τη λίστα αναζήτησης αν ο χρήστης κάνει κλικ αλλού"""
        mouse_over_listbox = (self.l1.winfo_containing(event.x_root, event.y_root) if event else False)
        mouse_over_entry = (self.search_client.winfo_containing(event.x_root, event.y_root) if event else False)
        
        if not (self.search_client.focus_get() in [self.search_client, self.l1] or 
                mouse_over_listbox or 
                mouse_over_entry):
            self.l1.place_forget()
            self.scrollbar.place_forget()
            self.close_btn.place_forget()
            self.newclient_btn.place_forget() # βγάζει πρόβλημα με το ttk.Button. Το κουμπί πριν δώσει την εντολή εξαφανίζεται.
            

    def search_customer(self, *args):
        """Αναζήτηση πελατών βάσει ονόματος ή τηλεφώνου"""
        self.query = self.search_var.get().strip().lower()

        customer_list = self.show_all_customers()

        # Φιλτράρισμα
        filtered_customers = [
            customer for customer in customer_list
            if self.query in customer[1].lower() or self.query in customer[2]
        ]

        def my_upd(my_widget):
            """Επεξεργασία επιλογής πελάτη από τη λίστα"""
            my_w = my_widget.widget
            selection = my_w.curselection()
            if not selection:
                # Κενή επιλογή: το listbox απλώς έχασε το selection (exportselection),
                # π.χ. όταν επιλέγει ο χρήστης σε άλλο listbox/Entry. Δεν είναι επιλογή πελάτη.
                return
            index = int(selection[0])
            customer = filtered_customers[index]
            self.selected_id = customer[3] # είναι το customer_id που αντιστοιχεί στο συγκεκριμένο index της listbox
            value = my_w.get(index).strip()
            self.selected_name = value
            self.search_var.set(value)
            self.l1.place_forget()
            self.close_btn.place_forget()
            self.scrollbar.place_forget()
            self.newclient_btn.place_forget()
            self.focus_set()

        self.l1.delete(0, 'end')

        # if not filtered_customers and self.query:  # Αν δεν βρέθηκαν αποτελέσματα
        if not filtered_customers and len(self.query) >= 2:  # Μόνο αν έχει πληκτρολογήσει τουλάχιστον 2 χαρακτήρες

            self.l1.insert(tk.END, "   Ο πελάτης δε βρέθηκε...")

            self.l1.itemconfig(0, {'fg': 'black'})

            # Απενεργοποίηση αλληλεπίδρασης
            self.l1.bind("<Button-1>", lambda e: "break")  # Απενεργοποιεί αριστερό κλικ
            self.l1.bind("<Double-Button-1>", lambda e: "break")  # Απενεργοποιεί διπλό κλικ
            self.l1.bind("<Return>", lambda e: "break")  # Αν πατήσει Enter
        else:
            self.newclient_btn.place_forget()
            # Αν υπάρχουν πελάτες, επαναφέρουμε τα bindings
            self.l1.unbind("<Button-1>")
            self.l1.unbind("<Double-Button-1>")
            self.l1.unbind("<Return>")
            for customer in filtered_customers:
                full_name = f"{customer[0]} {customer[1]}"
                self.l1.insert(tk.END,f" {full_name}")
            self.l1.bind("<<ListboxSelect>>", my_upd)
            
        # Διαμόρφωση εμφάνισης λίστας
        for row_index in range(len(filtered_customers)):
            bg = "#e3f2fd" if row_index % 2 == 0 else "#F5F2E9"
            self.l1.itemconfig(row_index,{'bg': bg})
            self.l1.itemconfig(row_index,{'bg': bg})
        # Τοποθέτηση λίστας αναζήτησης, κουμπιού κλεισίματος, scrollabar και κουμπιού για νέα πελάτη μέσα στο listbox
        self.l1.place(
                        relx=0.01, rely=0.53,
                        width=204, height=241)
        
        self.close_btn.place(
                        relx=0.237, rely=0.482,)
        
        self.scrollbar.place(
            x=10+202,
            y=self.search_client.winfo_y() + self.search_client.winfo_height() + 5,
            height=235
        )
        self.newclient_btn.place(
                        relx=0.034, rely=0.120,)
        self.l1.lift()
        self.scrollbar.lift()
        self.close_btn.lift()

        if "βρέθηκε" in self.l1.get(0):
            self.newclient_btn.lift()
        else:
            self.newclient_btn.place_forget()

    def create_new_client(self, event):
        """Δημιουργία νέου πελάτη"""
        widget = event.widget
        selection = widget.curselection()
        if selection and widget.get(selection[0]) == "   Ο πελάτης δε βρέθηκε...":
            self.show_new_client_popup()
        self.focus_set()

    def show_new_client_popup(self):
        """Εμφάνιση popup για δημιουργία νέου πελάτη"""
        popup = tk.Toplevel(self)
        popup.title("Νέος Πελάτης")
        popup.geometry("600x400")
        popup.resizable(False, False)  # Απενεργοποίηση αλλαγής μεγέθους
        
        # Φόρτωση της σελίδας NewClientPage μέσα στο popup
        new_client_frame = NewClientPage(popup, self.controller)
        new_client_frame.pack(fill="both", expand=True)

        # Κεντράρισμα popup
        popup.update_idletasks()
        width = popup.winfo_width()
        height = popup.winfo_height()
        x = (popup.winfo_screenwidth() // 2) - (width // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")

        # Απόκρυψη listbox και των στοιχείων του
        self.l1.place_forget()
        self.close_btn.place_forget()
        self.scrollbar.place_forget()
        self.newclient_btn.place_forget()

        if self.controller.favicon: # αν λείπει η εικόνα, το popup ανοίγει με το default εικονίδιο
            popup.iconphoto(False, self.controller.favicon) # favicon για popup, πρέπει να μπει κάτω από το κεντράρισμα αλλιώς βγάζει πρόβλημα
        
        self.current_popup = popup
        # Bind το κλείσιμο του popup
        popup.protocol("WM_DELETE_WINDOW", lambda: self.on_popup_close(popup))

        def force_focus(self, popup):
            try:
                popup.lift()
                popup.grab_set() # Απαιτεί από τον χρήστη να αλληλεπιδράσει πρώτα με αυτό το παράθυρο
                popup.focus_force() # Δίνει focus στο popup
            except Exception as e:
                print("Force focus error:", e)

        self.after(300, lambda: force_focus(self, self.current_popup))
  
    def show_appointment_popup(self, appointment, customer_name): # ανενεργό προς το παρόν
        """Εμφάνιση popup με λεπτομέρειες ραντεβού"""
        popup = tk.Toplevel(self)
        popup.title("Λεπτομέρειες Ραντεβού")
        popup.geometry("600x400")
        popup.resizable(False, False)
        popup.grab_set()
        popup.focus_set() 
        dt, t = appointment.datetime.split()
        date_obj = datetime.strptime(dt, "%Y-%m-%d")
        day = date_obj.strftime("%A")
        date_with_day_infront = f"{day} {date_obj.strftime('%d-%m-%Y')}"
        customer = Customer.get_customer_by_id(appointment.customer_id)
        tk.Label(popup, text=f"{date_with_day_infront}", font=('Segoe UI Semibold', 14)).pack(padx=10, pady=(20,0))
        tk.Label(popup, text=f"Ώρα: {t}", font=('Segoe UI Semibold', 11)).pack(padx=10)
        tk.Label(popup, text=f"Διάρκεια: {appointment.duration} λεπτά", font=('Segoe UI Semibold', 11)).pack(padx=10, pady=(0,0))
        tk.Label(popup, text=f"Υπηρεσία: {appointment.services}", font=('Segoe UI Semibold', 11)).pack(padx=10, pady=(0,10))
        tk.Label(popup, text=f"{customer_name}", font=('Segoe UI Semibold', 14)).pack(padx=10, pady=(5,0))
        tk.Label(popup, text=f"Τηλέφωνο: {customer.phone}", font=('Segoe UI Semibold', 11)).pack(padx=10, pady=0)
        tk.Label(popup, text=f"Email: {customer.email}", font=('Segoe UI Semibold', 11)).pack(padx=10, pady=(0,10))
        tk.Label(popup, text=f"Σημείωση: {appointment.notes or '-'}", font=('Segoe UI Semibold', 11)).pack(padx=10, pady=(10,40))

        btn_frame = ttk.Frame(popup)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Επεξεργασία", style='Accent.TButton', command=lambda a=appointment: self.controller.get_frame("NewAppointPage").edit_appoint(a.customer_id, customer_name, a.datetime, a.services, a.notes, a.id, popup)).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Διαγραφή", command=lambda: self.calendar_view.delete_appointment(popup, appointment.id)).pack(side="left", padx=5)

        # Κεντράρισμα popup
        popup.update_idletasks()
        width = popup.winfo_width()
        height = popup.winfo_height()
        x = (popup.winfo_screenwidth() // 2) - (width // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")

        if self.controller.favicon: # αν λείπει η εικόνα, το popup ανοίγει με το default εικονίδιο
            popup.iconphoto(False, self.controller.favicon) # favicon για popup, πρέπει να μπει κάτω από το κεντράρισμα αλλιώς βγάζει πρόβλημα
        
        self.current_popup = popup
        # Bind το κλείσιμο του popup
        popup.protocol("WM_DELETE_WINDOW", lambda: self.on_popup_close(popup))

    def on_popup_close(self, popup=None):
         # Βρες όλα τα ανοιχτά Toplevel που ανήκουν σε αυτό το παράθυρο και κλείστα
        open_popups = [
            w for w in self.winfo_children() 
            if isinstance(w, tk.Toplevel) and w.winfo_exists()
        ]
        
        for popup in open_popups:
            popup.destroy()
        self.search_client.delete(0, tk.END)  # Καθαρισμός αναζήτησης
        self.search_client.insert(0, "🔍 Επώνυμο & Τηλέφωνο")
        self.l1.place_forget()
        self.close_btn.place_forget()
        self.scrollbar.place_forget()
        self.newclient_btn.place_forget()
        self.focus_set()        
        
    def show_all_customers(self):
        """Επιστροφή λίστας με όλους τους πελάτες (όνομα, επίθετο, τηλέφωνο, id)"""
        try:
            customers_list = [(c.first_name, c.last_name, c.phone, c.id) for c in Customer.get_all()]
            return customers_list
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch customers: {e}")
            return []
        
    def on_show(self):
        """Επαναφέρει τα πεδία όταν ανοίγει η σελίδα."""
        if self.open_for_first_time == True:
            pass
        else:
            self.search_client.delete(0, tk.END)
            self.search_client.insert(0, "🔍 Επώνυμο & Τηλέφωνο")
            # 1. Λήψη σημερινής ημερομηνίας
            today = datetime.today().date()
            # 2. Ορισμός επιλογής στο calendar
            self.minical.selection_set(today)
            selected_date = today  # Fallback σε σημερινή ημερομηνία
            self.calendar_view.rebuild_calendar(selected_date)
            self.l1.place_forget()
            self.close_btn.place_forget()
            self.scrollbar.place_forget()
            self.newclient_btn.place_forget()
            self.focus_set()    
        self.open_for_first_time = False      


class ClientsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        sv_ttk.set_theme("light")

        # Content
        content = tk.Frame(self, padx=40, pady=20)
        content.pack(expand=1, fill="both")
        # List Container Frame
        list_container = ttk.Frame(content, border=1, borderwidth=1, relief="sunken")
        # Canvas and Scrollbar
        canvas_frame = tk.Frame(list_container, highlightbackground="gray", highlightthickness=1, background="#fdfdfd")
        canvas = tk.Canvas(canvas_frame)
        # Scrollable Frame
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
                                                    self.controller.show_frame("NewClientPage")
                                                ))
        new_cli_btn.pack(anchor="w", pady=(20,0))

        list_container.pack(fill="both", expand=True, padx=(0), pady=(20), anchor="center")

        # Header Row
        headers = ["Επώνυμο", "Όνομα", "Τηλέφωνο", "Email", "Ενέργειες"]
        header_row = tk.Frame(list_container, bg="#C2DFF7")
        for h in headers:
            label = tk.Label(header_row, text=h, font=("Segoe UI", 10, "bold"), fg="#242525", bg="#C2DFF7", width=18, anchor="w")
            label.pack(side="left",pady=(2,1), anchor="w", padx=(18,0))
        header_row.pack(fill="x", ipady=(2))


        # Canvas and Scrollbar
        canvas_frame.pack(fill="both", expand=True, pady=(0, 1))


        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y", pady=(4,1))
        canvas.configure(yscrollcommand=scrollbar.set)

        # Scrollable Frame
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.scrollable_frame.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.scrollable_frame.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

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
        filtered_customers.sort(key=lambda x: (x[1] == "", x[1])) #πιθανόν δε χρειάζεται πια, γίνεται από το models

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
                # Delete Button
                tk.Button(
                    row,
                    text=" 🗑️",
                    font=(18),
                    fg="#242525",
                    activeforeground="#e72565",
                    background=bg,
                    command=lambda c=customer: self.delete_and_reload(c),
                    width=4,
                    relief="flat",
                    cursor="hand2",
                    bd=0,  
                    highlightthickness=0, 
                    activebackground=bg  
                ).pack(side="right", padx=2, anchor="center")

                # Edit Button
                tk.Button(
                    row,
                    text="   🖋️",
                    font=(18),
                    fg="#242525",
                    activeforeground="#fd9827",
                    background=bg,
                    command=lambda c=customer: self.controller.get_frame("NewClientPage").edit_customer(c[0], c[1], c[2], c[3], c[4]),
                    width=4,
                    relief="flat",
                    cursor="hand2",
                    bd=0,
                    highlightthickness=0,
                    activebackground=bg
                ).pack(side="right", padx=2)

                # View Button
                tk.Button(
                    row,
                    text="🔍",
                    font=(18),
                    fg="#242525",
                    activeforeground="#4CAF50",
                    background=bg,
                    command=lambda c=customer: self.controller.get_frame("ShowClientPage").customer_info(c[0], c[1], c[2], c[3], c[4]),
                    width=3,
                    relief="flat",
                    cursor="hand2",
                    bd=0,
                    highlightthickness=0,
                    activebackground=bg
                ).pack(side="right", padx=2)
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

        # Εμφάνιση
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
                # Delete Button
                tk.Button(
                    row,
                    text=" 🗑️",
                    font=(18),
                    fg="#242525",
                    activeforeground="#e72565",
                    background=bg,
                    command=lambda c=customer: self.delete_and_reload(c),
                    width=4,
                    relief="flat",
                    cursor="hand2",
                    bd=0,  
                    highlightthickness=0, 
                    activebackground=bg  
                ).pack(side="right", padx=2, anchor="center")

                # Edit Button
                tk.Button(
                    row,
                    text="   🖋️",
                    font=(18),
                    fg="#242525",
                    activeforeground="#fd9827",
                    background=bg,
                    command=lambda c=customer: self.controller.get_frame("NewClientPage").edit_customer(c[0], c[1], c[2], c[3], c[4]),
                    width=4,
                    relief="flat",
                    cursor="hand2",
                    bd=0,
                    highlightthickness=0,
                    activebackground=bg
                ).pack(side="right", padx=2)

                # Show Button
                tk.Button(
                    row,
                    text="🔍",
                    font=(18),
                    fg="#242525",
                    activeforeground="#4CAF50",
                    background=bg,
                    command=lambda c=customer: self.controller.get_frame("ShowClientPage").customer_info(c[0], c[1], c[2], c[3], c[4]),
                    width=3,
                    relief="flat",
                    cursor="hand2",
                    bd=0,
                    highlightthickness=0,
                    activebackground=bg
                ).pack(side="right", padx=2)
            else:
                tk.Label(row, text=" ", background=bg, width=9).pack(side="right", padx=20, pady=(5,6), fill="x")

            row.pack(fill="x", pady=1)

    def delete_and_reload(self, client):
        if messagebox.askyesno("Επιβεβαίωση", f"Να διαγραφεί ο/η {client[0]} {client[1]};"):
            Customer.delete_from_db(client[2])
            self.load_clients()

    def show_all_customers(self):
        try:
            customers_list = [(c.first_name, c.last_name, c.phone, c.email, c.id) for c in Customer.get_all()]
            return customers_list
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch customers: {e}")
            return []
        
    def on_show(self):
        self.focus_set()  # Αφαιρεί το focus από το search_entry
        self.search_var.set("   Αναζήτηση με όνομα ή τηλέφωνο...")
        self.load_clients()


class NewAppointPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.editing = False
        self.selected_name = ""
        self.selected_id = None
        self.current_customer_id = None
        self.current_appointment_id = None
        self.loaded_customer_name = "" # το όνομα που φορτώθηκε στο πεδίο κατά το edit, για να ξεχωρίζουμε "ανέγγιχτο" από "ελεύθερο κείμενο"
        self.datetime_obj = None # για την περίπτωση του edit: δεν θέλουμε να αφαιρούνται τα time_options που αφορούν το συγκεκριμένο ραντεβού
        self.onlyinit = True
        # Φόρτωση εικόνας
        try:
            current_dir = os.path.dirname(__file__)  # /appointment_system/gui/
            image_path = os.path.join(current_dir, "images", "closebtn_rounded.png")
            self.closebtn_rounded = PhotoImage(file=image_path)
        except:
            print("Πρόβλημα με την φόρτωση εικόνας closebtn_rounded.png")
            self.closebtn_rounded = None

        self.content = ttk.Frame(self, padding=(260,25), border=5, borderwidth=3)
        self.content.pack(expand=1, ipady=10, fill="both")

        ttk.Label(self.content, text="Πελάτης:", anchor="w", width=20).grid(row=0, column=0, sticky="w", pady=10)

        # exportselection=0: το listbox δεν διεκδικεί το PRIMARY selection, ώστε να μη χάνει
        # την επιλογή του (και να μη στέλνει κενό <<ListboxSelect>>) όταν επιλέγει ο χρήστης αλλού
        self.l1 = tk.Listbox(self.content, relief="flat", width=35, bg="#f0f0f0", borderwidth=1, highlightthickness=1, font=("Segoe UI", 10), exportselection=0)
        self.close_btn = tk.Button(
                    self.content,
                    image=self.closebtn_rounded,
                    text="" if self.closebtn_rounded else "X",  # Fallback
                    bg=self["bg"] if self.closebtn_rounded else"#e3f2fd",
                    bd=0,
                    activebackground=self["bg"],  # για να μη δείχνει γκρι όταν πατιέται
                    # bg=self["bg"]  # ή απλώς αφαίρεσέ το τελείως
                    borderwidth=0,
                    highlightthickness=0,
                    relief="flat",
                    cursor="hand2",
                    command=lambda: (self.l1.place_forget(), self.close_btn.place_forget(), self.scrollbar.place_forget(), self.newclient_btn.place_forget())
                )        
        self.scrollbar = ttk.Scrollbar(self.content, orient="vertical", command=self.l1.yview)
        self.l1.configure(yscrollcommand=self.scrollbar.set)
        self.newclient_btn = tk.Button(
            self.l1,
            text="Δημιουργία Νέου Πελάτη",
            cursor="hand2",
            bg="white",
            activeforeground="#000000",
            fg="#505E66",
            relief="ridge",
            borderwidth=0,
            highlightthickness=0,
            border=0,
            bd=1,
            padx=6,
            pady=4,
            width=21,
            font=('"Segoe UI Semibold" 10'),
            command=lambda: self.show_new_client_popup()
        )
        def add_hover_effect(button, base_color, hover_color, active_color, hover_fg=None):
            button.configure(bg=base_color, activebackground=active_color)

            def on_enter(e):
                button['background'] = hover_color
                button['fg'] = hover_fg

            def on_leave(e):
                button['background'] = base_color

            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)
        
        add_hover_effect(
            self.newclient_btn,
            base_color="#FFFFFF",      # λευκό
            hover_color="#F8F8F8",     # λίγο πιο σκοτεινό άσπρο
            active_color="#ECECEC",     # ακόμα λίγο πιο σκοτεινό άσπρο
            hover_fg = "#000000",
        )
        # Πεδίο αναζήτησης
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.search_customer)
        self.search_client = ttk.Entry(self.content, textvariable=self.search_var)
        self.search_client.insert(0, "🔍Επώνυμο & Τηλέφωνο")
        self.search_client.bind("<FocusIn>", lambda args: self.search_client.delete('0', 'end'))

        self.search_client.grid(row=0, column=1, sticky="w", pady=10)

        # Πρέπει να γίνει update για να ξέρουμε τις συντεταγμένες του entry
        self.search_client.update_idletasks()

        ttk.Label(self.content, text="Ημερομηνία:", anchor="w", width=20).grid(row=1, column=0,sticky="w", pady=10)
        self.appoint_date = DateEntry(self.content, date_pattern='dd-mm-yyyy', width=16, selectbackground="#505E66", background="#505E66", headersbackground="#f1ede0", headersforeground="#505E66", showweeknumbers=False, bordercolor="#FDFDFD", weekendbackground="#FDFDFD", normalbackground="#FDFDFD" )

        self.appoint_date.grid(row=1, column=1, sticky="w", pady=10)
       
        ttk.Label(self.content, text="Είδος υπηρεσίας:", anchor="w", width=20).grid(row=2, column=0, sticky="w", pady=10) # multiple options? Checkbox?
        service_var = tk.StringVar(self.content, value="Κούρεμα")
        self.service_dropdown = ttk.Combobox(self.content, textvariable=service_var, values=["Κούρεμα","Βάψιμο","Χτένισμα"], state="readonly", width=16)
        self.service_dropdown.grid(row=2, column=1, sticky="w", pady=10)

        ttk.Label(self.content, text="Ώρα:", anchor="w", width=20).grid(row=3, column=0, sticky="w", pady=10)
        time_var = tk.StringVar(self.content)
        self.time_dropdown = ttk.Combobox(self.content, textvariable=time_var, values=[], state="disabled", width=16)
        self.time_dropdown.grid(row=3, column=1, sticky="w", pady=10)
        ToolTip(self.time_dropdown, msg="- Επιλέξτε πρώτα Ημερομηνία και Υπηρεσία\nώστε να εμφανιστούν οι διαθέσιμες ώρες.", delay=0.5,
        parent_kwargs={"bg": "#FFFFFF", "padx": 0, "pady": 0},
        fg="#ffffff", bg="#505E66", padx=7, pady=7)

        ttk.Label(self.content, text="Σημειώσεις:", anchor="w", width=20,).grid(row=4, column=0, sticky="nw", pady=(10,10))
        self.notes = tk.Text(self.content, height=3, width=15, bg="#fdfdfd", highlightbackground="white", padx=8, pady=8, wrap=tk.WORD)

        self.notes.grid(row=5, column=0, columnspan=2, padx=0, ipady=35, ipadx=100, sticky="nw")
        
        self.l1.place_forget()
        self.close_btn.place_forget()
        self.scrollbar.place_forget()
        self.newclient_btn.place_forget()

        # Κάθε φορά που αλλάζει η Ημερομηνία ή η Υπηρεσία, ξαναϋπολόγισε τις διαθέσιμες ώρες
        self.appoint_date.bind("<<DateEntrySelected>>", self.get_time_options)
        self.service_dropdown.bind("<<ComboboxSelected>>", self.get_time_options)

        # Όταν χάνει το focus, κρύψε το Listbox
        self.search_client.bind("<FocusOut>", lambda e: self.hide_listbox_if_needed())
        self.l1.bind("<B1-Motion>", lambda e: "break")  # Αριστερό κλικ drag
        self.l1.bind("<B3-Motion>", lambda e: "break")  # Μεσαίο κλικ drag
        self.l1.bind("<B3-Motion>", lambda e: "break")  # Δεξί κλικ drag
        self.l1.bind("<FocusOut>", lambda e: self.hide_listbox_if_needed())
        

        save_btn = ttk.Button(self.content, text="Αποθήκευση", width=12, underline=1, style='Accent.TButton', command=self.save_appoint).grid(row=6, column=1, pady=(40,15), sticky="w", padx=0)
        cancel_btn = ttk.Button(self.content, text="Ακύρωση", width=12, underline=1, command=lambda: self.controller.show_frame("DashboardPage")).grid(row=6, column=0, pady=(40,15), sticky="e", padx=15)

    def get_time_options(self, event=None):
        service_durations = {"Κούρεμα": 40, "Χτένισμα": 20, "Βάψιμο": 60}
        all_time_options = [f"{h:02d}:{m:02d}" for h in range(10, 20) for m in range(0, 60, 20)]

        unavailable = set()

        # Διαβάζουμε το πεδίο μία φορά - μπορεί να είναι κενό (π.χ. καθαρίζεται όταν επιλεγεί κλειστή ημέρα)
        date_str = self.appoint_date.get()

        if date_str:
            date_obj = datetime.strptime(date_str, "%d-%m-%Y")
            date_iso = date_obj.date().isoformat()

            if date_obj.weekday() in [6, 0]:
                if datetime.today().date() != date_obj.date():
                    messagebox.showerror("Μη διαθέσιμη ημέρα", f"Το κομμωτήριο είναι κλειστό Κυριακές και Δευτέρες.\nΠαρακαλώ επιλέξτε άλλη ημέρα.")
                self.appoint_date.delete(0, 'end')
                date_str = ""  # το πεδίο καθαρίστηκε - δεν υπάρχει πλέον έγκυρη ημερομηνία

            appointments_of_day = Appointment.get_by_date(date_iso) if date_str else []
            
            for app in appointments_of_day:
                dt_obj = datetime.strptime(app.datetime, "%Y-%m-%d %H:%M")
                if dt_obj == self.datetime_obj: # για την περίπτωση edit. Οι χρόνοι (ημερομηνία και ώρα) του επίμαχου ραντεβού, να μην συμπεριληφθούν στο unavailable, δηλαδή στις επικαλυπτόμενες ώρες
                    continue
                hour, minute = dt_obj.hour, dt_obj.minute
                duration = service_durations.get(app.services, 20)

                for offset in range(0, duration, 20):
                    total_minutes = hour * 60 + minute + offset
                    h, m = divmod(total_minutes, 60)
                    unavailable.add(f"{h:02d}:{m:02d}")

        # Αν υπάρχει επιλεγμένη υπηρεσία, φιλτράρουμε σύμφωνα με διάρκεια
        selected_service = self.service_dropdown.get()
        duration = service_durations.get(selected_service, 20)
        # Αν δεν είναι επιλεγμένα και τα δύο, τότε απενεργοποίησε time_dropdown και σταμάτα
        if not date_str or not selected_service:
            self.time_dropdown['state'] = 'disabled'
            self.time_dropdown.set('')
            return
            
        time_options = []
        for time_str in all_time_options:
            h, m = map(int, time_str.split(':'))
            total_minutes = h * 60 + m
            end_time = total_minutes + duration

            if end_time > 20 * 60:  # Δεν επιτρέπεται να ξεπερνά τις 20:00
                continue

            # Έλεγχος αν κάποιο από τα slots που καταλαμβάνει το ραντεβού είναι ήδη πιασμένο
            overlaps = False
            for offset in range(0, duration, 20):
                t_min = total_minutes + offset
                hh, mm = divmod(t_min, 60)
                slot = f"{hh:02d}:{mm:02d}"
                if slot in unavailable:
                    overlaps = True
                    break

            if not overlaps:
                time_options.append(time_str)

        # Ενημέρωση του dropdown
        if self.appoint_date and self.service_dropdown:
            self.time_dropdown['state'] = 'readonly'
        else:
            self.time_dropdown['state'] = 'disabled'

        self.time_dropdown['values'] = time_options

        if not self.time_dropdown.get() in time_options: # Αν η επιλεγμένη ώρα δεν είναι μέσα στις διαθέσιμες
                        self.time_dropdown.set('') # άδειασε το time entry ώστε να ξαναεπιλέξει άλλη ώρα

        # print("διαθέσιμες επιλογές ώρας:", time_options)

    def hide_listbox_if_needed(self, event=None):
        # Έλεγχος αν το ποντίκι είναι πάνω από το listbox ή το entry
        mouse_over_listbox = (self.l1.winfo_containing(event.x_root, event.y_root) if event else False)
        mouse_over_entry = (self.search_client.winfo_containing(event.x_root, event.y_root) if event else False)
        # Αν δεν έχει focus ούτε το Entry ούτε το Listbox, απόκρυψε
        if not (self.search_client.focus_get() in [self.search_client, self.l1] or 
                mouse_over_listbox or 
                mouse_over_entry):
            self.l1.place_forget()
            self.scrollbar.place_forget() 
            self.close_btn.place_forget()
            self.newclient_btn.place_forget()

    def search_customer(self, *args):
        customer_list = self.show_all_customers()
        self.query = self.search_var.get().strip().lower()

        # Φιλτράρισμα
        filtered_customers = [
            customer for customer in customer_list
            if self.query in customer[1].lower() or self.query in customer[2]
        ]

        def my_upd(my_widget):
            my_w = my_widget.widget
            selection = my_w.curselection()
            if not selection:
                # Κενή επιλογή: το listbox απλώς έχασε το selection (exportselection),
                # π.χ. όταν επιλέγει ο χρήστης σε άλλο listbox/Entry. Δεν είναι επιλογή πελάτη.
                return
            index = int(selection[0])
            customer = filtered_customers[index]
            self.selected_id = customer[3] # είναι το customer_id που αντιστοιχεί στο συγκεκριμένο index της listbox
            value = my_w.get(index).strip()
            self.selected_name = value
            self.search_var.set(value)
            self.l1.place_forget()
            self.scrollbar.place_forget()
            self.close_btn.place_forget()
            self.newclient_btn.place_forget()
            self.focus_set()

        self.l1.delete(0, 'end')
        if not filtered_customers and len(self.query) >= 2:  # Μόνο αν έχει πληκτρολογήσει τουλάχιστον 2 χαρακτήρες
            self.l1.insert(tk.END, "   Ο πελάτης δε βρέθηκε...")
            self.l1.itemconfig(0, {'fg': 'black'})
            # Απενεργοποίηση αλληλεπίδρασης
            self.l1.bind("<Button-1>", lambda e: "break")  # Απενεργοποιεί αριστερό κλικ
            self.l1.bind("<Double-Button-1>", lambda e: "break")  # Απενεργοποιεί διπλό κλικ
            self.l1.bind("<Return>", lambda e: "break")  # Αν πατήσει Enter
        else:
            self.newclient_btn.place_forget()
            # Αν υπάρχουν πελάτες, επαναφέρουμε τα bindings
            self.l1.unbind("<Button-1>")
            self.l1.unbind("<Double-Button-1>")
            self.l1.unbind("<Return>")
            for customer in filtered_customers:
                full_name = f"{customer[0]} {customer[1]}"
                self.l1.insert(tk.END,f" {full_name}")
            self.l1.bind("<<ListboxSelect>>", my_upd)

        for row_index in range(len(filtered_customers)):
            bg = "#e3f2fd" if row_index % 2 == 0 else "#F5F2E9"
            self.l1.itemconfig(row_index,{'bg': bg})
            self.l1.itemconfig(row_index,{'bg': bg})

        self.l1.place(
                        x=self.search_client.winfo_x() - 80, 
                        y=self.search_client.winfo_y() + self.search_client.winfo_height() - 60,
                        width=215, height=241)
        
        self.close_btn.place(
                        relx=1.492, rely=-0.033,)
        
        self.scrollbar.place(
            x=10+548,
            y=self.search_client.winfo_y() + self.search_client.winfo_height() - 57,
            height=235
        )
        self.newclient_btn.place(
                        relx=0.064, rely=0.120,)
        self.l1.lift()
        self.scrollbar.lift()
        self.close_btn.lift()
        if "βρέθηκε" in self.l1.get(0):
            self.newclient_btn.lift()
        else:
            self.newclient_btn.place_forget()

    def create_new_client(self, event):
        
        widget = event.widget
        selection = widget.curselection()
        if selection and widget.get(selection[0]) == "   Ο πελάτης δε βρέθηκε...": # Έλεγχος αν επιλέχθηκε το self.l1.insert(tk.END, "   Ο πελάτης δε βρέθηκε...")
            self.show_new_client_popup()
        self.focus_set()

    def show_new_client_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Νέος Πελάτης")
        popup.geometry("600x400")
        popup.resizable(False, False)

        # Φόρτωση της σελίδας NewClientPage μέσα στο popup
        new_client_frame = NewClientPage(popup, self.controller)
        new_client_frame.pack(fill="both", expand=True)
        
        # Κεντράρισμα popup
        popup.update_idletasks()
        width = popup.winfo_width()
        height = popup.winfo_height()
        x = (popup.winfo_screenwidth() // 2) - (width // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")

        self.l1.place_forget()
        self.scrollbar.place_forget()
        self.close_btn.place_forget()
        self.newclient_btn.place_forget()

        if self.controller.favicon: # αν λείπει η εικόνα, το popup ανοίγει με το default εικονίδιο
            popup.iconphoto(False, self.controller.favicon) # favicon για popup, πρέπει να μπει κάτω από το κεντράρισμα αλλιώς βγάζει πρόβλημα
        
        self.current_popup = popup
        # Bind το κλείσιμο του popup
        popup.protocol("WM_DELETE_WINDOW", lambda: self.on_popup_close(popup))

        def force_focus(self, popup):
            try:
                popup.lift()
                popup.grab_set()
                popup.focus_force()
            except Exception as e:
                print("Force focus error:", e)

        self.after(500, lambda: force_focus(self, self.current_popup))

    def on_popup_close(self, popup=None):
         # Βρες όλα τα ανοιχτά Toplevel που ανήκουν σε αυτό το παράθυρο
        open_popups = [
            w for w in self.winfo_children() 
            if isinstance(w, tk.Toplevel) and w.winfo_exists()
        ]
        
        for popup in open_popups:
            popup.destroy()
        self.search_client.delete(0, tk.END)  # Καθαρισμός αναζήτησης
        self.search_client.insert(0, "🔍Επώνυμο & Τηλέφωνο")
        self.l1.place_forget()
        self.scrollbar.place_forget()
        self.close_btn.place_forget()
        self.newclient_btn.place_forget()
        self.focus_set()

    def save_appoint(self):
        """
        Save or Update ένα (καινούργιο) ραντεβού στη database.
        """

        # Το κείμενο του πεδίου πρέπει να αντιστοιχεί σε πραγματικό πελάτη:
        #  - είτε τον επέλεξε ο χρήστης από τη λίστα (selected_id/selected_name) και δεν
        #    πείραξε μετά το κείμενο,
        #  - είτε το πεδίο έμεινε ανέγγιχτο σε edit (loaded_customer_name), οπότε κρατάμε
        #    τον αρχικό πελάτη του ραντεβού (π.χ. αλλάζουμε μόνο ώρα/υπηρεσία).
        # Οτιδήποτε άλλο είναι ελεύθερο κείμενο και απορρίπτεται.
        typed_name = self.search_var.get().strip()

        if self.selected_id and typed_name == (self.selected_name or "").strip():
            selected_id = self.selected_id
        elif self.current_customer_id and typed_name == self.loaded_customer_name:
            selected_id = self.current_customer_id
        else:
            messagebox.showerror("Σφάλμα", "Διαλέξτε υπαρκτό πελάτη για το ραντεβού από τη λίστα")
            return

        appoint_date = self.appoint_date.get()
        # Το μετατρέπεις σε datetime object - το πεδίο μπορεί να είναι κενό ή άκυρο
        # (π.χ. καθαρίστηκε από τον έλεγχο κλειστής ημέρας στην get_time_options)
        try:
            date_obj = datetime.strptime(appoint_date, "%d-%m-%Y") # μετατροπή σε datetime object
        except ValueError:
            messagebox.showerror("Σφάλμα", "Επιλέξτε έγκυρη ημερομηνία για το ραντεβού.")
            return
        appoint_date = date_obj.date().isoformat() # μετατροπή σε isoformat string

        time_dropdown = self.time_dropdown.get()

        service_dropdown = self.service_dropdown.get()
        # duration_dropdown = self.duration_dropdown.get()
        if service_dropdown == "Κούρεμα":
            duration = 40
        elif service_dropdown == "Βάψιμο":
            duration = 60
        elif service_dropdown == "Χτένισμα":
            duration = 20
        else:
            messagebox.showerror("Σφάλμα", "Πρόβλημα με τη Διάρκεια του ραντεβού. Ξαναδιαλέξτε Είδος Υπηρεσίας.")
        notes = self.notes.get("1.0", tk.END).strip()
        if self.current_appointment_id:
            id = self.current_appointment_id
        else:
            id = None

        # Validate input fields
        selected_name = self.search_var.get().strip()

        if not selected_name or not appoint_date or not time_dropdown or not service_dropdown or not duration:
            messagebox.showerror("Σφάλμα", "Όλα τα πεδία (Πελάτης, Ημερομηνία, Είδος Υπηρεσίας και Ώρα) πρέπει να συμπληρωθούν")
            return
        
        try:
            # Create and save the appointment
            datetime_str = f"{appoint_date} {time_dropdown}"
            try:
                appointment = Appointment(selected_id, datetime_str, service_dropdown, duration, notes)
                appointment.save_to_db(id) # IF ALREADY EXISTS WE UPDATE
            except AppointmentOverlapError as e:
                messagebox.showerror("Σφάλμα", f"{e}\nΕπιλέξτε άλλη ώρα.")
                self.get_time_options() # ανανέωση των διαθέσιμων ωρών με βάση την τρέχουσα κατάσταση της βάσης
                return
            except Exception as e:
                messagebox.showerror("Σφάλμα", "Όλα τα πεδία πρέπει να συμπληρωθούν σωστά")
                print("Παρουσιάστηκε σφάλμα", f"{e}")
                return
            # Το μήνυμα δείχνει τον πελάτη που όντως γράφτηκε στη βάση, όχι ό,τι έτυχε
            # να υπάρχει στο πεδίο αναζήτησης.
            saved_customer_name = Customer.get_name_by_id(selected_id) or typed_name
            messagebox.showinfo("Επιτυχία", f"Αποθηκεύτηκε το ραντεβού για {saved_customer_name}")

            # Πηγαίνουμε στην DashboardPage και καλούμε την rebuild_calendar
            self.controller.get_frame("DashboardPage").on_minical_date_selected()
            self.controller.show_frame("DashboardPage")
        except Exception as e:
            print("Παρουσιάστηκε σφάλμα", f"Αποτυχία στην αποθήκευση του ραντεβού: {e}")
        
        self.editing = False

    # def show_edit_appointment_popup(self, customer_id, name, datetime_str, services, notes, id): # προσωρινά ανενεργό
    #     popup = tk.Toplevel(self)
    #     popup.title("Επεξεργασία ραντεβού")
    #     popup.geometry("800x550")
    #     popup.resizable(False, False)
    #     popup.grab_set()
    #     popup.focus_set()
        
    #     # Φόρτωση της σελίδας NewAppointPage μέσα στο popup
    #     new_client_frame = NewAppointPage(popup, self.controller)
    #     new_client_frame.pack(side="left", expand=False, fill="none")

    #     self.editing = True 
        
    #     self.current_customer_id = customer_id
    #     self.search_var.set(name)
    #     self.search_customer()
    #     # Διαχωρισμός ημερομηνίας και ώρας
    #     dt_str, time_str = datetime_str.split()
    #     print("dt_str",dt_str)
    #     yyyy, mm, dd = dt_str.split('-')
    #     dt_str = f"{dd}-{mm}-{yyyy}"
    #     # Μετατροπή string ημερομηνίας σε datetime αντικείμενο
    #     try:
    #         self.appoint_date.set_date(dt_str)
     
    #     except Exception as e:
    #         messagebox.showerror("Σφάλμα", f"Λάθος μορφή ημερομηνίας: {e}")
    #     self.service_dropdown.set(services)
    #     # self.duration_dropdown.set(duration)
    #     self.notes.delete("1.0", tk.END)  # Καθαρισμός του πεδίου
    #     self.notes.insert("1.7", notes)
    #     self.current_appointment_id = id
    #     self.get_time_options()
    #     self.controller.show_frame("DashboardPage")
    #     self.l1.place_forget()
    #     self.scrollbar.place_forget()
        
    #     # Κεντράρισμα popup
    #     popup.update_idletasks()
    #     width = popup.winfo_width()
    #     height = popup.winfo_height()
    #     x = (popup.winfo_screenwidth() // 2) - (width // 2)
    #     y = (popup.winfo_screenheight() // 2) - (height // 2)
    #     popup.geometry(f"{width}x{height}+{x}+{y}")

    #     self.current_popup = popup
    #     # Bind το κλείσιμο του popup
    #     popup.protocol("WM_DELETE_WINDOW", lambda: self.on_popup_close(popup))

    # def on_popup_close(self, popup=None):
    #      # Βρες όλα τα ανοιχτά Toplevel που ανήκουν σε αυτό το παράθυρο
    #     open_popups = [
    #         w for w in self.winfo_children() 
    #         if isinstance(w, tk.Toplevel) and w.winfo_exists()
    #     ]
        
    #     for popup in open_popups:
    #         popup.destroy()
    #     self.focus_set()

    def edit_appoint(self, customer_id, name, datetime_str, services, notes, id, popup):
        popup.destroy()
        self.editing = True
        # Καθαρισμός τυχόν προηγούμενης επιλογής: το selected_id πρέπει να σημαίνει
        # "ο πελάτης που επέλεξε ρητά ο χρήστης σε αυτή την επεξεργασία", ώστε να μη
        # μεταφέρεται μπαγιάτικη επιλογή από προηγούμενο ραντεβού.
        self.selected_id = None
        self.selected_name = ""
        self.loaded_customer_name = (name or "").strip() # ό,τι φορτώνουμε στο πεδίο = "ανέγγιχτο"
        self.current_customer_id = customer_id
        self.search_var.set(name)
        self.search_customer()
        # Διαχωρισμός ημερομηνίας και ώρας
        dt_str, time_str = datetime_str.split()

        yyyy, mm, dd = dt_str.split('-')
        dt_str = f"{dd}-{mm}-{yyyy}"

        try:
            self.appoint_date.set_date(dt_str)
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Λάθος μορφή ημερομηνίας: {e}")
        self.service_dropdown.set(services)
        
        # self.duration_dropdown.set(duration)
        self.notes.delete("1.0", tk.END)  # Καθαρισμός του πεδίου
        self.notes.insert("1.7", notes)
        self.current_appointment_id = id
        
        self.datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M") # Θέλουμε το χρονικό διάστημα του ραντεβού μας, να περιλαμβάνεται στα time_options
        self.get_time_options()
        if hasattr(self, 'time_dropdown'): # πρέπει να μπει μετά το self.get_time_options() γιατί εκεί υπάρχει self.time_dropdown.set("")
                hours, minutes = map(int, time_str.split(':'))
                self.time_dropdown.set(f"{hours:02d}:{minutes:02d}")
        self.controller.show_frame("NewAppointPage")
        self.l1.place_forget()
        self.scrollbar.place_forget()
        self.close_btn.place_forget()
        self.newclient_btn.place_forget()
        
    def create_new_appointment(self, date, time):
        
        self.editing = True
        self.appoint_date.set_date(date)
        self.time_dropdown.set(time)
        self.selected_name = ""
        self.selected_id = None
        self.current_customer_id = None
        self.current_appointment_id = None
        self.loaded_customer_name = ""
        self.search_var.set("🔍Επώνυμο & Τηλέφωνο")
        self.service_dropdown.set("")
        self.notes.delete("1.0", tk.END)  # Καθαρίζει το πεδίο σημειώσεων
        self.time_dropdown['state'] = 'disabled'
        self.controller.show_frame("NewAppointPage")
        self.focus_set()
        self.l1.place_forget()
        self.scrollbar.place_forget()
        self.close_btn.place_forget()
        self.newclient_btn.place_forget()


    def show_all_customers(self):
        try:
            customers_list = [(c.first_name, c.last_name, c.phone, c.id) for c in Customer.get_all()]
            return customers_list
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch customers: {e}")
            return []
        

    def on_show(self):
        """Καθαρίζει τα πεδία όταν ανοίγει η σελίδα."""
        if not self.editing and not self.onlyinit:
            self.selected_name = ""
            self.selected_id = None
            self.current_customer_id = None
            self.current_appointment_id = None
            self.loaded_customer_name = ""
            self.search_var.set("🔍Επώνυμο & Τηλέφωνο")
            self.appoint_date.set_date(datetime.today().date())  # Επαναφέρει τη σημερινή ημερομηνία
            self.time_dropdown.set("")  # Καθαρίζει την ώρα
            self.service_dropdown.set("")  # Καθαρίζει την υπηρεσία
            # self.duration_dropdown.set("")  # Καθαρίζει τη διάρκεια
            self.notes.delete("1.0", tk.END)  # Καθαρίζει το πεδίο σημειώσεων
            self.get_time_options()
            self.datetime_obj = None
            self.focus_set()  # Αφαιρεί focus από όποιο widget είχε focus
            self.l1.place_forget()
            self.close_btn.place_forget() 
            self.scrollbar.place_forget()
            self.newclient_btn.place_forget()
        self.editing = False
        self.onlyinit = False
   
        
class NewClientPage(tk.Frame):

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent_window = parent     # Για να κλείνουμε popups
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

        cancel_btn = ttk.Button(content, text="Ακύρωση", width=12, command=self.cancel_action).grid(row=6, column=0, pady=(50,0), sticky="e", padx=15)
        save_btn = ttk.Button(content, text="Αποθήκευση", width=12, style='Accent.TButton', command=self.save_customer).grid(row=6, column=1, pady=(50,0), sticky="w", padx=15)

    def cancel_action(self):

        current = self.controller.current_frame
        if current == self.controller.get_frame("DashboardPage"):
            has_popup = any(isinstance(w, tk.Toplevel) for w in self.controller.winfo_toplevel().winfo_children())
            if has_popup:
                self.controller.get_frame("DashboardPage").on_popup_close()
                return  # Μένεις στη Dashboard
        if current == self.controller.get_frame("NewAppointPage"):
            has_popup = any(isinstance(w, tk.Toplevel) for w in self.controller.winfo_toplevel().winfo_children())
            if has_popup:
                self.controller.get_frame("NewAppointPage").on_popup_close()
                return  # Μένεις στη Dashboard
        # Σε οποιαδήποτε άλλη περίπτωση ή αν δεν έχει popup:
        self.controller.show_frame("ClientsPage")

    def reset_fields(self):
        """Καθαρίζει τα πεδία για νέο πελάτη."""
        self.entry_name.delete(0, tk.END)
        self.entry_surname.delete(0, tk.END)
        self.entry_phone.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)

    def save_customer(self):
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
                customer = Customer(first_name, last_name, phone, email, id)
                customer.save_to_db(id) # IF ALREADY EXISTS WE UPDATE!
                messagebox.showinfo("Επιτυχία", f"Αποθηκεύτηκε: {customer.first_name} {customer.last_name}")

                # Καθάρισε τα πεδία
                self.reset_fields()

                # Καλεί την load_clients για να καθαρίσει το all clients table και να το ξαναγεμίσει περιέχοντας τον καινούργιο customer
                self.controller.get_frame("ClientsPage").load_clients()

                # Αν είμαστε μέσα σε popup, το κλείνουμε και μένουμε στη σελίδα που
                # ήμασταν (ίδιο μοτίβο με την cancel_action: η current_frame δείχνει
                # την υποκείμενη σελίδα και η on_popup_close κλείνει το Toplevel).
                for page_name in ("DashboardPage", "NewAppointPage"):
                    page = self.controller.frames.get(page_name)
                    if page is not None and self.controller.current_frame is page:
                        page.on_popup_close()
                        return
                # Αλλιώς (η σελίδα ανοίχτηκε κανονικά) πηγαίνουμε στην ClientsPage
                self.controller.show_frame("ClientsPage")
            except Exception as e:
                messagebox.showerror("Παρουσιάστηκε σφάλμα", f"Αποτυχία στην αποθήκευση του πελάτη: {e}")

    

    def edit_customer(self, first_name, last_name, phone, email, id):
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

        # Header Row
        headers = ["Ημερομηνία", "Ώρα", "Υπηρεσία"]
        header_row = tk.Frame(list_container, bg="#C2DFF7")
        header_row.pack(fill="x")

        for col, h in enumerate(headers):
            label = tk.Label(header_row, text=h, font=("Segoe UI", 10, "bold"),
                            fg="#242525", bg="#C2DFF7", anchor="w", padx=3, pady=5)
            label.grid(row=0, column=col, sticky="ew", padx=(20,0))
            header_row.grid_columnconfigure(col, weight=col+1)  # stretch equally

        # Canvas and Scrollbar
        canvas_frame = tk.Frame(list_container, highlightbackground="#A1A1A1", highlightthickness=1)
        canvas_frame.pack(fill="both", expand=True, pady=(0, 1))

        self.canvas = tk.Canvas(canvas_frame)
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y", pady=(4, 1), padx=0)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Scrollable Frame
        self.scrollable_frame = ttk.Frame(self.canvas)

        # This line ensures the inner frame will stretch horizontally
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=canvas_frame.winfo_width())
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", tags="frame")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfig("frame", width=event.width))

        # Mousewheel scrolling
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

    def show_appointments(self):

        self.items = []  # καθάρισε την παλιά λίστα (αν υπάρχει)
        today = datetime.today().date()

        # Καθαρισμός παλιών widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        for i in range(10 - len(self.appoints_list)):
            self.appoints_list.append(["", "", ""])
       
        # Εμφάνιση
        for row_index, appoint in enumerate(self.appoints_list):
            bg = "#e3f2fd" if row_index % 2 == 0 else "#F5F2E9"
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

    def customer_info(self, first_name, last_name, phone, email, id):

        full_name = f"{first_name} {last_name}"
        self.client_name.config(text=full_name)
        self.contact_phone.config(text=phone)
        self.contact_email.config(text=email)
        
        self.appoints_list = self.get_appoints_from_id(id)
        self.show_appointments()
        self.controller.show_frame("ShowClientPage")

    def highlight_target_row(self):
        if self.target_index is None:
            return

        for widget in self.scrollable_frame.winfo_children():
            info = widget.grid_info()
            if int(info["row"]) == self.target_index:
                widget.configure(bg="#0560b6", fg="white")  # highlight τη γραμμή

    def get_appoints_from_id(self, customer_id):
        try:
            appoints_list = [(a.datetime, a.services) for a in Appointment.get_by_customer_id(customer_id)]

            new_appoints_list = []

            for date_str, service in appoints_list:
                dt_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                date_part = dt_obj.strftime("%d-%m-%Y")
                time_part = dt_obj.strftime("%H:%M")
                new_appoints_list.append((date_part, time_part, service))

            appoints_list = new_appoints_list

            return appoints_list      
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch customers: {e}")
            return []

            
class RemindersPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.selected_day = None

        content = ttk.Frame(self, border=1, borderwidth=1, relief="sunken")
        content.pack(fill="both", expand=True, padx=(120,120), pady=20, anchor="center")

        # Date Picke
        self.top_bar = tk.Frame(content, bg="#C2DFF7")
        self.top_bar.pack(fill="x", ipadx=10, ipady=(2))

        self.date_entry = DateEntry(self.top_bar, date_pattern='dd-mm-yyyy', selectbackground="#505E66", background="#505E66", headersbackground="#f1ede0", headersforeground="#505E66", showweeknumbers=False, showothermonthdays=False, font=('Segoe UI Variable Text Semiligh', 10),
                               bordercolor="#FDFDFD", weekendbackground="#FDFDFD", normalbackground="#FDFDFD" )
        self.date_entry.pack(side="right", padx=(10,40), pady=(2,1))
        ttk.Label(self.top_bar, text="Όλα τα ραντεβού για:", background="#C2DFF7").pack(side="right", pady=(2,1))

        canvas_frame = tk.Frame(content, highlightbackground="gray", highlightthickness=1, background="#fdfdfd")
        canvas_frame.pack(fill="both", expand=True, pady=(0, 1))

        canvas = tk.Canvas(canvas_frame)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y", pady=(4,1))
        canvas.configure(yscrollcommand=scrollbar.set)

        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.scrollable_frame.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.scrollable_frame.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        self.date_entry.bind("<<DateEntrySelected>>", self.load_appoinments)
        
        self.load_appoinments()

        new_cli_btn = ttk.Button(self, text="Αποστολή Email", style='Accent.TButton', padding=(6,6), width=15, command=self.send_reminders)
        new_cli_btn.pack(padx=(300,0), pady=(10,20), side="left")
        new_cli_btn2 = ttk.Button(self, text="Εκτύπωση σε Excel", style='Accent.TButton', padding=(6,6), width=15, command=self.export_to_excel)
        new_cli_btn2.pack(padx=(0,300), pady=(10,20), side="right")

    def load_appoinments(self, event=None):
        # 1. Καθάρισε όλα τα προηγούμενα rows
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        appoints_by_date = self.get_appointments_by_date()

        if appoints_by_date:     
            if ((len(appoints_by_date)-10) < 10):
                for i in range((12-len(appoints_by_date))):
                    appoints_by_date.append(("","","","", "", "", ""))

            for i, appoint in enumerate(appoints_by_date):
                bg = "#e3f2fd" if i % 2 == 0 else "#F5F2E9"
                # Δημιουργία χρονικού διαστήματος
                time_range = ""

                if appoint[1] and appoint[3]:
                    dt_obj = datetime.strptime(appoint[1], "%Y-%m-%d %H:%M")
                    time_part = dt_obj.strftime("%H:%M")
                    start_time = datetime.strptime(time_part, "%H:%M")
                    end_time = start_time + timedelta(minutes=int(appoint[3]))
                    time_range = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"

                # Δημιουργία Frame για κάθε γραμμή
                row_frame = ttk.Frame(self.scrollable_frame)
                row_frame.pack(fill="x", pady=1)

                # Στήλη 1: Χρονικό διάστημα
                ttk.Label(
                    row_frame,
                    text=time_range,
                    background=bg,
                    width=14,
                    anchor="w",
                    padding=(12, 7)
                ).pack(side="left")

                # Στήλη 2: Όνομα πελάτη
                customer_name = Customer.get_name_by_id(appoint[0]) if appoint[0] else ""
                ttk.Label(
                    row_frame,
                    text=customer_name,
                    background=bg,
                    width=26,
                    anchor="w",
                    padding=(0, 7)
                ).pack(side="left", ipadx=7)

                # Στήλη 3: Υπηρεσία
                service = str(appoint[2]) if appoint[2] else ""
                ttk.Label(
                    row_frame,
                    text=service,
                    background=bg,
                    width=12,
                    anchor="w",
                    padding=(0, 7)
                ).pack(side="left", ipadx=(10))

                # Στήλη 4: Σημειώσεις
                notes = str(appoint[4]) if appoint[4] else ""
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

    def get_appointments_by_date(self):

        if self.date_entry.get():
            date = self.date_entry.get()
            date_obj = datetime.strptime(date, "%d-%m-%Y")
            date_str = date_obj.isoformat()
        else:
            date = datetime.today().date()
            date_obj = datetime.strftime(date, "%d-%m-%Y")
            date_str = date_obj.isoformat()
        
        try:
            appointments = [(a.customer_id, a.datetime, a.services, a.duration, a.notes, a.id) for a in Appointment.get_by_date(date_str)]
            return appointments
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch appointments: {e}")
            return []

### Κώδικας Σοφοκλή
    def send_reminders(self):
        """Αποστολή email υπενθυμίσεων"""
        if self.date_entry.get():
            date = self.date_entry.get()
            date_obj = datetime.strptime(date, "%d-%m-%Y")
            date_str = date_obj.isoformat()
        else:
            date_obj = datetime.today().date()
            date_str = date_obj.isoformat()
        # Διάλογος για στοιχεία email
        dialog = EmailConfigDialog(self)
        self.wait_window(dialog)

        if hasattr(dialog, 'email_config'):
            config = dialog.email_config
            sender = EmailSender(
                smtp_server=config['server'],
                smtp_port=config['port'],
                email=config['email'],
                password=config['password']
            )

            success_count, message = sender.send_reminders_for_date(date_str)
            messagebox.showinfo("Αποτέλεσμα", message)

### Κώδικας Σοφοκλή
    def export_to_excel(self):
        # import datetime
        """Εξαγωγή σε Excel"""
        try:
            # Λήψη ημερομηνίας από το πεδίο εισαγωγής ή χρήση σημερινής
            if self.date_entry.get():
                date_str = self.date_entry.get()  # Μορφή "DD-MM-YYYY"
                print("Επιλεγμένη ημερομηνία:", date_str)
                
                # Μετατροπή string σε ημερομηνία
                date_obj = datetime.strptime(date_str, "%d-%m-%Y").date()
                date_str = date_obj.strftime("%d-%m-%Y")  # Μετατροπή πίσω σε string για συνέπεια
            else:
                date_obj = datetime.today().date()
                date_str = date_obj.strftime("%d-%m-%Y")
                print("Χρήση σημερινής ημερομηνίας:", date_str)
            
            # Εξαγωγή σε Excel
            filepath = export_excel.export_appointments_to_excel(date_str)
            messagebox.showinfo("Επιτυχία", f"Το αρχείο δημιουργήθηκε:\n{filepath}")
            
        except ValueError as e:
            messagebox.showerror("Σφάλμα", f"Λάθος μορφή ημερομηνίας. Χρησιμοποιήστε ΗΗ-ΜΜ-ΕΕΕΕ\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Σφάλμα!", f"Αποτυχία εξαγωγής...: {str(e)}")

    def on_show(self):
        self.date_entry.set_date(datetime.today().date())
        self.load_appoinments()
        self.date_entry.bind("<<DateEntrySelected>>", self.load_appoinments)

### Κώδικας Σοφοκλή
class EmailConfigDialog(tk.Toplevel):
    """Διάλογος για ρύθμιση email"""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Ρυθμίσεις Email")
        self.geometry("400x300")
        self.resizable(False, False)

        # Center the dialog
        self.transient(parent)
        self.grab_set()

        # Frame
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        # Fields
        ttk.Label(frame, text="SMTP Server:").grid(row=0, column=0, sticky="w", pady=5)
        self.server_entry = ttk.Entry(frame, width=30)
        self.server_entry.insert(0, "smtp.gmail.com")
        self.server_entry.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Port:").grid(row=1, column=0, sticky="w", pady=5)
        self.port_entry = ttk.Entry(frame, width=30)
        self.port_entry.insert(0, "587")
        self.port_entry.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Email:").grid(row=2, column=0, sticky="w", pady=5)
        self.email_entry = ttk.Entry(frame, width=30)
        self.email_entry.grid(row=2, column=1, pady=5)

        ttk.Label(frame, text="Password:").grid(row=3, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(frame, width=30, show="*")
        self.password_entry.grid(row=3, column=1, pady=5)

        # Info label
        info_text = "Για Gmail: Χρησιμοποιήστε App Password,\nόχι το κανονικό password του λογαριασμού σας."
        ttk.Label(frame, text=info_text, foreground="gray").grid(row=4, column=0, columnspan=2, pady=10)

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Δοκιμή Σύνδεσης",
                  command=self.test_connection).pack(side="left", padx=5)
        ttk.Button(button_frame, text="OK", style='Accent.TButton',
                  command=self.save_config).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Άκυρο",
                  command=self.destroy).pack(side="left", padx=5)

    def test_connection(self):
        """Δοκιμή σύνδεσης"""
        from emails_utils import test_email_connection

        success, message = test_email_connection(
            self.server_entry.get(),
            int(self.port_entry.get()),
            self.email_entry.get(),
            self.password_entry.get()
        )

        if success:
            messagebox.showinfo("Επιτυχία", message)
        else:
            messagebox.showerror("Σφάλμα", message)

    def save_config(self):
        """Αποθήκευση ρυθμίσεων"""
        self.email_config = {
            'server': self.server_entry.get(),
            'port': int(self.port_entry.get()),
            'email': self.email_entry.get(),
            'password': self.password_entry.get()
        }
        self.destroy()
        

if __name__ == "__main__":
    print("⚠️  Μην εκτελείς απευθείας αυτό το αρχείο. Χρησιμοποίησε το main.py")
    