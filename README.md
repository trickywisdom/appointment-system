Appointment System

This is a simple desktop application for managing appointments using Python and Tkinter.

## 📋 Features

- Add, update and list customers
- Book and validate appointments
- Prevent overlapping and invalid time slots
- Search by date or phone number
- Export appointments to Excel

## 💻 Technologies Used

- Python 3
- Tkinter
- SQLite3
- XlsxWriter
- tkcalendar
- PIL

## 🗂 Project Structure

```
appointment-system/
│
├── main.py                # Entry point of the application
├── gui.py                 # Graphical interface (Tkinter)
├── models.py              # Patient & Appointment classes
├── database.py            # Database connection logic
├── export_excel.py        # Export appointments to Excel
├── emails_utils.py        # Notify customers through email
├── salon_appointments.db  # SQLite DB (auto-created)
├── README.md              # Project overview
├── .gitignore             # Git ignored files
├── images/                # images for a better looking app
└── docs/                  # Documentation, diagrams, PDF files
```

## 🚀 Getting Started

1. Clone the repository:
```bash
git clone https://github.com/PLHPRO/appointment-system.git
cd appointment-system
```

2. Install dependencies:
```bash
pip install tkcalendar xlsxwriter sv-ttk tkinter-tooltip
```

3. Run the app:
```bash
python main.py
```

## 👨‍💻 Team Members

- Member 1: 
- Member 2: 
- Member 3: 
- Member 4: 

---

*This project is part of a university assignment.*
