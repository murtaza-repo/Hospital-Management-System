# App imports #

from flask import Flask, render_template, redirect, url_for,request, flash, session
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import logging

###########


# App cofig #

app = Flask(__name__)
app.secret_key = 'twhkehberuoraddgcfadsvtw'
app.config.from_pyfile('config.cfg')
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

###########

# Database Models

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dept = db.Column(db.String(50), nullable=False)
    userId = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    admin = db.Column(db.Boolean, default=False)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ssnID = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    doj = db.Column(db.Date, nullable=False)
    type_of_bed = db.Column(db.String(30), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(30), nullable=False)
    state = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(30), default='Active', nullable=False)

    # medicines = db.relationship("Medicine_Issued", back_populates="medicine")
    # diagnosis = db.relationship("Diagnostics", secondary="diagnosis_performed", backref="patient", lazy="dynamic")

    def __repr__(self):
        return '<Patient %r>' % self.name

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    quantity_available = db.Column(db.Integer, nullable=False)
    rate_of_medicine = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return 'Medicine %r' % self.name

class Medicine_Issued(db.Model):
    patient_id = db.Column(db.Integer,db.ForeignKey('patient.id'), primary_key=True)
    medicine_id = db.Column(db.Integer,db.ForeignKey('medicine.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)

    patients = db.relationship("Patient", backref="medicine_issued")
    medicines = db.relationship("Medicine", backref="medicine_issued")

class Diagnostics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_name = db.Column(db.String(50), unique=True, nullable=False)
    test_charges = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return 'Diagnosis %r' % self.test_name

class DiagnosisPerformed(db.Model):
    patient_id = db.Column(db.Integer,db.ForeignKey('patient.id'), primary_key=True)
    test_id = db.Column(db.Integer,db.ForeignKey('diagnostics.id'), primary_key=True)
    
    patients = db.relationship("Patient", backref="diagnosis_performed")
    diagnostics = db.relationship("Diagnostics", backref="diagnosis_performed")

# App routes 
@app.route('/')
def index():
    if 'loggedin' in session:
        return redirect(url_for('home'))

    return render_template('index.html', index=True)

@app.route('/home')
def home():
    if 'loggedin' in session:
        id = session['userId']
        user = Users.query.get_or_404(id)
        return render_template("home.html", user=user, home=True)
    else:
        return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    if 'loggedin' in session:
        return redirect(url_for('home'))
    # Check if "userId" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'userId' in request.form and 'password' in request.form:
        # Create variables for easy access
        userId = request.form['userId']
        password = request.form['password']
        # Check if account exists using MySQL
        user = Users.query.filter(Users.userId==userId).first()
        # If account exists in accounts table in out database
        if user:
            passwd = bcrypt.check_password_hash(user.password, password)
            if passwd:
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['userId'] = user.id
                session['admin'] = user.admin
                # Redirect to home page
                return redirect(url_for('home'))
            else:
                flash('Incorrect password!', category='error')
                return redirect(url_for('index'))
        else:
            # Account doesnt exist or username/password incorrect
            flash('user not found!', category='error')
            return redirect(url_for('index'))

@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('userId', None)
    # Redirect to login page
    return redirect(url_for('index'))


@app.route('/registerPatient', methods=['GET','POST'])
def registerPatient():
    if 'loggedin' in session:
        if request.method == 'POST' and 'ssnID' in request.form \
            and 'name' in request.form and 'age' in request.form and \
            'doj' in request.form and 'type_of_bed' in request.form and \
            'address' in request.form and 'state' in request.form and 'city' in request.form:
            
            ssnID = request.form['ssnID']
            name = request.form['name']
            age = request.form['age']
            doj = date.fromisoformat(request.form['doj'])
            type_of_bed = request.form['type_of_bed']
            address = request.form['address']
            state = request.form['state']
            city = request.form['city']

            patient = Patient(ssnID=ssnID, name=name, age=age, doj=doj, type_of_bed=type_of_bed, address=address, state=state, city=city)
            db.session.add(patient)
            db.session.commit()
            flash('Patient registration initiated successfully', category='info')
            return redirect(url_for('home'))
        else:
            return render_template('regPatient.html')
    else:
        flash('Please Sign-in first!', category='warning')
        return redirect(url_for('index'))

@app.route('/managePatient', methods=['GET', 'POST'])
def managePatient():
    if 'loggedin' in session:
        if request.method == 'POST' and 'ssnID' in request.form:
            ssnID = request.form['ssnID']
            patient = Patient.query.filter(Patient.ssnID == ssnID).first()
            if patient:
                return render_template('mngPatient.html', patient=patient)
            else:
                flash('Patient with SSN ID not found!', category='warning')
                return redirect(url_for('managePatient'))
        else:
            return render_template('mngPatient.html')
    else:
        flash('Please Sign-in first!', category='warning')
        return redirect(url_for('index'))

@app.route('/editPatient/<int:id>', methods=['POST'])
def editPatient(id):
    if 'loggedin' in session:
        if request.method == 'POST'and 'ssnID' in request.form \
            and 'name' in request.form and 'age' in request.form and \
            'doj' in request.form and 'type_of_bed' in request.form and \
            'address' in request.form and 'state' in request.form and 'city' in request.form:

            patient = Patient.query.get_or_404(id)
            patient.ssnID = request.form['ssnID']
            patient.name = request.form['name']
            patient.age = request.form['age']
            patient.doj = date.fromisoformat(request.form['doj'])
            patient.type_of_bed = request.form['type_of_bed']
            patient.address = request.form['address']
            patient.state = request.form['state']
            patient.city = request.form['city']
            db.session.commit()
            flash('Patient update initiated successfully', category='info')
            return redirect(url_for('managePatient'))
        else:
            flash('Please check the entered data', category='warning')
            return redirect(url_for('managePatient'))
    else:
        flash('Please Sign-in first!', category='warning')
        return redirect(url_for('index'))

@app.route('/deletePatient/<int:id>')
def deletePatient(id):
    if 'loggedin' in session:
        patient = Patient.query.get_or_404(id)
        db.session.delete(patient)
        db.session.commit()
        flash('Patient deletion initiated successfully', category='info')
        return redirect(url_for('managePatient'))
    else:
        flash('Please Sign-in first!', category='warning')
        return redirect(url_for('index'))

@app.route('/viewPatients')
def viewPatients():
    if 'loggedin' in session:
        all_patients = Patient.query.all()
        return render_template('viewPatients.html', all_patients=all_patients)
    else:
        flash('Please Sign-in first!', category='warning')
        return redirect(url_for('index'))

@app.route('/medicineIssued', methods=['GET', 'POST'])
def medicineIssued():
    if 'loggedin' in session:
        all_medicines = Medicine.query.all()

        if request.method == 'POST' and 'ssnID' in request.form:
            ssnID = request.form['ssnID']
            patient = Patient.query.filter(Patient.ssnID == ssnID).first()
            if patient:
                medIssued = Medicine_Issued.query.filter(Medicine_Issued.patient_id==patient.id).all()
                medlist = list()
                for medId in medIssued:
                    med = Medicine.query.filter(Medicine.id==medId.medicine_id).first()
                    medData = {
                        'obj': med,
                        'quantity': medId.quantity
                    }
                    medlist.append(medData)
                return render_template('medIssued.html', patient=patient, all_medicines=all_medicines, medlist=medlist, medIssued=medIssued)
            else:
                flash('Patient with SSN ID not found!', category='warning')
                return redirect(url_for('medicineIssued'))
        elif request.method == 'POST' and 'patientId' in request.form and 'medicineId' in request.form and 'quantity' in request.form:
            patientId = request.form['patientId']
            medicineId = request.form['medicineId']
            quantity = int(request.form['quantity'])

            medIssued = Medicine_Issued.query.filter(Medicine_Issued.patient_id==patientId, Medicine_Issued.medicine_id == medicineId).first()
            medicine = Medicine.query.filter(Medicine.id == medicineId).first()
            if medIssued:
                # flash('Medicine already issued! Update quantity if you want...', category="warning")
                if quantity > medicine.quantity_available:
                    flash(f'Requested quantity not available! Quantity Available: {medicine.quantity_available}', category = 'info')
                    return redirect(url_for('medicineIssued'))
                else:
                    medIssued.quantity += quantity
                    medicine.quantity_available -= quantity
                    db.session.commit()
                    flash('Medicine issued successfully', category = 'info')
                    return redirect(url_for('medicineIssued'))
            else: 
                if quantity > medicine.quantity_available: 
                    flash(f'Requested quantity not available! \n\n Quantity Available: {medicine.quantity_available}', category = 'info')
                    return redirect(url_for('medicine_issued'))
                else:
                    medicine.quantity_available -= quantity
                    medIssue = Medicine_Issued(patient_id = patientId, medicine_id = medicineId, quantity = quantity)
                    db.session.add(medIssue)
                    db.session.commit()
                    flash('Medicine issued successfully', category = 'info')
                    return redirect(url_for('medicineIssued'))
        else:
            return render_template('medIssued.html')
    else:
        flash('Please Sign-in first!', category='warning')
        return redirect(url_for('index'))

@app.route('/updateQuant/<int:id>', methods=['POST'])
def updateQuant(id):
    if 'loggedin' in session:
        if request.method == 'POST' and 'patientId' in request.form and 'quantity' in request.form:
            patient_Id = request.form['patientId']
            quantity = int(request.form['quantity'])
            
            medIssued = Medicine_Issued.query.filter(Medicine_Issued.patient_id==patient_Id, Medicine_Issued.medicine_id == id).first() 
            medicine = Medicine.query.filter(Medicine.id == medIssued.medicine_id).first()
            if medIssued.quantity > quantity:
                medicine.quantity_available += (medIssued.quantity - quantity)
                medIssued.quantity = quantity
                db.session.commit()
                flash('Medicine quantity update initiated succesfully', category='info')
                return redirect(url_for('medicineIssued'))
            else:
                medicine.quantity_available -= (quantity - medIssued.quantity)    
                medIssued.quantity = quantity
                db.session.commit()
                flash('Medicine quantity update initiated succesfully', category='info')
                return redirect(url_for('medicineIssued'))
        else:
            flash('Please check the inputs!', category='warning')
            return redirect(url_for('medicineIssued'))
    else:
       flash('Please Sign-in first!', category='warning')
       return redirect(url_for('index')) 
       
@app.route('/removeMedicine/<int:pid>,<int:mid>')
def removeMedicine(pid, mid):
    if 'loggedin' in session:
        med = Medicine_Issued.query.filter(Medicine_Issued.patient_id==pid,Medicine_Issued.medicine_id == mid).first()
        medicine = Medicine.query.filter(Medicine.id == mid).first()
        medicine.quantity_available += med.quantity
        db.session.delete(med)
        db.session.commit()
        flash('Medicine removal initiated successfully', category='info')
        return redirect(url_for('medicineIssued'))
    else:
       flash('Please Sign-in first!', category='warning')
       return redirect(url_for('index')) 

@app.route('/medicineDetails', methods=['GET','POST'])
def medicineDetails():
    if 'loggedin' in session:
        all_medicines = Medicine.query.all()
        
        if request.method == 'POST' and 'name' in request.form \
            and 'quantity' in request.form and 'rate' in request.form:

            name = request.form['name']
            quantity_available = request.form['quantity']
            rate_of_medicine = request.form['rate']

            med = Medicine(name=name, quantity_available = quantity_available, rate_of_medicine = rate_of_medicine)
            db.session.add(med)
            db.session.commit()
            flash('Medicine added successfully', category='info')
            return redirect(url_for('medicineDetails'))
        else:
            return render_template('medDetails.html', all_medicines=all_medicines)
    else:
        flash('Please Sign-in first!', category='warning')
        return redirect(url_for('index'))

@app.route('/editMedicine/<int:id>', methods=['POST'])
def editMedicine(id):
    if 'loggedin' in session:
        if request.method == 'POST'and 'name' in request.form \
            and 'quantity' in request.form and 'rate' in request.form:

            med = Medicine.query.get_or_404(id)
            med.name = request.form['name']
            med.quantity_available = request.form['quantity']
            med.rate_of_medicine = request.form['rate']
            db.session.commit()
            flash('Medicine update initiated successfully', category='info')
            return redirect(url_for('medicineDetails'))
        else:
            flash('Please check the entered data', category='warning')
            return redirect(url_for('medicineDetails'))
    else:
        flash('Please Sign-in first!', category='warning')
        return redirect(url_for('index'))

@app.route('/deleteMedicine/<int:id>')
def deleteMedicine(id):
    if 'loggedin' in session:
        med = Medicine.query.get_or_404(id)
        db.session.delete(med)
        db.session.commit()
        flash('Medicine deletion initiated successfully', category='info')
        return redirect(url_for('medicineDetails'))
    else:
        flash('Please Sign-in first!', category='warning')
        return redirect(url_for('index'))

@app.route('/diagDetails', methods=['GET', 'POST'])
def diagDetails():
    if 'loggedin' in session:
        all_diagnostics = Diagnostics.query.all()
        
        if request.method == 'POST' and 'name' in request.form \
            and 'charge' in request.form:

            test_name = request.form['name']
            test_charges = request.form['charge']

            diag = Diagnostics(test_name=test_name, test_charges=test_charges)
            db.session.add(diag)
            db.session.commit()
            flash('Diagnosis added successfully', category='info')
            return redirect(url_for('diagDetails'))
        else:
            return render_template('diagDetails.html', all_diagnostics=all_diagnostics)
    else:
        flash('Please Sign-in first!', category='warning')
        return redirect(url_for('index'))    

@app.route('/editDiagnosis/<int:testId>', methods=['POST'])
def editDiagnosis(testId):
    if 'loggedin' in session:
        if request.method == 'POST'and 'name' in request.form \
            and 'charge' in request.form:

            diag = Diagnostics.query.get_or_404(testId)
            diag.test_name = request.form['name']
            diag.test_charges = request.form['charge']
            db.session.commit()
            flash('Diagnostics update initiated successfully', category='info')
            return redirect(url_for('diagDetails'))
        else:
            flash('Please check the entered data', category='warning')
            return redirect(url_for('diagDetails'))
    else:
        flash('Please Sign-in first!', category='warning')
        return redirect(url_for('index'))

@app.route('/deleteDiagnosis/<int:testId>')
def deleteDiagnosis(testId):
    if 'loggedin' in session:
        diag = Diagnostics.query.get_or_404(testId)
        db.session.delete(diag)
        db.session.commit()
        flash('Diagnostics deletion initiated successfully', category='info')
        return redirect(url_for('diagDetails'))
    else:
        flash('Please Sign-in first!', category='warning')
        return redirect(url_for('index'))


@app.route('/diagPerformed', methods=['GET', 'POST'])
def diagPerformed():
    if 'loggedin' in session:
        all_diagnosis = Diagnostics.query.all()
        
        if request.method == 'POST' and 'ssnID' in request.form:
            ssnID = request.form['ssnID']
            patient = Patient.query.filter(Patient.ssnID == ssnID).first()
            if patient:
                diagPerform = DiagnosisPerformed.query.filter(DiagnosisPerformed.patient_id == patient.id).all()
                diaglist = list()
                for diag in diagPerform:
                    diagObj = Diagnostics.query.filter(Diagnostics.id == diag.test_id).first()
                    diagData = {
                        'id': diagObj.id,
                        'name': diagObj.test_name,
                        'charges': diagObj.test_charges
                    }
                    diaglist.append(diagData)
                
                return render_template('diagPerformed.html', patient=patient, all_diagnosis=all_diagnosis, diagPerform=diagPerform, diaglist=diaglist)
            else:
                flash('Patient with SSN ID not found!', category='warning')
                return redirect(url_for('medicineIssued'))
        elif request.method=='POST' and 'patientId' in request.form and 'testId' in request.form:
            patientId = request.form['patientId']
            testId = request.form['testId']

            is_diagPerformed = DiagnosisPerformed.query.filter(DiagnosisPerformed.patient_id == patientId, DiagnosisPerformed.test_id == testId).first()
            if is_diagPerformed:
                flash('Test already performed!', category='warning')
                return redirect(url_for('diagPerformed'))
            else:
                performTest = DiagnosisPerformed(patient_id=patientId, test_id=testId)
                db.session.add(performTest)
                db.session.commit()
                flash('Diagnosis test initiated successfully', category='info')
                return redirect(url_for('diagPerformed'))
        else:
            return render_template('diagPerformed.html')
    else:
        flash('Please Sign-in first!', category='warning')
        return redirect(url_for('index'))

@app.route('/removeTest/<int:pid>,<int:tid>')
def removeTest(pid, tid):
    if 'loggedin' in session:
        diag = DiagnosisPerformed.query.filter(DiagnosisPerformed.patient_id == pid, DiagnosisPerformed.test_id == tid).first()
        db.session.delete(diag)
        db.session.commit()
        flash('Diagnosis removal initiated successfully', category='info')
        return redirect(url_for('diagPerformed'))
    else:
       flash('Please Sign-in first!', category='warning')
       return redirect(url_for('index'))         


@app.route('/genBill', methods=['GET', 'POST'])
def genBill():
    if 'loggedin' in session:
        #overall total parameters
        room_total = 0
        pharmacy_total = 0
        diagnostics_total = 0  
        
        #Room charges
        general_rate = 2000 #per day
        semi_rate = 4000 #per day
        single_rate = 8000 #per day

        if request.method == 'POST' and 'ssnID' in request.form:
            ssnID = request.form['ssnID']
            patient = Patient.query.filter(Patient.ssnID == ssnID).first()
            if patient:
                patientData = list()
                days = (datetime.now().date()-date.fromisoformat(str(patient.doj))).days + 1
                
                if patient.type_of_bed == 'General':
                    room_total += (general_rate*days)
                elif patient.type_of_bed == 'Semi':
                    room_total += (semi_rate*days)
                else:
                    room_total += (single_rate*days)

                pobj = {'ssnID' : patient.ssnID, 'name': patient.name, 'age': patient.age, 
                        'address': (patient.address+", "+patient.city+", "+ patient.state), 
                        'doj': patient.doj, 'date_of_discharge': datetime.utcnow().date(), 
                        'type_of_bed': patient.type_of_bed, 'number_of_days': days, 
                        'room_charges': room_total}
                patientData.append(pobj)

                print(patientData)

                med_issued = Medicine_Issued.query.filter(Medicine_Issued.patient_id == patient.id).all()
                diag_performed = DiagnosisPerformed.query.filter(DiagnosisPerformed.patient_id == patient.id).all()
                medData = list()
                diagData = list()
                for med in med_issued:
                    medicine = Medicine.query.filter(Medicine.id == med.medicine_id).first()
                    obj = { 'name': medicine.name, 'quantity': med.quantity, 
                            'rate': medicine.rate_of_medicine, 
                            'amount': (med.quantity * medicine.rate_of_medicine) }
                    medData.append(obj)
                
                for total1 in medData:
                    pharmacy_total+=total1['amount']
                
                for diag in diag_performed:
                    diagnos = Diagnostics.query.filter(Diagnostics.id == diag.test_id).first()
                    output = {'test_name': diagnos.test_name, 'test_charges': diagnos.test_charges}
                    diagData.append(output)

                for total2 in diagData:
                    diagnostics_total+=total2['test_charges']

                return render_template('genBill.html', patient=patient, patientData=patientData, medData=medData, pharmacy_total=pharmacy_total, 
                                        diagData = diagData, diagnostics_total=diagnostics_total)
            else:
                flash('Patient with SSN ID not found!', category='warning')
                return redirect(url_for('genBill'))

        return render_template('genBill.html')
    else:
       flash('Please Sign-in first!', category='warning')
       return redirect(url_for('index'))


@app.route('/discharge', methods=['POST'])
def discharge():
    if 'loggedin' in session:
        if request.method == 'POST' and 'ssnID' in request.form:
            ssnID = request.form['ssnID']
            patient = Patient.query.filter(Patient.ssnID == ssnID).first()
            patient.status = 'Discharged'
            db.session.commit()
            flash('Patient discharge intiated successfully', category='info')
            return redirect(url_for('home'))
        else:
            flash('Try again!', category='warning')
            return redirect(url_for('home'))
    else:
       flash('Please Sign-in first!', category='warning')
       return redirect(url_for('index'))
########### 

# App Execution Main #
if __name__=='__main__':
    app.run()

###########
