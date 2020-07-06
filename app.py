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
    diagnosis = db.relationship("Diagnostics", secondary="diagnosis_performed", backref="patient", lazy="dynamic")

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
    test_Id = db.Column(db.Integer, primary_key=True)
    test_name = db.Column(db.String(50), unique=True, nullable=False)
    test_charges = db.Column(db.Float, nullable=False)

db.Table('diagnosis_performed',
	db.Column('patient_Id', db.Integer, db.ForeignKey('patient.id')),
	db.Column('test_Id', db.Integer, db.ForeignKey('diagnostics.test_Id'))
	)

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
                flash('Patient with that SSN ID not found!', category='warning')
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
###########


# App Execution Main #
if __name__=='__main__':
    app.run(debug=True)

###########
