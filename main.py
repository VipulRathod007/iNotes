from flask import Flask, session, url_for, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_mail import Mail

params, isLoggedIn = None, False
with open('config.json', 'r') as fileObj:
    params = json.load(fileObj)

app = Flask(__name__)
app.secret_key = 'super-vip-key'
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = params['database']['local_db_uri']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['social-links']['mailAddr'],
    MAIL_PASSWORD=params['social-links']['mailPass']
)
mail = Mail(app)


class LoginData(db.Model):
    __tablename__ = 'loginData'
    entryid = db.Column(db.Integer, primary_key=True)
    mailid = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(500), unique=False)
    date = db.Column(db.String(25), unique=False)

    def __init__(self, mail, passwd, date):
        self.mailid = mail
        self.password = passwd
        self.date = date


class UserData(db.Model):
    __tablename__ = 'userdata'
    entryid = db.Column(db.Integer, primary_key=True)
    mailid = db.Column(db.String(50), unique=True)
    notetitle = db.Column(db.String(50), unique=True)
    notedesc = db.Column(db.String(500), unique=False)
    notedate = db.Column(db.String(25), unique=False)
    date = db.Column(db.String(25), unique=False)

    def __init__(self, title, desc, notedate, date, mail):
        self.notetitle = title
        self.notedesc = desc
        self.notedate = notedate
        self.date = date
        self.mailid = mail


@app.route('/')
def home():
    return render_template('home.html', params=params, isLoggedIn=isLoggedIn)


@app.route('/login', methods=['POST', 'GET'])
def login():
    global isLoggedIn
    error = False
    if request.method == 'POST':
        if 'user' in session and isLoggedIn:
            return render_template('service.html', params=params, isLoggedIn=isLoggedIn)
        else:
            userMail = request.form.get('email')
            userPass = request.form.get('password')
            result = LoginData.query.filter_by(mailid=userMail, password=userPass).count()
            if result:
                isLoggedIn = True
                error = False
                session['user'] = userMail
                return redirect(url_for('service'))
            else:
                isLoggedIn = False
                error = True
                return render_template('login.html', params=params, isLoggedIn=isLoggedIn, error=error)
    else:
        error = False
        return render_template('login.html', params=params, isLoggedIn=isLoggedIn, error=error)


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    global isLoggedIn
    found = False
    if request.method == 'POST':
        if 'user' in session and isLoggedIn:
            return redirect(url_for('service.html'))
        else:
            userMail = request.form.get('email')
            result = LoginData.query.filter_by(mailid=userMail).count()
            if result:
                found = True
                return render_template('signup.html', params=params, isLoggedIn=isLoggedIn, found=found)
            else:
                userPass = request.form.get('password')
                entry = LoginData(userMail, userPass, datetime.now())
                db.session.add(entry)
                db.session.commit()
                isLoggedIn = True
                session['user'] = userMail
                return redirect(url_for('service'))
    else:
        found = False
        return render_template('signup.html', params=params, isLoggedIn=isLoggedIn, found=found)


@app.route('/edit/<int:noteid>', methods=['POST', 'GET'])
def edit(noteid):
    if 'user' in session:
        entry = UserData.query.filter_by(entryid=noteid).first()
        if request.method == 'GET':
            return render_template('edit.html', params=params, isLoggedIn=isLoggedIn, entry=entry)
        else:
            entry.notetitle = request.form.get('title')
            entry.notedesc = request.form.get('desc')
            entry.notedate = request.form.get('date')
            entry.date = datetime.now()
            db.session.commit()
            return redirect(url_for('service'))
    else:
        return redirect(url_for('home'))

@app.route('/delete/<int:id>')
def delete(id):
    if 'user' in session:
        deleteEntry = UserData.query.filter_by(entryid=id).first()
        db.session.delete(deleteEntry)
        db.session.commit()
        return redirect(url_for('service'))


@app.route('/logout')
def logout():
    session.pop('user', None)
    isLoggedIn = False
    return render_template('home.html', params=params, isLoggedIn=isLoggedIn)


@app.route('/contact', methods=['POST', 'GET'])
def contact():
    sent = False
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        mail.send_message(subject+' From '+name, sender=email, recipients=[params['social-links']['mailAddr']], body=message)
        sent = True
        return render_template('contact.html', params=params, isLoggedIn=isLoggedIn, sent=sent)
    else:
        return render_template('contact.html', params=params, isLoggedIn=isLoggedIn, sent=sent)


@app.route('/service', methods=['POST', 'GET'])
def service():
    if 'user' in session:
        if request.method == 'POST':
            noteTitle = request.form.get('title')
            noteDesc = request.form.get('desc')
            noteDate = request.form.get('date')
            entry = UserData(noteTitle, noteDesc, noteDate, datetime.now(), session['user'])
            db.session.add(entry)
            db.session.commit()
            return redirect(url_for('service'))
        else:
            notes = UserData.query.filter_by(mailid=session['user'])
            return render_template('service.html', params=params, isLoggedIn=isLoggedIn, notes=notes)
    else:
        return render_template('signup.html', params=params, isLoggedIn=isLoggedIn)


app.run(debug=True)
