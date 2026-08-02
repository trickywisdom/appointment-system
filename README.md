Appointment System

This is a simple desktop application for managing appointments using Python and Tkinter.

## 📋 Features

- Add, update and list customers
- Book and validate appointments
- Prevent overlapping and invalid time slots
- Search customers by first name, last name, phone or email — insensitive to Greek accents and case
- Browse appointments by date
- Export appointments to Excel

## 💻 Technologies Used

- Python 3
- Tkinter
- SQLite3
- XlsxWriter
- tkcalendar
- sv-ttk
- tkinter-tooltip

## 🗂 Project Structure

```
appointment-system/
│
├── main.py                # Entry point of the application
├── gui.py                 # Graphical interface (Tkinter)
├── models.py              # Customer & Appointment classes
├── database.py            # Database connection logic
├── export_excel.py        # Export appointments to Excel
├── emails_utils.py        # Notify customers through email
├── test_bugfixes.py       # Verification script — plain runnable, no pytest
├── salon_appointments.db  # SQLite DB (auto-created)
├── README.md              # Project overview
├── .gitignore             # Git ignored files
└── images/                # images for a better looking app
```

## 🚀 Getting Started

1. Clone the repository:
```bash
git clone https://github.com/trickywisdom/appointment-system.git
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

## 👨‍💻 Author

- Spyros Trimis — [github.com/trickywisdom](https://github.com/trickywisdom)

---

*This project began as a university assignment and is now maintained as a personal portfolio project.*
