# install pip tkcalendar xlsxwriter pillow sv-ttk
import tkinter as tk
from tkinter import messagebox, ttk
# from tkinter import font as tkFont
import models
from models import Customer, Appointment
from tkcalendar import DateEntry
from tkcalendar import Calendar
from datetime import datetime, timedelta
# import pandas as pd
# from pandastable import Table
import sv_ttk
import locale
# Ορισμός ελληνικών για το strftime
locale.setlocale(locale.LC_TIME, "el_GR.UTF-8")  # Linux/macOS
locale.setlocale(locale.LC_TIME, "Greek_Greece.1253")  # Windows alternative

models.setup_database()



class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Κομμώσεις για όλα τα γούστα")
        self.geometry("900x600+250+150")
        sv_ttk.set_theme("light")


        self.header = tk.Frame(self, bg="#2196F3", height=40)
        self.header.pack(side="top", fill="x")

         # Πίσω κουμπί (←)
        self.back_btn = tk.Button(
            self.header,
            text="←",
            font=("Ink Free",12,"bold"),
            bg="#2196F3",
            fg="white",
            bd=0,
            padx=0,
            pady=0,
            activebackground="#2196F3",
            activeforeground="#e6e6e6",
            command=lambda: self.show_frame("DashboardPage")
        )

        self.header_label = ttk.Label(
            self.header,
            text="Dashboard - Σημερινά Ραντεβού",
            font=("Segoe UI Variable Display", 15),
            background="#2196F3",
            foreground="white"
        )
        self.header_label.pack(padx=20, pady=(11,14), anchor="w", side="left")
        
        container = tk.Frame(self)
        container.pack(fill="both", expand=1)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        
        for Page in (DashboardPage, ClientsPage, NewAppointPage, NewClientPage, ShowClientPage, RemindersPage):
            page_name = Page.__name__
            frame = Page(parent=container, controller=self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[page_name] = frame
            
        self.show_frame("DashboardPage")
        # self.show_frame("NewAppointPage")
        # self.show_frame("ClientsPage")
        # self.show_frame("NewClientPage")
        # self.show_frame("ShowClientPage")
        # self.show_frame("RemindersPage")
        
    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        
        # Ανανεώνεις τον τίτλο του header
        if page_name == "DashboardPage":
            self.header_label.config(text="Dashboard - Σημερινά Ραντεβού")
        elif page_name == "ClientsPage":
            self.header_label.config(text="Διαχείριση Πελατών")
        elif page_name == "NewAppointPage":
            self.header_label.config(text="Δημιουργία Νέου Ραντεβού & Επεξεργασία")
        elif page_name == "NewClientPage":
            self.header_label.config(text="Προσθήκη/Επεξεργασία Πελάτη")
        elif page_name == "ShowClientPage":
            self.header_label.config(text="Ραντεβού του Πελάτη")
        elif page_name == "RemindersPage":
            self.header_label.config(text="Υπενθύμιση & Εκτύπωση")

        # === Εμφάνιση ή απόκρυψη του κουμπιού back ===
        if page_name == "DashboardPage":
            self.back_btn.pack_forget()
        else:
            self.back_btn.pack(side="right", padx=20, pady=12)

    
        
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
            # lbl_days = tk.Label(self, text=day.strftime("%a"), font=('Segoe UI', 9), bg="#f8fafd", pady=2)
            lbl = tk.Label(self, text=day.strftime("%a %d"), font=('Segoe UI Semibold', 12), bg="#f8fafd", fg="#1F1F1F", pady=0)
            lbl_month.grid(row=0, column=0, sticky="nw", columnspan=2, pady=(0,3))
            # lbl_days.grid(row=0, column=i+1, sticky="ew")
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
        # cell_size = 500 # Square cell size in pixels
        self.minical = Calendar(self.left_menu,
                             showweeknumbers=False, 
                             showothermonthdays=False, 
                             firstweekday='monday', 
                             selectmode='day', 
                             cursor="hand1", 
                             font=('Segoe UI Variable Text Semiligh', 10), 
                             locale="el_GR", 
                             selectbackground="#636332",
                             borderwidth=0,
                             background="#636332",
                             foreground="white",
                             headersbackground="#f1ede0",
                             headersforeground="#3F3F3F",
                             padding=0,
                             bordercolor="#F5F5F5",
                            # cellwidth=cell_size,
                            # cellheight=cell_size,
                            weekendbackground="#F5F5F5",
                            normalbackground="#F5F5F5",
                            highlightthickness=1
                             )
        # for i in range(6):
        #     self.cal._week_nbs[i].destroy()
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
        # self.new_appt_btn.pack(pady=5, padx=20, fill=tk.X, side="bottom")
        
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
        # self.clients_btn.pack(pady=5, padx=20, fill=tk.X, side="bottom")
        
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

       
        # Περιεχόμενο
        content = tk.Frame(self, bg="#f8fafd")
        content.pack(side="left", fill="both", expand=True, padx=0, pady=0)

        calendar = CalendarView(content, days=3)
        calendar.pack(side="left", fill="both", expand=True, padx=7, pady=(0,15))
        

class ClientsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # self.back_btn = tk.Button(controller.header, text="back", command=lambda: controller.show_frame("DashboardPage"))
        # self.back_btn.pack(padx=20, pady=15, anchor="e")

        # === Content wrapper ===
        content = tk.Frame(self, padx=40, pady=20)
        content.pack(expand=1, fill="both")

        

        # === Search Entry ===
        search_client = ttk.Entry(content)
        search_client.insert(0, "   Αναζήτηση με όνομα ή τηλέφωνο...")
        search_client.bind("<FocusIn>", lambda args: search_client.delete('0', 'end'))
        search_client.bind("<FocusOut>", lambda args: search_client.insert(0, "   Αναζήτηση με όνομα ή τηλέφωνο..."))
        search_client.pack(anchor="w", fill="x", pady=0, ipady=10)

        new_cli_btn = ttk.Button(content, text="+ Νέος πελάτης", style='Accent.TButton',
                                 command=lambda: (
                                                    controller.frames["NewClientPage"].reset_fields(),
                                                    controller.show_frame("NewClientPage")
                                                ))
        new_cli_btn.pack(anchor="w", pady=(20,0))


        # === List Container Frame ===
        list_container = ttk.Frame(content, border=1, borderwidth=1, relief="sunken")
        list_container.pack(fill="both", expand=True, padx=(0), pady=(20), anchor="center")

        # === Header Row ===
        headers = ["Επώνυμο", "Όνομα", "Τηλέφωνο", "Email", "Ενέργειες"]
        header_row = tk.Frame(list_container, bg="#C2DFF7")
        for h in headers:
            label = tk.Label(header_row, text=h, font=("Segoe UI", 10, "bold"), fg="#242525", bg="#C2DFF7", width=18, anchor="w")
            label.pack(side="left",pady=(2,1), anchor="w", padx=(18,0))
        header_row.pack(fill="x", ipady=(2))


        # === Canvas and Scrollbar ===
        canvas_frame = tk.Frame(list_container, highlightbackground="gray", highlightthickness=1, background="#fdfdfd")
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
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.scrollable_frame.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.scrollable_frame.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))


        self.load_clients()


    def load_clients(self):
    # 1. Καθάρισε όλα τα προηγούμενα rows
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        clients = self.show_all_customers()

        if ((len(clients)-10) < 10):
            for i in range((9-len(clients))):
                clients.append(("","","",""))
        
        clients.sort(key=lambda x: (x[1] == "", x[1]))

        for index, client in enumerate(clients):
            bg = "#e3f2fd" if index % 2 == 0 else "#E3DAC9"
            row = tk.Frame(self.scrollable_frame, background=bg, padx=4, pady=1)
            for i in range(4):
                tk.Label(row, text=client[i], font=("Segoe UI", 10), width=21, anchor="w", background=bg).pack(anchor="w", pady=2, padx=(14,2), side="left")

            tk.Button(row, text=" 🗑️", font=(18), fg="#242525", background=bg, command=lambda c=client: self.delete_and_reload(c), width=3, relief="flat").pack(side="right", padx=2, anchor="center")
            tk.Button(row, text=" 🖋️", font=(18), fg="#242525", background=bg,  command=lambda c=client:self.controller.frames["NewClientPage"].edit_customer(c[0],c[1],c[2],c[3]), width=3, relief="flat").pack(side="right", padx=2)
            tk.Button(row, text="🔍", font=(18), fg="#242525", background=bg,  command=lambda: self.controller.show_frame("ShowClientPage"), width=3, relief="flat").pack(side="right", padx=2)

            row.pack(fill="x", pady=1)

    def delete_and_reload(self, client):
        if messagebox.askyesno("Επιβεβαίωση", f"Να διαγραφεί ο/η {client[0]} {client[1]};"):
            Customer.delete_from_db(client[2])
            self.load_clients()

    def show_all_customers(self):
        """
        Display all appointments with patient details (name, surname, phone) in a message box.
        """
        try:
            # all_customers = Customer.get_all()
            customers_list = [(c.first_name, c.last_name, c.phone, c.email) for c in Customer.get_all()]
            return customers_list
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch appointments: {e}")




class NewAppointPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        

        content = ttk.Frame(self, padding=(40,25), border=5, borderwidth=3)
        content.pack(expand=1, ipady=10)

        ttk.Label(content, text="Πελάτης:", anchor="w", width=20).grid(row=0, column=0, sticky="w", pady=10)
        client = ttk.Entry(content, width=20).grid(row=0, column=1, sticky="w", pady=10)
        
        ttk.Label(content, text="Ημερομηνία:", anchor="w", width=20).grid(row=1, column=0,sticky="w", pady=10)
        appoint_date = DateEntry(content, date_pattern='dd-mm-yyyy', width=16).grid(row=1, column=1, sticky="w", pady=10)
        
        ttk.Label(content, text="Ώρα:", anchor="w", width=20).grid(row=2, column=0, sticky="w", pady=10)
        time_options = [f"{h:02d}:{m:02d}" for h in range(10, 20) for m in range(0, 60, 20)]
        time_var = tk.StringVar(content)
        time_dropdown = ttk.Combobox(content, textvariable=time_var, values=time_options, state="readonly", width=16)
        time_dropdown.grid(row=2, column=1, sticky="w", pady=10)
        
        ttk.Label(content, text="Διάρκεια:", anchor="w", width=20).grid(row=3, column=0, sticky="w", pady=10)
        duration_var = tk.StringVar(content, value="20")
        duration_dropdown = ttk.Combobox(content, textvariable=duration_var, values=["20","40","60"], state="readonly", width=16)
        duration_dropdown.grid(row=3, column=1, sticky="w", pady=10)
        
        ttk.Label(content, text="Είδος υπηρεσίας:", anchor="w", width=20).grid(row=4, column=0, sticky="w", pady=10)
        service_var = tk.StringVar(content, value="Κούρεμα")
        service_dropdown = ttk.Combobox(content, textvariable=service_var, values=["Κούρεμα","Βάψιμο","Χτένισμα"], state="readonly", width=16)
        service_dropdown.grid(row=4, column=1, sticky="w", pady=10)
        
        ttk.Label(content, text="Σημειώσεις:", anchor="w", width=20,).grid(row=5, column=0, sticky="w", pady=(10,10))
        notes = tk.Entry(content, bg="#fdfdfd", highlightbackground="white").grid(row=6, column=0, columnspan=2, padx=0, ipady=35, ipadx=108, sticky="nw")

        save_btn = ttk.Button(content, text="Αποθήκευση", width=12, underline=1, style='Accent.TButton').grid(row=7, column=1, pady=(40,15), sticky="w", padx=0)
        cancel_btn = ttk.Button(content, text="Ακύρωση", width=12, underline=1).grid(row=7, column=0, pady=(40,15), sticky="e", padx=15)
    

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

            # Validate input fields
            if not first_name.strip() or not last_name.strip() or not phone.strip() or not email.strip():
                messagebox.showerror("Σφάλμα", "Όλα τα πεδία (όνομα, επώνυμο, τηλέφωνο, email) είναι απαραίτητα!")
                return

            try:
                # Create and save the patient
                customer = Customer(first_name, last_name, phone, email)
                customer.save_to_db() # IF ALREADY EXISTS WE SHOULD UPDATE
                messagebox.showinfo("Επιτυχία", f"Αποθηκεύτηκε: {customer.first_name} {customer.last_name}")

                # Clear input fields
                self.reset_fields()

                # # Update the patient dropdown
                # update_patient_dropdown()

                # Καλεί την load_clients για να καθαρίσει το all clients table και να το ξαναγεμίσει περιέχοντας τον καινούργιο customer
                self.controller.frames["ClientsPage"].load_clients()
                # Πηγαίνουμε στην ClientsPage
                self.controller.show_frame("ClientsPage")
            except Exception as e:
                messagebox.showerror("Παρουσιάστηκε σφάλμα", f"Αποτυχία στην αποθήκευση του πελάτη: {e}")

    def edit_customer(self, first_name, last_name, phone, email):
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

            # ΟΤΑΝ ΠΑΤΑΩ ΑΠΟΘΗΚΕΥΣΗ, ΧΤΥΠΑΕΙ ΤΟ UNIQUE FIELD. ΠΡΕΠΕΙ ΝΑ ΜΠΕΙ UPDATE


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
            bg = "#e3f2fd" if index % 2 == 0 else "#F5EBD9"
            row = tk.Frame(scrollable_frame, background=bg, padx=4, pady=1)
            for i in range(3):
                tk.Label(row, text=client[i], font=("Segoe UI", 10), width=25, anchor="w", background=bg).pack(anchor="w", pady=0, padx=(14,2), side="left")

            
            

            row.pack(fill="x", pady=1)



        ttk.Button(content, text="⬅️ Επιστοφή στη Διαχείριση Πελατών", command=lambda: controller.show_frame("ClientsPage")).pack(anchor="s", pady=(15,10)) # .grid(row=4, column=0, sticky="S", pady=(15,10))



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

        
        date_entry = DateEntry(top_bar, date_pattern='dd-mm-yyyy', selectbackground="#A1795A", background="#A1795A", headersbackground="#f1ede0", headersforeground="#3F3F3F", showweeknumbers=False, showothermonthdays=False, font=('Segoe UI Variable Text Semiligh', 10),
                               bordercolor="#FDFDFD", weekendbackground="#FDFDFD", normalbackground="#FDFDFD" )
        date_entry.pack(side="right", padx=(10,40), pady=(2,1))
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
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # === Mousewheel scrolling ===
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        scrollable_frame.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        scrollable_frame.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # ttk.Separator(scrollable_frame).pack(anchor="w", pady=1)
        # === Example appointments ===
        for i in range(20):
            bg = "#e3f2fd" if i % 2 == 0 else "#F0DAC9"
            ttk.Label(
                scrollable_frame,
                text=f"{10+i}:00 - {10+i}:20 \t Μαρία Αντωνιάδου \t  Κούρεμα",
                background=bg,
                padding=(15,7),
                width=94
            ).pack(anchor="w", pady=1, padx=0)

        new_cli_btn = ttk.Button(self, text="Αποστολή Email", style='Accent.TButton', padding=(6,6), width=15)
        new_cli_btn.pack(padx=(300,0), pady=(10,20), side="left")
        new_cli_btn2 = ttk.Button(self, text="Εκτύπωση σε Excel", style='Accent.TButton', padding=(6,6), width=15)
        new_cli_btn2.pack(padx=(0,300), pady=(10,20), side="right")


        
             
        
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()