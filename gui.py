# pip install tkcalendar xlsxwriter smtplib pillow sv-ttk tkinter-tooltip
import threading
import tkinter as tk
from tkinter import messagebox, ttk
# from tkinter import font as tkFont
import models_revised
from models_revised import Customer, Appointment
from tkcalendar import DateEntry
from tkcalendar import Calendar
from datetime import datetime, timedelta
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
        if hasattr(self.current_frame, "on_show"):
            self.current_frame.on_show()

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

        
class CalendarView(tk.Frame):
    def __init__(self, parent, days=3):
        super().__init__(parent, bg="#f8fafd")

        self.days = days
        self.hours = [f"{h:02}:00" for h in range(10, 20)]  # 10:00 - 20:00
        self.rows = len(self.hours)
        self.cols = self.days
        
        self.build_grid()

    def build_grid(self):
        today = datetime.today()

        # --- Top row: Dates ---
        tk.Label(self, text="", bg="#f8fafd", font=('Segoe UI', 10)).grid(row=0, column=0)
        for i in range(self.days):
            day = today + timedelta(days=i)
            lbl_month = tk.Label(self,text=day.strftime("%b"), font=('Segoe UI Variable Display', 15, "bold"), bg="#f8fafd", fg="#1F1F1F", padx=9)
            lbl = tk.Label(self, text=day.strftime("%a %d"), font=('Segoe UI Semibold', 12), bg="#f8fafd", fg="#1F1F1F", pady=0)
            lbl_month.grid(row=0, column=0, sticky="nw", columnspan=2, pady=(0,3))
            lbl.grid(row=0, column=i+1, sticky="nsew")

        # --- Rows: Hours ---
        for i, hour in enumerate(self.hours):
            tk.Label(self, text=hour, bg="#f8fafd", width=5, font=('Segoe UI', 10), fg="#444746").grid(row=i+1, column=0, sticky="w", padx=(7,0))
            
            for j in range(self.days):
                cell = tk.Frame(self, width=200, height=49, bg="white")
                cell.grid(row=i+1, column=j+1, sticky="nsew")
                cell.grid_propagate(False)

                inner = tk.Frame(cell, bg="white")
                inner.place(relx=0, rely=0, relwidth=1, relheight=1)

                # Add bottom border unless it's the last row
                if i != self.rows - 1:
                    tk.Frame(inner, bg="#dde3ea", height=1).pack(side="bottom", fill="x")

                # Add right border unless it's the last column
                if j != self.cols - 1:
                    tk.Frame(inner, bg="#dde3ea", width=1).pack(side="right", fill="y")

                # example placeholder appointment at 12:00 today
                if self.hours[i] == "12:00" and j == 0:
                    appt = tk.Label(cell, text="Μαρία Αντωνιάδου (Κ)", bg="#F5F2E9", fg="black", relief="flat", height=0, pady=0, font=('Segoe UI', 9), padx=3, anchor="w")
                    appt.pack(fill="x", padx=(0,1), pady=(0,1), side="bottom")
                if self.hours[i] == "12:00" and j == 0:
                    appt = tk.Label(cell, text="Αντουάν Μπισμπίκης (Χ)", bg="#F5F2E9", fg="black", relief="flat", height=0, pady=0, font=('Segoe UI', 9), padx=3, anchor="w")
                    appt.pack(fill="x", padx=(0,1), pady=0, side="top")
                if self.hours[i] == "12:00" and j == 0:
                    appt = tk.Label(cell, text="Γιώργος Τσανακλάκης (Λ)", bg="#e3f2fd", fg="black", relief="flat", height=0, pady=0, font=('Segoe UI', 9), padx=3, anchor="w")
                    appt.pack(fill="x", padx=(0,1), pady=1)
                if self.hours[i] == "14:00" and j == 2:
                    appt = tk.Label(cell, text="Αντουάν Μπισμπίκης (Β)", bg="#e3f2fd", fg="black", relief="flat", height=0, pady=0, font=('Segoe UI', 9), padx=3, anchor="w")
                    appt.pack(fill="both", padx=(0,1), pady=(0,1), expand=1)
                if self.hours[i] == "19:00" and j == 1:
                    appt = tk.Label(cell, text="Μαρία Αντωνιάδου (Κ)", bg="#F5F2E9", fg="black", relief="flat", height=2, pady=0, padx=3, anchor="w", font=('Segoe UI', 9))
                    appt.pack(fill="x", padx=(0,1), pady=0, side="bottom")

        for col in range(self.cols + 1):
            self.grid_columnconfigure(col, weight=1)

        for row in range(self.rows + 1):
            self.grid_rowconfigure(row, weight=1)
        
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
        search_client.insert(0, "🔍 Αναζήτηση...")
        search_client.bind("<FocusIn>", lambda args: search_client.delete('0', 'end'))
        search_client.bind("<FocusOut>", lambda args: search_client.insert(0, "🔍 Αναζήτηση..."))
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
            command=lambda: controller.show_frame("NewAppointPage")
        )
        
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
            command=lambda: controller.show_frame("RemindersPage")
        )
        
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
        calendar.pack(side="left", fill="both", expand=True, padx=7, pady=(0,15))

class ClientsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

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
                                                    controller.get_frame("NewClientPage").reset_fields(),
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

        self.load_clients()

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
                tk.Button(row, text="🔍", font=(18), fg="#242525", background=bg,  command=lambda: self.controller.show_frame("ShowClientPage"), width=3, relief="flat").pack(side="right", padx=2)
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
                tk.Button(row, text="🔍", font=(18), fg="#242525", background=bg,  command=lambda: self.controller.show_frame("ShowClientPage"), width=3, relief="flat").pack(side="right", padx=2)
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
        sv_ttk.set_theme("light")
        self.focus_set()  # Αφαιρεί το focus από το entry
        self.search_var.set("   Αναζήτηση με όνομα ή τηλέφωνο...")
        self.load_clients()

class NewAppointPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        content = ttk.Frame(self, padding=(40,25), border=5, borderwidth=3)
        content.pack(expand=1, ipady=10)

        ttk.Label(content, text="Πελάτης:", anchor="w", width=20).grid(row=0, column=0, sticky="w", pady=10)

        all_clients = self.show_all_customers()
  
        self.client_map = {f"{c[0]} {c[1]}": c[4] for c in all_clients}
        client_names = list(self.client_map.keys())

        
        client_var = tk.StringVar(content)
        
        self.selected_name = ttk.Combobox(content, textvariable=client_var, values=client_names, state="readonly", width=16)
        self.selected_name.grid(row=0, column=1, sticky="w", pady=10)

        print(self.selected_name.get())

        ttk.Label(content, text="Ημερομηνία:", anchor="w", width=20).grid(row=1, column=0,sticky="w", pady=10)
        self.appoint_date = DateEntry(content, date_pattern='dd-mm-yyyy', width=16)
        self.appoint_date.grid(row=1, column=1, sticky="w", pady=10)
        
        ttk.Label(content, text="Ώρα:", anchor="w", width=20).grid(row=2, column=0, sticky="w", pady=10)
        time_options = [f"{h:02d}:{m:02d}" for h in range(10, 20) for m in range(0, 60, 20)]
        time_var = tk.StringVar(content)
        self.time_dropdown = ttk.Combobox(content, textvariable=time_var, values=time_options, state="readonly", width=16)
        self.time_dropdown.grid(row=2, column=1, sticky="w", pady=10)
        
        ttk.Label(content, text="Διάρκεια:", anchor="w", width=20).grid(row=3, column=0, sticky="w", pady=10)
        duration_var = tk.StringVar(content, value="20")
        self.duration_dropdown = ttk.Combobox(content, textvariable=duration_var, values=["20","40","60"], state="readonly", width=16)
        self.duration_dropdown.grid(row=3, column=1, sticky="w", pady=10)
        
        ttk.Label(content, text="Είδος υπηρεσίας:", anchor="w", width=20).grid(row=4, column=0, sticky="w", pady=10) # multiple options? Checkbox?
        service_var = tk.StringVar(content, value="Κούρεμα")
        self.service_dropdown = ttk.Combobox(content, textvariable=service_var, values=["Κούρεμα","Βάψιμο","Χτένισμα"], state="readonly", width=16)
        self.service_dropdown.grid(row=4, column=1, sticky="w", pady=10)
        
        ttk.Label(content, text="Σημειώσεις:", anchor="w", width=20,).grid(row=5, column=0, sticky="w", pady=(10,10))
        self.notes = tk.Entry(content, bg="#fdfdfd", highlightbackground="white")
        self.notes.grid(row=6, column=0, columnspan=2, padx=0, ipady=35, ipadx=108, sticky="nw")

        save_btn = ttk.Button(content, text="Αποθήκευση", width=12, underline=1, style='Accent.TButton', command=self.save_appoint).grid(row=7, column=1, pady=(40,15), sticky="w", padx=0)
        cancel_btn = ttk.Button(content, text="Ακύρωση", width=12, underline=1).grid(row=7, column=0, pady=(40,15), sticky="e", padx=15)


    def reset_fields(self):
        """Καθαρίζει τα πεδία για νέο ραντεβού."""
        self.selected_name.delete(0, tk.END)
        self.appoint_date.delete(0, tk.END)
        self.time_dropdown.delete(0, tk.END)
        self.service_dropdown.delete(0, tk.END)
        self.duration_dropdown.delete(0, tk.END)
        self.notes.delete(0, tk.END)

    def save_appoint(self):
        print(self.selected_name.get())
        """
        Create, Save or Update a (new) appointment to the database.
        """
        selected_name = self.selected_name.get()  # ΠΑΡΕ το string όνομα από το Combobox
        selected_id = self.client_map.get(selected_name)
        appoint_date = self.appoint_date.get()
        time_dropdown = self.time_dropdown.get()
        service_dropdown = self.service_dropdown.get()
        duration_dropdown = self.duration_dropdown.get()
        notes = self.notes.get()

        print(selected_id, appoint_date, time_dropdown, service_dropdown, duration_dropdown, notes)

        # Validate input fields
        if not self.selected_name or not appoint_date or not time_dropdown or not time_dropdown or not service_dropdown or not duration_dropdown.strip():
            messagebox.showerror("Σφάλμα", "Όλα τα πεδία (Πελάτης, Ημερομηνία, Ώρα, Διάρκεια και Είδος Υπηρεσίας) πρέπει να συμπληρωθούν")
            return

        try:
            # Create and save the appointment
            appointment = Appointment(selected_id, appoint_date, time_dropdown, service_dropdown, duration_dropdown, notes)
            appointment.save_to_db() # IF ALREADY EXISTS WE SHOULD UPDATE
            messagebox.showinfo("Επιτυχία", f"Αποθηκεύτηκε το ραντεβού για {selected_name}")

            # Clear input fields
            self.reset_fields()

            # Πηγαίνουμε στην ClientsPage
            self.controller.show_frame("DashboardPage")
        except Exception as e:
            messagebox.showerror("Παρουσιάστηκε σφάλμα", f"Αποτυχία στην αποθήκευση του ραντεβού: {e}")



    def show_all_customers(self):
        """
        Display all appointments with patient details (name, surname, phone) in a message box.
        """
        try:
            # all_customers = Customer.get_all()
            customers_list = [(c.first_name, c.last_name, c.phone, c.email, c.id) for c in Customer.get_all()]
            return customers_list
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch customers: {e}")
            return [] 
        
