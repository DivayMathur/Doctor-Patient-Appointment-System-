from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_db, init_db
app = Flask(__name__)
app.secret_key = 'dpas_secret_2024'

def query(sql, args=(), one=False, commit=False):
    db = get_db()
    cur = db.execute(sql, args)
    if commit:
        db.commit()
        db.close()
        return None
    result = cur.fetchone() if one else cur.fetchall()
    db.close()
    return result

@app.route('/')
def index():
    recent = query(
        'SELECT a.id, p.name AS patient_name, d.name AS doctor_name, '
        'a.appointment_date, a.appointment_time, a.status '
        'FROM appointments a JOIN patients p ON a.patient_id=p.id '
        'JOIN doctors d ON a.doctor_id=d.id ORDER BY a.id DESC LIMIT 5'
    )
    return render_template('index.html',
        total_doctors=query('SELECT COUNT(*) FROM doctors', one=True)[0],
        total_patients=query('SELECT COUNT(*) FROM patients', one=True)[0],
        total_appointments=query('SELECT COUNT(*) FROM appointments', one=True)[0],
        scheduled=query("SELECT COUNT(*) FROM appointments WHERE status='Scheduled'", one=True)[0],
        recent_appointments=recent)

@app.route('/doctors')
def doctors_list():
    s = request.args.get('search', '')
    doctors = query('SELECT * FROM doctors WHERE name LIKE ? OR specialization LIKE ? ORDER BY name', (f'%{s}%', f'%{s}%'))
    return render_template('doctors/list.html', doctors=doctors, search=s)

@app.route('/doctors/add', methods=['GET', 'POST'])
def doctors_add():
    if request.method == 'POST':
        f = request.form
        query('INSERT INTO doctors (name, specialization, phone, email, available_days) VALUES (?, ?, ?, ?, ?)',
              (f['name'], f['specialization'], f['phone'], f['email'], f['available_days']), commit=True)
        flash('Doctor added successfully!', 'success')
        return redirect(url_for('doctors_list'))
    return render_template('doctors/add.html')

@app.route('/doctors/<int:id>')
def doctors_detail(id):
    doctor = query('SELECT * FROM doctors WHERE id = ?', (id,), one=True)
    appointments = query('SELECT a.*, p.name AS patient_name FROM appointments a '
                         'JOIN patients p ON a.patient_id=p.id WHERE a.doctor_id=?', (id,))
    return render_template('doctors/detail.html', doctor=doctor, appointments=appointments)

@app.route('/doctors/<int:id>/edit', methods=['GET', 'POST'])
def doctors_edit(id):
    doctor = query('SELECT * FROM doctors WHERE id = ?', (id,), one=True)
    if request.method == 'POST':
        f = request.form
        query('UPDATE doctors SET name=?, specialization=?, phone=?, email=?, available_days=? WHERE id=?',
              (f['name'], f['specialization'], f['phone'], f['email'], f['available_days'], id), commit=True)
        flash('Doctor updated successfully!', 'success')
        return redirect(url_for('doctors_detail', id=id))
    return render_template('doctors/edit.html', doctor=doctor)

@app.route('/doctors/<int:id>/delete', methods=['POST'])
def doctors_delete(id):
    query('DELETE FROM doctors WHERE id = ?', (id,), commit=True)
    flash('Doctor deleted successfully!', 'success')
    return redirect(url_for('doctors_list'))

@app.route('/patients')
def patients_list():
    s = request.args.get('search', '')
    patients = query('SELECT * FROM patients WHERE name LIKE ? OR phone LIKE ? ORDER BY name', (f'%{s}%', f'%{s}%'))
    return render_template('patients/list.html', patients=patients, search=s)

@app.route('/patients/add', methods=['GET', 'POST'])
def patients_add():
    if request.method == 'POST':
        f = request.form
        query('INSERT INTO patients (name, age, gender, phone, email, address) VALUES (?, ?, ?, ?, ?, ?)',
              (f['name'], f['age'], f['gender'], f['phone'], f['email'], f['address']), commit=True)
        flash('Patient added successfully!', 'success')
        return redirect(url_for('patients_list'))
    return render_template('patients/add.html')

