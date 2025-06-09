#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Σύστημα Διαχείρισης Ραντεβού - Κομμώσεις για όλα τα γούστα
Entry point της εφαρμογής
"""

import sys
import os
from tkinter import messagebox

# Προσθήκη του τρέχοντος φακέλου στο Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """Έλεγχος ότι όλες οι απαραίτητες βιβλιοθήκες είναι εγκατεστημένες"""
    missing_modules = []
    
    required_modules = {
        'tkinter': 'tkinter',
        'tkcalendar': 'tkcalendar',
        'xlsxwriter': 'xlsxwriter',
        # 'PIL': 'pillow',
        'sv_ttk': 'sv-ttk',
        # 'tkinter-tooltip': 'tkinter-tooltip'
    }
    
    for module_name, pip_name in required_modules.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_modules.append(pip_name)
    
    if missing_modules:
        error_msg = f"Λείπουν οι παρακάτω βιβλιοθήκες:\n{', '.join(missing_modules)}\n\n"
        error_msg += "Εγκαταστήστε τις με την εντολή:\n"
        error_msg += f"pip install {' '.join(missing_modules)}"
        
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Λείπουν βιβλιοθήκες", error_msg)
        except:
            print(error_msg)
        
        sys.exit(1)

def main():
    """Κύρια συνάρτηση εκκίνησης της εφαρμογής"""
    # Έλεγχος εξαρτήσεων
    check_dependencies()
    
    try:
        # Εισαγωγή της κύριας εφαρμογής
        from gui import MainApp
        
        # Δημιουργία και εκκίνηση της εφαρμογής
        app = MainApp()
        
        # # Κεντράρισμα παραθύρου - #Μεταφέρεται στο gui MainApp λόγω ταχύτητας στην εναλλαγή θέσης
        # app.update_idletasks()
        # width = app.winfo_width()
        # height = app.winfo_height()
        # x = (app.winfo_screenwidth() // 2) - (width // 2)
        # y = (app.winfo_screenheight() // 2) - (height // 2)
        # app.geometry(f'{width}x{height}+{x}+{y}')
        
        # Εκκίνηση
        app.mainloop()
        
    except Exception as e:
        error_msg = f"Σφάλμα κατά την εκκίνηση της εφαρμογής:\n{str(e)}"
        
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Σφάλμα", error_msg)
        except:
            print(error_msg)
        
        sys.exit(1)

if __name__ == "__main__":
    main()