class NewClientPage(tk.Frame):

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

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
            Save a new patient to the database.
            """
            first_name = self.entry_name.get()
            last_name = self.entry_surname.get()
            phone = self.entry_phone.get()
            email = self.entry_email.get()
            id = self.id

            # Validate input fields
            if not first_name.strip() or not last_name.strip() or not phone.strip() or not email.strip():
                messagebox.showerror("Σφάλμα", "Όλα τα πεδία (όνομα, επώνυμο, τηλέφωνο, email) πρέπει να συμπληρωθούν")
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
            print(first_name, last_name, phone, email, id)
            """
            Επεξεργασία πελάτη και update database
            """
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

class ShowClientPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        content = ttk.Frame(self)
        content.pack(fill="both", expand=True, padx=(150,150), pady=10, anchor="center")

        name_contact = tk.Frame(content).pack()

        client = ttk.Label(content, text="Μαρία Αντωνιάδου", font=('Segoe UI Variable Display Semib', 20), foreground="#1F1F1F")
        # client.grid(row=0, column=0, sticky="NW", pady=(20,0), padx=45)
        client.pack(pady=(0,0), padx=2, anchor="nw")
        
        contact_phone = ttk.Label(content, text='6947000000', font=('Segoe UI Variable Display', 10), foreground="#1F1F1F")
        # contact_phone.grid(row=1, column=0, sticky="NW", pady=3, padx=47)
        contact_phone.pack(pady=3, padx=3, anchor="nw")
        contact_email = ttk.Label(content, text="pentagiotissa@gmail.com", font=('Segoe UI Variable Display', 10), foreground="#1F1F1F")
        # contact_email.grid(row=2, column=0, sticky="NW", padx=47, pady=(0,15))
        contact_email.pack(padx=4, pady=(0,22), anchor="nw")

        list_container = ttk.Frame(content, border=1, borderwidth=1, relief="sunken")
        list_container.pack(fill="both", expand=True, padx=(0), pady=(0,5), anchor="center")

        # === Header Row ===
        headers = ["Ημερομηνία", "Ώρα", "Υπηρεσία"]
        header_row = tk.Frame(list_container, bg="#C2DFF7")
        for h in headers:
            label = tk.Label(header_row, text=h, font=("Segoe UI", 10, "bold"), fg="#242525", bg="#C2DFF7", width=22, anchor="w")
            label.pack(side="left",pady=(2,1), anchor="w", padx=(18,0))
        header_row.pack(fill="x", ipady=(2))


        # === Canvas and Scrollbar ===
        canvas_frame = tk.Frame(list_container, highlightbackground="#A1A1A1", highlightthickness=1)
        canvas_frame.pack(fill="both", expand=True, pady=(0, 1))

        canvas = tk.Canvas(canvas_frame)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y", pady=(4,1))
        canvas.configure(yscrollcommand=scrollbar.set)

        # === Scrollable Frame ===
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # === Mousewheel scrolling ===
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        scrollable_frame.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        scrollable_frame.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        clients = [
            ("12/5/2025", "12:00", "Κούρεμα"),
            ("14/5/2025", "15:00", "Βάψιμο"),
            ("26/5/2025", "18:20", "Χτένισμα")
        ] * 5

        for index, client in enumerate(clients):
            bg = "#e3f2fd" if index % 2 == 0 else "#F5F2E9"
            row = tk.Frame(scrollable_frame, background=bg, padx=4, pady=1)
            for i in range(3):
                tk.Label(row, text=client[i], font=("Segoe UI", 10), width=25, anchor="w", background=bg).pack(anchor="w", pady=0, padx=(14,2), side="left")

            
            

            row.pack(fill="x", pady=1)

        # columns = ("Ημερομηνία", "Ώρα", "Υπηρεσία")

        # ##  Function to sort the Treeview by column
        # # def sort_treeview(tree, col, descending):
        # #     data = [(tree.set(item, col), item) for item in tree.get_children('')]
        # #     data.sort(reverse=descending)
        # #     for index, (val, item) in enumerate(data):
        # #         tree.move(item, '', index)
        # #     tree.heading(col, command=lambda: sort_treeview(tree, col, not descending))

        
        # self.client_tree = ttk.Treeview(content, columns=columns, show="headings", height=15)
        # self.client_tree.column(0,anchor="center")
        # self.client_tree.column(1,anchor="center")
        # self.client_tree.column(2,anchor="center")
        # self.client_tree.heading("Ημερομηνία", text="Ημερομηνία")
        # self.client_tree.heading("Ώρα", text="Ώρα")
        # self.client_tree.heading("Υπηρεσία", text="Υπηρεσία")
        # self.client_tree.grid(row=3, column=0, sticky="NSEW", pady=3)
        # ## Configure column headings and sorting functionality
        # # for col in columns:
        # #     client_tree.heading(col, text=col, command=lambda c=col: sort_treeview(client_tree, c, False))
        # #     client_tree.column(col)
        # # mylist = []
        # # for i in range(20,0,-1):
        #     # client_tree.insert('', 'end', values=(f'{i}/1/2025','12:00', 'Κούρεμα'))
        # #     mylist.append(f'{i}/1/2025')
        
        # # mylist.sort(key=lambda x: datetime.strptime(x, '%d/%m/%Y'))
        # # for i in range(0,20,1):
        # #     self.client_tree.insert('', 'end', values=(mylist[i],'12:00', 'Κούρεμα'))
        # # print(mylist)

        # vsb = ttk.Scrollbar(content, orient="vertical", command=self.client_tree.yview)
        # vsb.grid(row=3, column=1, sticky="nse", pady=(25,0))

    #     self.client_tree.configure(yscrollcommand=vsb.set)

    #     self.items = []  # list of tuples: (date_obj, item_id)
    #     today = datetime.now().date()

    #     # Δημιουργούμε ημερομηνίες 1-30 Μαΐου 2025
    #     mylist = [f'{i}/5/2025' for i in range(1, 30)]
    #     mylist.sort(key=lambda x: datetime.strptime(x, '%d/%m/%Y'))

    #     for date_str in mylist:
    #         date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
    #         item = self.client_tree.insert('', 'end', values=(date_str, '12:00', 'Κούρεμα'))
    #         self.items.append((date_obj, item))

    #     # βρες την κατάλληλη ημερομηνία
    #     self.target_item = self.find_best_matching_item(today)
    #     self.after(100, self.scroll_to_target)


        ttk.Button(content, text="⬅️ Επιστοφή στη Διαχείριση Πελατών", command=lambda: controller.show_frame("ClientsPage")).pack(anchor="s", pady=(15,10)) # .grid(row=4, column=0, sticky="S", pady=(15,10))

    # def find_best_matching_item(self, today):
    #     future_dates = sorted([d for d in self.items if d[0] >= today], key=lambda x: x[0])
    #     if future_dates:
    #         return future_dates[0][1]  # επιστρέφει το item_id της πιο κοντινής μελλοντικής

    #     # αλλιώς πάρε την τελευταία διαθέσιμη (πιο κοντινή παρελθοντική)
    #     past_dates = sorted([d for d in self.items if d[0] < today], key=lambda x: x[0], reverse=True)
    #     if past_dates:
    #         return past_dates[0][1]

    #     return None  # τίποτα δεν υπάρχει

    # def scroll_to_target(self):
    #     if self.target_item:
    #         self.client_tree.selection_set(self.target_item)
    #         self.client_tree.focus(self.target_item)
    #         self.client_tree.see(self.target_item)

    #         # Κάνει την ημερομηνία να εμφανίζεται **στην κορυφή**
    #         index = self.client_tree.index(self.target_item)
    #         if index > 0:
    #             above_item = self.client_tree.get_children()[max(0, index - 1)]
    #             self.client_tree.see(above_item)
class RemindersPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # === Content Frame ===
        content = ttk.Frame(self, border=1, borderwidth=1, relief="sunken")
        content.pack(fill="both", expand=True, padx=(120,120), pady=20, anchor="center")

        # === Date Picker ===
        top_bar = tk.Frame(content, bg="#C2DFF7")
        top_bar.pack(fill="x", ipadx=10, ipady=(2))

        self.get_all()
        self.date_entry = DateEntry(top_bar, date_pattern='dd-mm-yyyy', selectbackground="#A1795A", background="#A1795A", headersbackground="#f1ede0", headersforeground="#3F3F3F", showweeknumbers=False, showothermonthdays=False, font=('Segoe UI Variable Text Semiligh', 10),
                               bordercolor="#FDFDFD", weekendbackground="#FDFDFD", normalbackground="#FDFDFD" )
        self.date_entry.pack(side="right", padx=(10,40), pady=(2,1))
        ttk.Label(top_bar, text="Όλα τα ραντεβού για:", background="#C2DFF7").pack(side="right", pady=(2,1))
 
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

        # ttk.Separator(scrollable_frame).pack(anchor="w", pady=1)
        self.date_entry.bind("<<DateEntrySelected>>", self.load_appoinments)
        appoints_by_date = self.get_appointments_by_date()

        if appoints_by_date:     
            if ((len(appoints_by_date)-10) < 10):
                for i in range((12-len(appoints_by_date))):
                    appoints_by_date.append(("","","","", "", "", ""))
                # === Example appointments ===
                for i, appoint in enumerate(appoints_by_date):
                    bg = "#e3f2fd" if i % 2 == 0 else "#F5F2E9"
                    if appoint[2] and appoint[4]:
                        start_time_str = appoint[2]
                        duration_min = int(appoint[4]) 

                        # Μετατροπή ώρας έναρξης σε datetime αντικείμενο
                        start_time = datetime.strptime(start_time_str, "%H:%M")
                        end_time = start_time + timedelta(minutes=duration_min)

                        # Format τελικού string
                        time_range = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
                    else:
                        time_range = ""
                    ttk.Label(
                        self.scrollable_frame,
                        text=f"{time_range:30s}{Customer.get_name_by_id(appoint[0]):40s}{appoint[3]:30s}{appoint[5]:20s}",
                        background=bg,
                        padding=(15,7),
                        width=94
                    ).pack(anchor="w", pady=1, padx=0)
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
                                padding=(15,7),
                                width=94
                                ).pack(anchor="w", pady=1, padx=0)
                    else:
                        ttk.Label(
                                self.scrollable_frame,
                                text="",
                                background=bg,
                                padding=(15,7),
                                width=94
                                ).pack(anchor="w", pady=1, padx=0)


        new_cli_btn = ttk.Button(self, text="Αποστολή Email", style='Accent.TButton', padding=(6,6), width=15)
        new_cli_btn.pack(padx=(300,0), pady=(10,20), side="left")
        new_cli_btn2 = ttk.Button(self, text="Εκτύπωση σε Excel", style='Accent.TButton', padding=(6,6), width=15)
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
            # === Example appointments ===
            for i, appoint in enumerate(appoints_by_date):
                bg = "#e3f2fd" if i % 2 == 0 else "#F5F2E9"
                if appoint[2] and appoint[4]:
                    start_time_str = appoint[2]
                    duration_min = int(appoint[4]) 

                    # Μετατροπή ώρας έναρξης σε datetime αντικείμενο
                    start_time = datetime.strptime(start_time_str, "%H:%M")
                    end_time = start_time + timedelta(minutes=duration_min)

                    # Format τελικού string
                    time_range = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
                else:
                    time_range = ""
                ttk.Label(
                    self.scrollable_frame,
                    text=f"{time_range:30s}{Customer.get_name_by_id(appoint[0]):40s}{appoint[3]:30s}{appoint[5]:20s}",
                    background=bg,
                    padding=(15,7),
                    width=94
                            ).pack(anchor="w", pady=1, padx=0)
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
                                padding=(15,7),
                                width=94
                                ).pack(anchor="w", pady=1, padx=0)
                    else:
                        ttk.Label(
                                self.scrollable_frame,
                                text="",
                                background=bg,
                                padding=(15,7),
                                width=94
                                ).pack(anchor="w", pady=1, padx=0)

    def get_appointments_by_date(self):

        date = self.date_entry.get()  # Get the date from an input field
        try:
            appointments = [(a.customer_id, a.date, a.time, a.services, a.duration, a.notes, a.id) for a in Appointment.get_by_date(date)]
            print("appointments by date", date, appointments)

            return appointments
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch appointments: {e}")
            return []
        
    def get_all(self):
        try:
            appointments = [(a.customer_id, a.date, a.time, a.services, a.duration, a.notes, a.id) for a in Appointment.get_all()]
            print("all appointments", appointments)
            return appointments
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch appointments: {e}")
            return []
        
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
    