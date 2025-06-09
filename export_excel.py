# Εξαγωγή ραντεβού σε Excel
import xlsxwriter
from datetime import datetime
import models
import os

def export_appointments_to_excel(date_str, filename=None):
    """
    Εξάγει τα ραντεβού της επιλεγμένης μέρας σε Excel
    
    Args:
        date_str: Ημερομηνία ως string (μορφή "DD-MM-YYYY")
        filename: Προαιρετικό όνομα αρχείου
    """
    try:
        # Μετατροπή σε ημερομηνία για έλεγχο εγκυρότητας
        date_obj = datetime.strptime(date_str, "%d-%m-%Y").date()
        
        # Δημιουργία ονόματος αρχείου αν δεν δοθεί
        if not filename:
            filename = f'ραντεβού_{date_obj.strftime("%Y-%m-%d")}.xlsx'
        
        # Λήψη ραντεβού από τη βάση
        appointments = models.Appointment.get_by_date(date_obj)
        print("Βρέθηκαν ραντεβού:", appointments)
        
    except Exception as e:
        raise Exception(f"Failed to export appointments: {str(e)}")
    
    # Δημιουργία Excel αρχείου
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet('Ραντεβού')
    
    # Μορφοποίηση
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'bg_color': '#2196F3',
        'font_color': 'white',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        'align': 'left',
        'valign': 'vcenter',
        'border': 1
    })
    
    center_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })
    
    # Τίτλος
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })
    # Μορφοποίηση για ώρα (HH:MM:SS)
    time_format = workbook.add_format({
        'num_format': 'HH:MM',  # Μορφοποίηση ώρας
        'align': 'center'
    })
    print("So far so good1:")
    worksheet.merge_range('A1:F1', 
                         f'Ραντεβού - {date_str}', # .strftime("%A %d/%m/%Y")
                         title_format)
    
    # Ρύθμιση πλάτους στηλών
    worksheet.set_column('A:A', 8)   # Ώρα
    worksheet.set_column('B:B', 10)  # Διάρκεια
    worksheet.set_column('C:C', 25)  # Όνομα
    worksheet.set_column('D:D', 15)  # Τηλέφωνο
    worksheet.set_column('E:E', 15)  # Υπηρεσία
    worksheet.set_column('F:F', 30)  # Σημειώσεις
    
    # Headers
    headers = ['Ώρα', 'Διάρκεια', 'Πελάτης', 'Τηλέφωνο', 'Υπηρεσία', 'Σημειώσεις']
    for col, header in enumerate(headers):
        worksheet.write(2, col, header, header_format)
    print("So far so good2:")
    # Δεδομένα
    row = 3
    for appt in appointments:
        dt_obj = datetime.strptime(appt.datetime, "%Y-%m-%d %H:%M")
        print("dt_obj.time()",dt_obj.time())
        worksheet.write(row, 0, dt_obj.time(), time_format)
        # worksheet.write(row, 0, appt.datetime, center_format) # .strftime('%H:%M')
        worksheet.write(row, 1, f"{appt.duration}'", center_format)
        worksheet.write(row, 2, appt.customer_name, cell_format)
        worksheet.write(row, 3, appt.customer_phone, cell_format)
        worksheet.write(row, 4, appt.services or '-', cell_format)
        worksheet.write(row, 5, appt.notes or '-', cell_format)
        row += 1
    
    # Σύνοψη στο τέλος
    if appointments:
        row += 1
        summary_format = workbook.add_format({
            'bold': True,
            'bg_color': '#E3F2FD',
            'border': 1
        })
        
        worksheet.merge_range(f'A{row+1}:B{row+1}', 
                            'Σύνολο Ραντεβού:', summary_format)
        worksheet.write(f'C{row+1}', len(appointments), summary_format)
        
        # Υπολογισμός συνολικού χρόνου
        total_duration = sum(appt.duration for appt in appointments)
        hours = total_duration // 60
        minutes = total_duration % 60
        
        worksheet.merge_range(f'D{row+1}:E{row+1}', 
                            'Συνολική Διάρκεια:', summary_format)
        worksheet.write(f'F{row+1}', 
                       f'{hours} ώρες {minutes} λεπτά', summary_format)
    
    # Κλείσιμο αρχείου
    workbook.close()
    
    # Επιστροφή του απόλυτου path
    return os.path.abspath(filename)


def export_customer_appointments(customer_id, filename=None):
    """
    Εξάγει όλα τα ραντεβού ενός πελάτη σε Excel
    
    Args:
        customer_id: Το ID του πελάτη
        filename: Προαιρετικό όνομα αρχείου
    
    Returns:
        Το path του αρχείου που δημιουργήθηκε
    """
    
    # Λήψη στοιχείων πελάτη
    customer = None
    for c in models.Customer.get_all():
        if c.id == customer_id:
            customer = c
            break
    
    if not customer:
        raise ValueError("Δεν βρέθηκε ο πελάτης")
    
    # Δημιουργία ονόματος αρχείου
    if not filename:
        filename = f'ραντεβού_{customer.last_name}_{customer.first_name}.xlsx'
    
    # Λήψη ραντεβού
    appointments = models.Appointment.get_by_customer(customer_id)
    
    # Δημιουργία Excel
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet('Ιστορικό Ραντεβού')
    
    # Μορφοποίηση
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'bg_color': '#2196F3',
        'font_color': 'white',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        'align': 'left',
        'valign': 'vcenter',
        'border': 1
    })
    
    center_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })
    
    # Τίτλος και στοιχεία πελάτη
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    info_format = workbook.add_format({
        'font_size': 11,
        'align': 'left'
    })
    
    worksheet.merge_range('A1:E1', 
                         f'Ιστορικό Ραντεβού - {customer.last_name} {customer.first_name}', 
                         title_format)
    
    worksheet.merge_range('A2:B2', f'Τηλέφωνο: {customer.phone}', info_format)
    worksheet.merge_range('C2:E2', f'Email: {customer.email}', info_format)
    
    # Πλάτος στηλών
    worksheet.set_column('A:A', 15)  # Ημερομηνία
    worksheet.set_column('B:B', 8)   # Ώρα
    worksheet.set_column('C:C', 10)  # Διάρκεια
    worksheet.set_column('D:D', 15)  # Υπηρεσία
    worksheet.set_column('E:E', 35)  # Σημειώσεις
    
    # Headers
    headers = ['Ημερομηνία', 'Ώρα', 'Διάρκεια', 'Υπηρεσία', 'Σημειώσεις']
    for col, header in enumerate(headers):
        worksheet.write(3, col, header, header_format)
    print("So far so good3:")
    # Δεδομένα
    row = 4
    for appt in appointments:
        worksheet.write(row, 0, appt.datetime, center_format) # .strftime('%d/%m/%Y') 
        worksheet.write(row, 1, appt.datetime, center_format) # .strftime('%H:%M')
        worksheet.write(row, 2, f"{appt.duration}'", center_format)
        worksheet.write(row, 3, appt.services or '-', cell_format)
        worksheet.write(row, 4, appt.notes or '-', cell_format)
        row += 1
    
    # Σύνοψη
    if appointments:
        row += 1
        summary_format = workbook.add_format({
            'bold': True,
            'bg_color': '#E3F2FD',
            'border': 1
        })
        
        worksheet.merge_range(f'A{row+1}:C{row+1}', 
                            f'Σύνολο Ραντεβού: {len(appointments)}', 
                            summary_format)
    
    workbook.close()
    return os.path.abspath(filename)