@app.route('/patients/<int:id>')
def patients_detail(id):
    patient = query('SELECT * FROM patients WHERE id = ?', (id,), one=True)
    appointments = query('SELECT a.*, d.name AS doctor_name, d.specialization FROM appointments a '
                         'JOIN doctors d ON a.doctor_id=d.id WHERE a.patient_id=?', (id,))
    return render_template('patients/detail.html', patient=patient, appointments=appointments)

@app.route('/patients/<int:id>/edit', methods=['GET', 'POST'])
def patients_edit(id):
    patient = query('SELECT * FROM patients WHERE id = ?', (id,), one=True)
    if request.method == 'POST':
        f = request.form
        query('UPDATE patients SET name=?, age=?, gender=?, phone=?, email=?, address=? WHERE id=?',
              (f['name'], f['age'], f['gender'], f['phone'], f['email'], f['address'], id), commit=True)
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('patients_detail', id=id))
    return render_template('patients/edit.html', patient=patient)

@app.route('/patients/<int:id>/delete', methods=['POST'])
def patients_delete(id):
    query('DELETE FROM patients WHERE id = ?', (id,), commit=True)
    flash('Patient deleted successfully!', 'success')
    return redirect(url_for('patients_list'))

APPT_SELECT = ('SELECT a.*, p.name AS patient_name, d.name AS doctor_name, d.specialization '
               'FROM appointments a JOIN patients p ON a.patient_id=p.id '
               'JOIN doctors d ON a.doctor_id=d.id')

@app.route('/appointments')
def appointments_list():
    status = request.args.get('status', '')
    if status:
        appointments = query(APPT_SELECT + ' WHERE a.status=? ORDER BY a.appointment_date DESC', (status,))
    else:
        appointments = query(APPT_SELECT + ' ORDER BY a.appointment_date DESC')
    return render_template('appointments/list.html', appointments=appointments, status_filter=status)

@app.route('/appointments/add', methods=['GET', 'POST'])
def appointments_add():
    if request.method == 'POST':
        f = request.form
        query('INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, status) '
              'VALUES (?, ?, ?, ?, ?, ?)',
              (f['patient_id'], f['doctor_id'], f['appointment_date'], f['appointment_time'], f['reason'], f['status']),
              commit=True)
        flash('Appointment scheduled successfully!', 'success')
        return redirect(url_for('appointments_list'))
    return render_template('appointments/add.html',
        patients=query('SELECT * FROM patients ORDER BY name'),
        doctors=query('SELECT * FROM doctors ORDER BY name'))

@app.route('/appointments/<int:id>')
def appointments_detail(id):
    appt = query(APPT_SELECT + ', p.phone AS patient_phone WHERE a.id=?', (id,), one=True)
    return render_template('appointments/detail.html', appt=appt)

@app.route('/appointments/<int:id>/edit', methods=['GET', 'POST'])
def appointments_edit(id):
    appt = query('SELECT * FROM appointments WHERE id = ?', (id,), one=True)
    if request.method == 'POST':
        f = request.form
        query('UPDATE appointments SET patient_id=?, doctor_id=?, appointment_date=?, '
              'appointment_time=?, reason=?, status=? WHERE id=?',
              (f['patient_id'], f['doctor_id'], f['appointment_date'], f['appointment_time'], f['reason'], f['status'], id),
              commit=True)
        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('appointments_detail', id=id))
    return render_template('appointments/edit.html', appt=appt,
        patients=query('SELECT * FROM patients ORDER BY name'),
        doctors=query('SELECT * FROM doctors ORDER BY name'))

@app.route('/appointments/<int:id>/delete', methods=['POST'])
def appointments_delete(id):
    query('DELETE FROM appointments WHERE id = ?', (id,), commit=True)
    flash('Appointment deleted successfully!', 'success')
    return redirect(url_for('appointments_list'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
