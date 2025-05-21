import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from tkcalendar import Calendar
from datetime import datetime, timedelta
# import pandas as pd
# from pandastable import Table
import sv_ttk

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Κομμώσεις για όλα τα γούστα")
        self.geometry("900x600+250+150")
        sv_ttk.set_theme("light")
        # style = ttk.Style(self)
        # style.theme_use('clam')
        # self.tk.call("source", "C:/Users/PC/Documents/eap/PLHPRO/appointment_system/gui/azure.tcl")
        # self.tk.call("set_theme", "light")

        self.header = tk.Frame(self, bg="#2196F3", height=60)
        self.header.pack(side="top", fill="x")

         # Πίσω κουμπί (←)
        self.back_btn = tk.Button(
            self.header,
            text="←",
            font=("Ink Free", 14, "bold"),
            bg="#2196F3",
            fg="white",
            bd=0,
            activebackground="#2196F3",
            activeforeground="#e6e6e6",
            command=lambda: self.show_frame("DashboardPage")
        )
        # self.header_label = tk.Label(
        #     self.header,
        #     text="Dashboard - Σημερινά Ραντεβού",
        #     bg="#2196F3",
        #     fg="white",
        #     font=("Courier New", 18)
        # )
        self.header_label = ttk.Label(
            self.header,
            text="Dashboard - Σημερινά Ραντεβού",
            font=("Ink Free", 20),
            background="#2196F3",
            foreground="white"
        )
        self.header_label.pack(padx=20, pady=15, anchor="w", side="left")
        
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
            self.header_label.config(text="Δημιουργία Νέου Ραντεβού")
        elif page_name == "NewClientPage":
            self.header_label.config(text="Προσθήκη/Επεξεργασία Πελάτη")
        elif page_name == "ShowClientPage":
            self.header_label.config(text="Ραντεβού Του Πελάτη")
        elif page_name == "RemindersPage":
            self.header_label.config(text="Υπενθύμιση & Εκτύπωση")

        # if page_name != "DashboardPage":
        #     tk.Button(self.header, text="back", command=lambda: self.show_frame("DashboardPage")).pack(padx=20, pady=15, anchor="e")
        # === Εμφάνιση ή απόκρυψη του κουμπιού back ===
        if page_name == "DashboardPage":
            self.back_btn.pack_forget()
        else:
            self.back_btn.pack(side="right", padx=20, pady=15)
        
class CalendarView(tk.Frame):
    def __init__(self, parent, days=3):
        super().__init__(parent, bg="white")

        self.days = days
        self.hours = [f"{h:02}:00" for h in range(10, 20)]  # 08:00 - 20:00

        self.build_grid()

    def build_grid(self):
        today = datetime.today()

        # --- Top row: Dates ---
        tk.Label(self, text="", width=10, bg="white").grid(row=0, column=0)
        for i in range(self.days):
            day = today + timedelta(days=i)
            lbl = tk.Label(self, text=day.strftime("%a\n%d/%m"), bg="#e6f2ff", width=20, pady=2)
            lbl.grid(row=0, column=i+1, sticky="nsew")

        # --- Rows: Hours ---
        for i, hour in enumerate(self.hours):
            tk.Label(self, text=hour, bg="#f2f2f2", width=10).grid(row=i+1, column=0, sticky="nsew")
            for j in range(self.days):
                cell = tk.Frame(self, width=193, height=46, bg="white", highlightbackground="#ccc", highlightthickness=1)
                cell.grid(row=i+1, column=j+1, sticky="nsew")
                cell.grid_propagate(False)

                # example placeholder appointment at 12:00 today
                if self.hours[i] == "12:00" and j == 0:
                    appt = tk.Label(cell, text="Μαρία Αντωνιάδου - Κούρεμα", bg="#fff2f7", fg="black", relief="flat", height=0, pady=0)
                    appt.pack(fill="x", padx=2, pady=0, side="bottom")
                if self.hours[i] == "12:00" and j == 0:
                    appt = tk.Label(cell, text="Αντουάν Μπισμπίκης - Χτένισμα", bg="#fff2f7", fg="black", relief="flat", height=0, pady=0)
                    appt.pack(fill="x", padx=2, pady=0, side="top")
                if self.hours[i] == "12:00" and j == 0:
                    appt = tk.Label(cell, text="Γιώργος Τσανακλάκης - Λούσιμο", bg="#e3f2fd", fg="black", relief="flat", height=0, pady=0)
                    appt.pack(fill="x", padx=2, pady=0)
                if self.hours[i] == "14:00" and j == 2:
                    appt = tk.Label(cell, text="Αντουάν Μπισμπίκης - Ξεψύρισμα & Βαφή", bg="#e3f2fd", fg="black", relief="flat", height=0, pady=0, wraplength=150)
                    appt.pack(fill="both", padx=2, pady=0, expand=1)
                if self.hours[i] == "19:00" and j == 1:
                    appt = tk.Label(cell, text="Μαρία Αντωνιάδου", bg="#fff2f7", fg="black", relief="flat", height=0, pady=0, padx=0, anchor="w")
                    appt.pack(fill="x", padx=0, pady=0, side="bottom")
        
class DashboardPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # self.header = tk.Frame(self, bg="#2196F3", height=60)
        # self.header.pack(fill="x", side="top")
        # # self.header.pack_propagate(False)  # Για να κρατήσει το ύψος
        
        # self.title_label = tk.Label(
        #     self.header, 
        #     text="Dashboard - Σημερινά Ραντεβού",
        #     fg="white", 
        #     bg="#2196F3",
        #     font=("Helvetica", 18)
        # )
        # self.title_label.place(x=20, y=15)
        
        # Left Side Menu
        self.left_menu = tk.Frame(self, bg="#F5F5F5", width=200)
        self.left_menu.pack(side="left", fill="y")

        # Calendar Mini
        self.minical = Calendar(self.left_menu,
                             showweeknumbers=False, 
                             showothermonthdays=False, 
                             firstweekday='monday', 
                             selectmode='day', 
                             cursor="hand1", 
                             font=('Segoe UI', 7), 
                             locale="el_GR", 
                             selectbackground="gray")
        # for i in range(6):
        #     self.cal._week_nbs[i].destroy()
        self.minical.pack(pady=(20,5), padx=10, fill="x")

        # === Search Entry ===
        search_client = ttk.Entry(self.left_menu)
        search_client.insert(0, "   Αναζήτηση πελάτη")
        search_client.bind("<FocusIn>", lambda args: search_client.delete('0', 'end'))
        search_client.bind("<FocusOut>", lambda args: search_client.insert(0, "   Όνομα ή τηλέφωνο..."))
        search_client.pack(anchor="w", fill="x", pady=15, ipady=4, padx=10)
        
        # Dashboard Button
        # self.dash_btn = tk.Button(
        #     self.left_menu,
        #     text="Dashboard",
        #     bg="#2196F3",
        #     fg="white",
        #     relief=tk.FLAT,
        #     padx=20,
        #     pady=10
        # )
        # self.dash_btn.pack(pady=(20,5), padx=20, fill="x", side="bottom")
        
        # New Appointment Button
        self.new_appt_btn = tk.Button(
            self.left_menu,
            text="Νέο Ραντεβού",
            bg="#4CAF50",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
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
            padx=20,
            pady=10,
            command=lambda: controller.show_frame("ClientsPage")
        )
        # self.clients_btn.pack(pady=5, padx=20, fill=tk.X, side="bottom")
        
        # Reminders Button
        self.remind_btn = tk.Button(
            self.left_menu,
            text="Υπενθυμίσεις",
            bg="#e72565",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            command=lambda: controller.show_frame("RemindersPage")
        )
        self.remind_btn.pack(pady=(12,25), padx=20, fill=tk.X, side="bottom")
        self.clients_btn.pack(pady=0, padx=20, fill=tk.X, side="bottom")
        self.new_appt_btn.pack(pady=12, padx=20, fill=tk.X, side="bottom")
        # Περιεχόμενο
        content = tk.Frame(self, bg="white")
        content.pack(fill="both", expand=True)

        calendar = CalendarView(content, days=3)
        calendar.pack(expand=1, fill="both", padx=20, pady=10)
        
class ClientPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        content = tk.Frame(self, padx=40, pady=20)
        content.pack(expand=1, fill="both")

        
        # search_client = tk.Entry(content, bg="white", border=1)
        search_client = ttk.Entry(content)
        
        search_client.insert(0, "   Αναζήτηση με όνομα ή τηλέφωνο...")
        search_client.bind("<FocusIn>", lambda args: search_client.delete('0', 'end'))
        search_client.bind("<FocusOut>", lambda args: search_client.insert(0, "   Αναζήτηση με όνομα ή τηλέφωνο..."))
        search_client.pack(anchor="w", fill="x", pady=5, ipady=10)
        # ipadx

        # new_cli_btn = tk.Button(content, text="+ Νέος πελάτης", bg="green", fg="white", padx=7, pady=7)
        new_cli_btn = ttk.Button(content, text="+ Νέος πελάτης", style='Accent.TButton',
            command=lambda: controller.show_frame("NewClientPage"))
        new_cli_btn.pack(anchor="w", pady=20)
        
        link = tk.Label(content, text = "🚽", font="TKDefaultFont 15", cursor="hand2")
        link.pack()
        link.bind("<Button-1>", lambda e: controller.show_frame("DashboardPage"))
        
        link2 = tk.StringVar(value="lalala", name="🚽")
        # link2.bind("<Button-1>", lambda e: controller.show_frame("RemindersPage"))
        self.clients_tree = ttk.Treeview(content, columns=("Επώνυμο", "Όνομα", "Τηλέφωνο", "Email", "Ενέργειες"), show="headings", height=10)
        # self.clients_tree.bind("<Double-1>", self.OnDoubleClick)
        self.clients_tree.bind("<Button-1>", self.on_tree_click)
        self.clients_tree.column("# 3",anchor="center", stretch=1, width=120)
        self.clients_tree.column("# 2", stretch=0, width=120)
        self.clients_tree.column("# 1", width=160)
        self.clients_tree.heading("Επώνυμο", text="Επώνυμο")
        self.clients_tree.heading("Όνομα", text="Όνομα")
        self.clients_tree.heading("Τηλέφωνο", text="Τηλέφωνο")
        self.clients_tree.heading("Email", text="Email")
        self.clients_tree.heading("Ενέργειες", text="Ενέργειες")
        link3 = tk.Label(self.clients_tree, text = "🚽", font="TKDefaultFont 15", cursor="hand2")
        # link3.pack()
        link3.bind("<Button-1>", lambda e: controller.show_frame("DashboardPage"))
        text3 = tk.Text(name="🔍", cursor="hand2", font="TKDefaultFont 15")
        text3.bind("<Button-1>", lambda e: controller.show_frame("NewClientPage"))
        self.clients_tree.insert('', 'end', values=('Αντωνιάδου','Μαρία', 6947000000, 'c@gmail.com', 'Επεξεργασία'), text="Item 1")
        self.clients_tree.insert('', 'end', values=('Παπαδόπουλος','Γιάννης', 6947000002, 'a@hotmail.com', 'Προβολή'))
        self.clients_tree.insert('', 'end', values=('Ζαχαρούμπας','Νικόλαος', 6947000001, 'b@yahoo.com', 'Διαγραφή'))
        self.clients_tree.insert('', 'end', values=('Αντωνιάδου','Μαρία', 6947000000, 'c@gmail.com', '🖋️'))
        self.clients_tree.insert('', 'end', values=('Παπαδόπουλος','Γιάννης', 6947000002, 'a@hotmail.com', '🔍'))
        self.clients_tree.insert('', 'end', values=('Ζαχαρούμπας','Νικόλαος', 6947000001, 'b@yahoo.com', '🚽'), open=1)
        self.clients_tree.insert('', 'end', values=('Αντωνιάδου','Μαρία', 6947000000, 'c@gmail.com', ' 🔍    -      🖋️ -    🗑️'))
        self.clients_tree.insert('', 'end', values=('Παπαδόπουλος','Γιάννης', 6947000002, 'a@hotmail.com', link2))
        self.clients_tree.insert('', 'end', values=('Ζαχαρούμπας','Νικόλαος', 6947000001, 'b@yahoo.com', text3), text=text3)
        self.clients_tree.insert('', 'end', values=('Αντωνιάδου','Μαρία', 6947000000, 'c@gmail.com', 'Επεξεργασία'))
        self.clients_tree.insert('', 'end', values=('Παπαδόπουλος','Γιάννης', 6947000002, 'a@hotmail.com', 'Προβολή'))
        self.clients_tree.insert('', 'end', values=('Ζαχαρούμπας','Νικόλαος', 6947000001, 'b@yahoo.com', link3))
        self.clients_tree.pack()
        
        

        # mydataset = {'countries': ["Greece", "Germany", "France"],'population': [ 10720000, 83240000, 67390000],'dialing_code': [ '+30', '+49', '+33']}
        # data = pd.DataFrame(mydataset)

        # table = Table(content, dataframe=data, showstatusbar=True, showtoolbar=1)
        # table.pack()
        
    def OnDoubleClick(self, event):
        item = self.clients_tree.selection()[0]
        print("you clicked on", self.clients_tree.item(item,"text"))
        self.controller.show_frame("DashboardPage")
    
    def on_tree_click(self, event):
        region = self.clients_tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = self.clients_tree.identify_row(event.y)
        column = self.clients_tree.identify_column(event.x)

        if not row_id or column != "#5":  # "#5" = 5η στήλη = "Ενέργειες"
            return

        item = self.clients_tree.item(row_id)
        actions = item['values'][4]  # Πιάνεις το string: "🔍 - 🖋️ - 🗑️"

        # Υπολόγισε σε ποιο εικονίδιο έκανε click (βάσει `event.x`)
        cell_bbox = self.clients_tree.bbox(row_id, column)
        if not cell_bbox:
            return
        x_rel = event.x - cell_bbox[0]

        if x_rel < 30:
            print("Προβολή")
            self.controller.show_frame("DashboardPage")  # π.χ. Προβολή
        elif x_rel < 70:
            print("Επεξεργασία")
            self.controller.show_frame("NewClientPage")
        else:
            print("Διαγραφή")
            self.clients_tree.delete(row_id)

class ClientsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # self.back_btn = tk.Button(controller.header, text="back", command=lambda: controller.show_frame("DashboardPage"))
        # self.back_btn.pack(padx=20, pady=15, anchor="e")

        # === Content wrapper ===
        content = tk.Frame(self, padx=40, pady=20, bg="#E1F0F8")
        content.pack(expand=1, fill="both")

        # === Search Entry ===
        search_client = ttk.Entry(content)
        search_client.insert(0, "   Αναζήτηση με όνομα ή τηλέφωνο...")
        search_client.bind("<FocusIn>", lambda args: search_client.delete('0', 'end'))
        search_client.bind("<FocusOut>", lambda args: search_client.insert(0, "   Αναζήτηση με όνομα ή τηλέφωνο..."))
        search_client.pack(anchor="w", fill="x", pady=0, ipady=10)

        new_cli_btn = ttk.Button(content, text="+ Νέος πελάτης", style='Accent.TButton',
                                 command=lambda: controller.show_frame("NewClientPage"))
        new_cli_btn.pack(anchor="w", pady=20)

        # === Scrollable Area ===
        container = tk.Frame(content, bg="#E1F0F8")
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg="#E1F0F8", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#E1F0F8")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # === Header Row ===
        headers = ["Επώνυμο", "Όνομα", "Τηλέφωνο", "Email", "Ενέργειες"]
        header_row = tk.Frame(scrollable_frame, bg="#263238")
        for h in headers:
            label = tk.Label(header_row, text=h, font=("Segoe UI", 10, "bold"), fg="white", bg="#263238", width=18)
            label.pack(side="left", padx=5, pady=2)
        header_row.pack(fill="x", pady=2)

        # === Πελάτες (δείγμα) ===
        clients = [
            ("Αντωνιάδου", "Μαρία", "6947000000", "maria@gmail.com"),
            ("Ζαχαρούμπας", "Νικόλαος", "6947000001", "nikos@yahoo.com"),
            ("Παπαδόπουλος", "Γιάννης", "6947000002", "giannis@hotmail.com")
        ] * 5

        for client in clients:
            row = tk.Frame(scrollable_frame, bg="#eceff1", padx=5, pady=1, highlightbackground="gray", highlightthickness=1)
            for i in range(4):
                tk.Label(row, text=client[i], font=("Segoe UI", 10), width=20, anchor="center", bg="#eceff1").pack(side="left", padx=5)

            # Actions
            ttk.Button(row, text=" 🗑️", command=lambda c=client: print("Διαγραφή:", c), width=3).pack(side="right", padx=2)
            ttk.Button(row, text=" 🖋️", command=lambda c=client: print("Επεξεργασία:", c), width=3).pack(side="right", padx=2)
            ttk.Button(row, text="🔍", command=lambda: controller.show_frame("ShowClientPage"), width=3).pack(side="right", padx=2)
            

            row.pack(fill="x", pady=1)

        # === Ροδέλα ποντικιού ===
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)


class NewAppointPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Περιεχόμενο
        # content = tk.Frame(self, bg="white", padx=80, pady=30)
        # content.pack(expand=1, ipady=10)
        content = ttk.Frame(self, padding=(40,25), border=5, borderwidth=3)
        content.pack(expand=1, ipady=10)

        # tk.Label(content, text="Εδώ μπορεί να μπουν σημερινά ραντεβού ή στατιστικά...").pack(pady=50)
        
        # tk.Label(content, text="Πελάτης:", bg="white", anchor="w", width=20).grid(row=0, column=0, sticky="w", pady=10)
        # client = tk.Entry(content).grid(row=0, column=1, sticky="w", pady=10)
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
        service_dropdown = ttk.Combobox(content, textvariable=service_var, values=["Κούρεμα","Λούσιμο"], state="readonly", width=16)
        service_dropdown.grid(row=4, column=1, sticky="w", pady=10)
        
        ttk.Label(content, text="Σημειώσεις:", font=("Gabriola", 15), anchor="sw").grid(row=5, column=0, sticky="sw", pady=(10,0))
        notes = tk.Entry(content, bg="#fdfdfd", highlightbackground="white").grid(row=6, column=0, columnspan=2, padx=5, ipady=35, ipadx=100, sticky="nw")

        save_btn = ttk.Button(content, text="Αποθήκευση", width=12).grid(row=7, column=0, pady=(40,15))
        cancel_btn = ttk.Button(content, text="Ακύρωση", width=12).grid(row=7, column=1, pady=(40,15))
    

class NewClientPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        content = ttk.Frame(self, padding=(30,10), border=5, borderwidth=3, relief="groove")
        content.pack(expand=1, ipady=10)

        ttk.Label(content, text="Όνομα:", anchor="w", width=20).grid(row=0, column=0, sticky="w", pady=(25,10))
        name = ttk.Entry(content).grid(row=0, column=1, sticky="w", pady=(25,10))
        ttk.Label(content, text="Επώνυμο:", anchor="w", width=20).grid(row=1, column=0, sticky="w", pady=10)
        surname = ttk.Entry(content).grid(row=1, column=1, sticky="w", pady=10)
        ttk.Label(content, text="Τηλέφωνο:", anchor="w", width=20).grid(row=2, column=0, sticky="w", pady=10)
        telephone = ttk.Entry(content).grid(row=2, column=1, sticky="w", pady=10)
        ttk.Label(content, text="Email:", anchor="w", width=20).grid(row=3, column=0, sticky="w", pady=10)
        email = ttk.Entry(content).grid(row=3, column=1, sticky="w", pady=10)
        ttk.Label(content, text="Σημειώσεις (προαιρετικό)", anchor="w").grid(row=4, column=0, sticky="w", pady=(20,8))
        notes = ttk.Entry(content).grid(row=5, column=0, columnspan=2, padx=5, ipady=35, ipadx=80, sticky="w")

        cancel_btn = ttk.Button(content, text="Ακύρωση", width=12).grid(row=6, column=0, pady=(65,0))
        save_btn = ttk.Button(content, text="Αποθήκευση", width=12, style='Accent.TButton').grid(row=6, column=1, pady=(65,0))
        


class ShowClientPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        content = tk.Frame(self, padx=40, pady=0)
        content.pack()

        client = ttk.Label(content, text="Μαρία Αντωνιάδου", font=('Segoe UI Variable Display Semib', 20))
        client.grid(row=0, column=0, sticky="NW", pady=(30,40), padx=45)
        contact_frame = ttk.Frame(content, border=0, borderwidth=10, relief="ridge")
        contact_frame.grid(row=0, column=0, sticky="NE", pady=10)
        contact = ttk.Label(contact_frame, text="Επικοινωνία", font=('Segoe UI Variable Display Semib', 12))
        contact.grid(row=0, column=0, sticky="N", pady=(0,10))
        contact_phone = ttk.Label(contact_frame, text='☎️6947000000', font=('Segoe UI Variable Display', 10))
        contact_phone.grid(row=1, column=0, sticky="SW", pady=3)
        contact_email = ttk.Label(contact_frame, text="📫 pentagiotissa@gmail.com", font=('Segoe UI Variable Display', 10)) #den tha xoraei to email
        contact_email.grid(row=2, column=0, sticky="SW")

        columns = ("Ημερομηνία", "Ώρα", "Υπηρεσία")

        ##  Function to sort the Treeview by column
        # def sort_treeview(tree, col, descending):
        #     data = [(tree.set(item, col), item) for item in tree.get_children('')]
        #     data.sort(reverse=descending)
        #     for index, (val, item) in enumerate(data):
        #         tree.move(item, '', index)
        #     tree.heading(col, command=lambda: sort_treeview(tree, col, not descending))

        
        self.client_tree = ttk.Treeview(content, columns=columns, show="headings", height=15)
        self.client_tree.column(0,anchor="center")
        self.client_tree.column(1,anchor="center")
        self.client_tree.column(2,anchor="center")
        self.client_tree.heading("Ημερομηνία", text="Ημερομηνία")
        self.client_tree.heading("Ώρα", text="Ώρα")
        self.client_tree.heading("Υπηρεσία", text="Υπηρεσία")
        self.client_tree.grid(row=1, column=0, sticky="NSEW", pady=3)
        ## Configure column headings and sorting functionality
        # for col in columns:
        #     client_tree.heading(col, text=col, command=lambda c=col: sort_treeview(client_tree, c, False))
        #     client_tree.column(col)
        # mylist = []
        # for i in range(20,0,-1):
            # client_tree.insert('', 'end', values=(f'{i}/1/2025','12:00', 'Κούρεμα'))
        #     mylist.append(f'{i}/1/2025')
        
        # mylist.sort(key=lambda x: datetime.strptime(x, '%d/%m/%Y'))
        # for i in range(0,20,1):
        #     self.client_tree.insert('', 'end', values=(mylist[i],'12:00', 'Κούρεμα'))
        # print(mylist)

        vsb = ttk.Scrollbar(content, orient="vertical", command=self.client_tree.yview)
        vsb.grid(row=1, column=1, sticky="nse", pady=(25,0))

        self.client_tree.configure(yscrollcommand=vsb.set)

        self.items = []  # list of tuples: (date_obj, item_id)
        today = datetime.now().date()

        # Δημιουργούμε ημερομηνίες 1-30 Μαΐου 2025
        mylist = [f'{i}/5/2025' for i in range(1, 30)]
        mylist.sort(key=lambda x: datetime.strptime(x, '%d/%m/%Y'))

        for date_str in mylist:
            date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
            item = self.client_tree.insert('', 'end', values=(date_str, '12:00', 'Κούρεμα'))
            self.items.append((date_obj, item))

        # βρες την κατάλληλη ημερομηνία
        self.target_item = self.find_best_matching_item(today)
        self.after(100, self.scroll_to_target)


        ttk.Button(content, text="⬅️ Επιστοφή στη Διαχείριση Πελατών", command=lambda: controller.show_frame("ClientsPage")).grid(row=2, column=0, sticky="S", pady=(15,10))

    def find_best_matching_item(self, today):
        future_dates = sorted([d for d in self.items if d[0] >= today], key=lambda x: x[0])
        if future_dates:
            return future_dates[0][1]  # επιστρέφει το item_id της πιο κοντινής μελλοντικής

        # αλλιώς πάρε την τελευταία διαθέσιμη (πιο κοντινή παρελθοντική)
        past_dates = sorted([d for d in self.items if d[0] < today], key=lambda x: x[0], reverse=True)
        if past_dates:
            return past_dates[0][1]

        return None  # τίποτα δεν υπάρχει

    def scroll_to_target(self):
        if self.target_item:
            self.client_tree.selection_set(self.target_item)
            self.client_tree.focus(self.target_item)
            self.client_tree.see(self.target_item)

            # Κάνει την ημερομηνία να εμφανίζεται **στην κορυφή**
            index = self.client_tree.index(self.target_item)
            if index > 0:
                above_item = self.client_tree.get_children()[max(0, index - 1)]
                self.client_tree.see(above_item)
    

class ShoClientPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        content = tk.Frame(self, padx=40, pady=0)
        content.pack()

        columns = ("Ημερομηνία", "Ώρα", "Υπηρεσία")
        self.client_tree = ttk.Treeview(content, columns=columns, show="headings")
        self.client_tree.column(0, anchor="center")
        self.client_tree.column(1, anchor="center")
        self.client_tree.column(2, anchor="center")
        self.client_tree.heading("Ημερομηνία", text="Ημερομηνία")
        self.client_tree.heading("Ώρα", text="Ώρα")
        self.client_tree.heading("Υπηρεσία", text="Υπηρεσία")
        self.client_tree.grid(row=1, column=0, sticky="NSEW")

        self.items = []  # list of tuples: (date_obj, item_id)
        today = datetime.now().date()

        # Δημιουργούμε ημερομηνίες 1-30 Μαΐου 2025
        mylist = [f'{i}/5/2025' for i in range(1, 14)]
        mylist.sort(key=lambda x: datetime.strptime(x, '%d/%m/%Y'))

        for date_str in mylist:
            date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
            item = self.client_tree.insert('', 'end', values=(date_str, '12:00', 'Κούρεμα'))
            self.items.append((date_obj, item))

        # βρες την κατάλληλη ημερομηνία
        self.target_item = self.find_best_matching_item(today)
        self.after(100, self.scroll_to_target)

    def find_best_matching_item(self, today):
        future_dates = sorted([d for d in self.items if d[0] >= today], key=lambda x: x[0])
        if future_dates:
            return future_dates[0][1]  # επιστρέφει το item_id της πιο κοντινής μελλοντικής

        # αλλιώς πάρε την τελευταία διαθέσιμη (πιο κοντινή παρελθοντική)
        past_dates = sorted([d for d in self.items if d[0] < today], key=lambda x: x[0], reverse=True)
        if past_dates:
            return past_dates[0][1]

        return None  # τίποτα δεν υπάρχει

    def scroll_to_target(self):
        if self.target_item:
            self.client_tree.selection_set(self.target_item)
            self.client_tree.focus(self.target_item)
            self.client_tree.see(self.target_item)

            # Κάνει την ημερομηνία να εμφανίζεται **στην κορυφή**
            index = self.client_tree.index(self.target_item)
            if index > 0:
                above_item = self.client_tree.get_children()[max(0, index - 1)]
                self.client_tree.see(above_item)





        
class ReminderPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        
        # mylist = tk.Listbox(self, yscrollcommand = scrollbar.set)
        # for line in range(100):
        #     mylist.insert('end', "This is line number " + str(line))
        #     # this changes the background colour of the 2nd item
        # mylist.itemconfig(1, {'bg':'red'})

    # this changes the font color of the 4th item
        # for jack in range(6,50,2):
        #     mylist.itemconfig(jack, bg="blue")

    # another way to pass the colour
        # mylist.itemconfig(2, bg='green')
        # mylist.itemconfig(0, foreground="purple")
   
        # mylist.pack( side ="left", fill = "both", padx=40, pady=20, ipady=10 )
        

        content = tk.Frame(self, padx=40, pady=20)
        content.pack(expand=1, fill="both")

        canvas = tk.Canvas(content, scrollregion=(0, 0, 1700, 1700))
        canvas.grid(row=1, column=0)

        
        # scrollbar.config( command = canvas.yview )
        
        

        

        # scrollbar = tk.Scrollbar(content)
        # scrollbar.grid(row=2, column=31, rowspan=15, sticky="ne")

        ttk.Label(content, text="Όλα τα ραντεβού για:").grid(row=0, column=0, sticky="w")
        date_entry = DateEntry(content, date_pattern='dd-mm-yyyy')
        date_entry.grid(row=0, column=1, sticky="w")

        

        # appoint_tree = ttk.Treeview(content, columns=( "Ώρες", "Όνοματεπώνυμο", "Υπηρεσία", 'Σημείωσεις'), show="", height=7, padding=7)
        # appoint_tree.column("# 1", width=140)
        # appoint_tree.column("# 2", width=215)
        # appoint_tree.column("# 3", width=220)
        # appoint_tree.column("# 4", anchor="w")
        # appoint_tree.insert('', 'end', values=('10:00 - 10:20','Μαρία'+' '+'Αντωνιάδου', 'Κούρεμα', 'Καρεκλάκι για τον μπέμπη'))
        # appoint_tree.insert('', 'end', values=('13:20 - 14:00', 'Γιάννης'+' '+'Παπαδόπουλος', 'Λούσιμο, Κούρεμα, Νύχια'))
        # appoint_tree.insert('', 'end', values=('18:00 - 18:40', 'Νικόλαος'+' '+'Ζαχαρούμπας', 'Βάψιμο', 'Πράσινο χρώμα'))
        # appoint_tree.grid(row=1, column=0, columnspan=30, pady=20)
        scrollbar = ttk.Scrollbar(canvas, orient="vertical", command = canvas.yview)
        scrollbar.grid(row=0, column=31, rowspan=15, sticky="ns")
        canvas.config(yscrollcommand=scrollbar)
        ttk.Label(canvas, text='10:00 - 10:20 \tΜαρία Αντωνιάδου \t  Κούρεμα', background="#e3f2fd", padding=(15,5), width="97").grid(row=2, column=0, columnspan=30, pady=0, sticky="w")
        ttk.Label(canvas, text='13:20 - 14:00 \tΓιάννης Παπαδόπουλος \t  Λούσιμο, Κούρεμα, Νύχια', background="#fff2f7", padding=(15,5), width="97").grid(row=3, column=0, columnspan=30, pady=5, sticky="w")
        ttk.Label(canvas, text='18:00 - 18:20 \tΜαρία Αντωνιάδου \t  Κούρεμα', background="#e3f2fd", padding=(15,5), width="97").grid(row=4, column=0, columnspan=30, pady=0, sticky="w")
        ttk.Label(canvas, text='19:20 - 20:00 \tΝικόλαος Ζαχαρούμπας \t  Χτένισμα & Βαφή', background="#fff2f7", padding=(15,5), width="97").grid(row=5, column=0, columnspan=30, pady=5, sticky="w")
        ttk.Label(canvas, text='10:00 - 10:20 \tΜαρία Αντωνιάδου \t  Κούρεμα', background="#e3f2fd", padding=(15,5), width="97").grid(row=6, column=0, columnspan=30, pady=0, sticky="w")
        ttk.Label(canvas, text='13:20 - 14:00 \tΓιάννης Παπαδόπουλος \t  Λούσιμο, Κούρεμα, Νύχια', background="#fff2f7", padding=(15,5), width="97").grid(row=7, column=0, columnspan=30, pady=5, sticky="w")
        ttk.Label(canvas, text='18:00 - 18:20 \tΜαρία Αντωνιάδου \t  Κούρεμα', background="#e3f2fd", padding=(15,5), width="97").grid(row=8, column=0, columnspan=30, pady=0, sticky="w")
        ttk.Label(canvas, text='19:20 - 20:00 \tΝικόλαος Ζαχαρούμπας \t  Χτένισμα & Βαφή', background="#fce4ec", padding=(15,5), width="97").grid(row=9, column=0, columnspan=30, pady=5, sticky="w")
        ttk.Label(canvas, text='10:00 - 10:20 \tΜαρία Αντωνιάδου \t  Κούρεμα', background="#e3f2fd", padding=(15,5), width="97").grid(row=10, column=0, columnspan=30, pady=0, sticky="w")
        ttk.Label(canvas, text='13:20 - 14:00 \tΓιάννης Παπαδόπουλος \t  Λούσιμο, Κούρεμα, Νύχια', background="#fce4ec", padding=(15,5), width="97").grid(row=11, column=0, columnspan=30, pady=5, sticky="w")
        ttk.Label(canvas, text='18:00 - 18:20 \tΜαρία Αντωνιάδου \t  Κούρεμα', background="#e3f2fd", padding=(15,5), width="97").grid(row=12, column=0, columnspan=30, pady=0, sticky="w")
        ttk.Label(canvas, text='19:20 - 20:00 \tΝικόλαος Ζαχαρούμπας \t  Χτένισμα & Βαφή', background="#fce4ec", padding=(15,5), width="97").grid(row=13, column=0, columnspan=30, pady=5, sticky="w")
        ttk.Label(canvas, text='10:00 - 10:20 \tΜαρία Αντωνιάδου \t  Κούρεμα', background="#e3f2fd", padding=(15,5), width="97").grid(row=14, column=0, columnspan=30, pady=0, sticky="w")
        ttk.Label(canvas, text='13:20 - 14:00 \tΓιάννης Παπαδόπουλος \t  Λούσιμο, Κούρεμα, Νύχια', background="#fce4ec", padding=(15,5), width="97").grid(row=15, column=0, columnspan=30, pady=5, sticky="w")
        ttk.Label(canvas, text='18:00 - 18:20 \tΜαρία Αντωνιάδου \t  Κούρεμα', background="#e3f2fd", padding=(15,5), width="97").grid(row=16, column=0, columnspan=30, pady=0, sticky="w")
        ttk.Label(canvas, text='19:20 - 20:00 \tΝικόλαος Ζαχαρούμπας \t  Χτένισμα & Βαφή', background="#fce4ec", padding=(15,5), width="97").grid(row=17, column=0, columnspan=30, pady=5, sticky="w")
        
        
        canvas.config(scrollregion=canvas.bbox('all'))

class RemindersPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # === Content Frame ===
        content = ttk.Frame(self, border=1, borderwidth=1, relief="sunken")
        content.pack(fill="both", expand=True, padx=(40,30), pady=20, side="left", anchor="nw")

        # === Date Picker ===
        top_bar = tk.Frame(content, bg="#dbdbdb")
        top_bar.pack(fill="x", ipadx=10, ipady=(2))

        
        date_entry = DateEntry(top_bar, date_pattern='dd-mm-yyyy')
        date_entry.pack(side="right", padx=(10,40), pady=(2,1))
        ttk.Label(top_bar, text="Όλα τα ραντεβού για:", background="#dbdbdb").pack(side="right", pady=(2,1))

        # === Canvas and Scrollbar ===
        canvas_frame = tk.Frame(content, highlightbackground="gray", highlightthickness=1)
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

        ttk.Separator(scrollable_frame).pack(anchor="w", pady=1)
        # === Example appointments ===
        for i in range(20):
            bg = "#e3f2fd" if i % 2 == 0 else "#fdfbe1"
            ttk.Label(
                scrollable_frame,
                text=f"{10+i}:00 - {10+i}:20 \t Μαρία Αντωνιάδου \t  Κούρεμα",
                background=bg,
                padding=(15,7),
                width=94
            ).pack(anchor="w", pady=3, padx=7)

        new_cli_btn = ttk.Button(self, text="Αποστολή\n    email", style='Accent.TButton', width=10, padding=(2,14))
        new_cli_btn.pack(side="top", padx=(0,30), pady=(80,0))
        new_cli_btn2 = ttk.Button(self, text="Εκτύπωση\n  σε Excel", style='Accent.TButton', width=10, padding=(2,14))
        new_cli_btn2.pack(side="top", padx=(0,30), pady=(30,30))
        new_cli_btn3 = ttk.Button(self, text="Επιστροφή",style='Accent.TButton', width=9, cursor="hand2",
            command=lambda: controller.show_frame("DashboardPage"))
        new_cli_btn3.pack(side="bottom", padx=(0,30), pady=40)


        
             
        
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()