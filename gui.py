# GUI module using Tkinter
import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
# from models import Customer, Appointment
from PIL import Image, ImageTk
# from export_excel import export_appointments_to_excel
# from emails_utils import send_reminders

# Create main window
root = tk.Tk()
root.title("Barber Shop Appointment System")
root.geometry("600x700")
root.configure(bg='white')

# Header with Cross Icon
header_frame = tk.Frame(root, bg='white')
header_frame.pack(pady=10)

tk.Label(header_frame, text="Barber Shop Appointment System", font=("Segoe UI Variable Display", 14, "bold")).pack()

def run_gui(root_window=None):
    global root
    if root_window:
        root = root_window
    root.mainloop()

if __name__ == "__main__":
    run_gui(root)