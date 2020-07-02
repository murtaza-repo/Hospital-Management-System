# App imports #

from flask import Flask, render_template, redirect, url_for,request, flash, session
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
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
    typeOfBed = db.Column(db.String(30), nullable=False)
    adress = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(30), nullable=False)
    state = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(30), nullable=False)

###########

# App routes 
@app.route('/')
def index():
    if 'loggedin' in session:
        return redirect(url_for('home'))

    return render_template('index.html')

@app.route('/home')
def home():
    if 'loggedin' in session:
        id = session['userId']
        user = Users.query.get_or_404(id)
        return render_template("home.html", user=user)
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

###########


# App Execution Main #
if __name__=='__main__':
    app.run(debug=True)

###########