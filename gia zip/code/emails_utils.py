# -*- coding: utf-8 -*-
# Λειτουργίες για αποστολή email υπενθυμίσεων
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import models


class EmailSender:
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587,
                 email="", password=""):
        """
        Αρχικοποίηση του EmailSender
        ΜΗΝ ΒΑΖΕΤΕ ΠΟΤΕ PASSWORDS ΣΤΟΝ ΚΩΔΙΚΑ!
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password

    def send_reminder(self, recipient_email, customer_name, appointment_time, services):
        """Στέλνει email υπενθύμισης για ραντεβού"""
        try:
            # Δημιουργία μηνύματος
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Υπενθύμιση Ραντεβού - Ο Ψαλιδοχέρης'
            msg['From'] = self.email
            msg['To'] = recipient_email

            # Μορφοποίηση ώρας
            appointment_datetime_obj = datetime.strptime(appointment_time, "%Y-%m-%d %H:%M")
            time_str = appointment_datetime_obj.strftime('%H:%M')
            date_str = appointment_datetime_obj.strftime('%d/%m/%Y')
            day_name = appointment_datetime_obj.strftime('%A')

            # HTML περιεχόμενο
            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                  <h2 style="color: #2196F3;">Υπενθύμιση Ραντεβού</h2>

                  <p>Αγαπητέ/ή <strong>{customer_name}</strong>,</p>

                  <p>Σας υπενθυμίζουμε ότι έχετε ραντεβού:</p>

                  <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Ημερομηνία:</strong> {day_name} {date_str}</p>
                    <p style="margin: 5px 0;"><strong>Ώρα:</strong> {time_str}</p>
                    <p style="margin: 5px 0;"><strong>Υπηρεσία:</strong> {services}</p>
                  </div>

                  <p>Παρακαλούμε να είστε στο κατάστημά μας 5 λεπτά πριν την προγραμματισμένη ώρα.</p>

                  <p>Σε περίπτωση που χρειάζεται να ακυρώσετε ή να αλλάξετε το ραντεβού σας, 
                     παρακαλούμε επικοινωνήστε μαζί μας το συντομότερο δυνατό.</p>

                  <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">

                  <p style="color: #666; font-size: 14px;">
                    Με εκτίμηση,<br>
                    <strong>Hairway to heaven</strong><br>
                    Τηλέφωνο: 210-1234567<br>
                    Διεύθυνση: Οδός Κομμώσεων 123, Αθήνα
                  </p>
                </div>
              </body>
            </html>
            """

            # Plain text εναλλακτικό
            text = f"""
            Υπενθύμιση Ραντεβού

            Αγαπητέ/ή {customer_name},

            Σας υπενθυμίζουμε ότι έχετε ραντεβού:

            Ημερομηνία: {day_name} {date_str}
            Ώρα: {time_str}
            Υπηρεσία: {services}

            Παρακαλούμε να είστε στο κατάστημά μας 5 λεπτά πριν την προγραμματισμένη ώρα.

            Με εκτίμηση,
            Hairway to heaven
            """

            # Προσθήκη των δύο εκδοχών
            part1 = MIMEText(text, 'plain', 'utf-8')
            part2 = MIMEText(html, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)

            # Σύνδεση και αποστολή
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)

            return True, "Το email στάλθηκε επιτυχώς!"

        except Exception as e:
            return False, f"Σφάλμα αποστολής: {str(e)}"

    def send_reminders_for_date(self, date):
        """Στέλνει υπενθυμίσεις σε όλους τους πελάτες που έχουν ραντεβού την συγκεκριμένη ημέρα"""
        appointments = models.Appointment.get_by_date(date)

        if not appointments:
            return 0, "Δεν υπάρχουν ραντεβού για αυτή την ημερομηνία"

        success_count = 0
        failed_count = 0
        failed_messages = []

        for appt in appointments:
            success, message = self.send_reminder(
                appt.customer_email,
                appt.customer_name,
                appt.datetime,
                appt.services or "Ραντεβού"
            )

            if success:
                success_count += 1
            else:
                failed_count += 1
                failed_messages.append(f"{appt.customer_name}: {message}")

        # Δημιουργία μηνύματος αποτελέσματος
        result_msg = f"Στάλθηκαν {success_count} από {len(appointments)} emails."
        if failed_count > 0:
            result_msg += f"\n\nΑποτυχίες ({failed_count}):\n"
            result_msg += "\n".join(failed_messages)

        return success_count, result_msg


def test_email_connection(smtp_server, smtp_port, email, password):
    """Δοκιμή σύνδεσης με τον email server"""
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email, password)
        return True, "Επιτυχής σύνδεση!"
    except Exception as e:
        return False, f"Σφάλμα: {str(e)}"
