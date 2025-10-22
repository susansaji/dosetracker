from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mail import Mail, Message
import mysql.connector
import schedule
import time
import threading
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 🔹 MySQL Configuration
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Susan2327@2005",
    database="medicine_reminder"
)

# 🔹 Email Configuration (Gmail)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'dosetracker0@#gmail.com'
app.config['MAIL_PASSWORD'] = 'dosetracker2025'  # Gmail App Password
mail = Mail(app)

# =================================
# USER REGISTRATION
# =================================
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data['name']
    email = data['email']
    password = data['password']

    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)',
        (name, email, password)
    )
    db.commit()
    cursor.close()
    return jsonify({'message': 'User registered successfully!'})

# =================================
# ADD MEDICINE (API)
# =================================
@app.route('/add_medicine', methods=['POST'])
def add_medicine():
    data = request.get_json()
    user_id = data['user_id']
    medicine_name = data['medicine_name']
    dosage = data['dosage']
    start_date = data['start_date']
    end_date = data['end_date']
    times_per_day = data['times_per_day']

    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'INSERT INTO medicines (user_id, medicine_name, dosage, start_date, end_date, times_per_day) VALUES (%s, %s, %s, %s, %s, %s)',
        (user_id, medicine_name, dosage, start_date, end_date, times_per_day)
    )
    db.commit()
    cursor.close()
    return jsonify({'message': 'Medicine added successfully!'})

# =================================
# ADD MEDICINE (FORM SUBMISSION)
# =================================
@app.route('/add_medicine_form', methods=['POST'])
def add_medicine_form():
    medicine_name = request.form.get('medicine_name')
    dosage = request.form.get('dosage')
    food_time = request.form.get('food_time')  # Before / After
    schedule_time = request.form.get('schedule_time')  # Morning / Noon / Night

    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'INSERT INTO medicines (medicine_name, dosage, food_time, schedule_time) VALUES (%s, %s, %s, %s)',
        (medicine_name, dosage, food_time, schedule_time)
    )
    db.commit()
    cursor.close()
    return jsonify({'message': 'Medicine added successfully from form!'})

# =================================
# GET ALL REMINDERS
# =================================
@app.route('/reminders', methods=['GET'])
def get_reminders():
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT * FROM reminders')
    reminders = cursor.fetchall()
    cursor.close()
    return jsonify(reminders)

# =================================
# EMAIL REMINDER SCHEDULER
# =================================
def send_email_reminder(to_email, subject, message):
    msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[to_email])
    msg.body = message
    mail.send(msg)

def check_reminders():
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT r.reminder_id, r.reminder_datetime, r.status, u.email, m.medicine_name, m.dosage "
        "FROM reminders r "
        "JOIN medicines m ON r.medicine_id=m.medicine_id "
        "JOIN users u ON m.user_id=u.user_id "
        "WHERE r.status='Pending'"
    )
    reminders = cursor.fetchall()
    now = datetime.now()

    for r in reminders:
        reminder_time = r['reminder_datetime']
        if now >= reminder_time:
            subject = f"Time for your medicine: {r['medicine_name']}"
            message = f"Please take your medicine {r['medicine_name']} ({r['dosage']}) now."
            send_email_reminder(r['email'], subject, message)
            cursor.execute("UPDATE reminders SET status='Sent' WHERE reminder_id=%s", (r['reminder_id'],))
            db.commit()
    cursor.close()

# Run scheduler every 1 minute
def run_scheduler():
    schedule.every(1).minutes.do(check_reminders)
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()

# =================================
# RUN SERVER
# =================================
if __name__ == '__main__':
    app.run(debug=True)