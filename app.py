from flask import Flask, render_template, request, redirect, send_file
import sqlite3
from reportlab.pdfgen import canvas

app = Flask(__name__)

# DATABASE CREATION
def init_db():

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute('''

    CREATE TABLE IF NOT EXISTS portfolio(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,
        designation TEXT,
        location TEXT,
        contact TEXT,
        summary TEXT,
        education TEXT,
        skills TEXT,
        achievement TEXT,
        project TEXT,
        subject TEXT,
        activities TEXT

    )

    ''')

    conn.commit()
    conn.close()

init_db()

# HOME PAGE
@app.route('/')
def home():
    return render_template('home.html')

# ADMIN LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():

    error = ""

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == 'shorya' and password == '123456':
            return redirect('/dashboard')

        else:
            error = "Invalid Username or Password"

    return render_template('login.html', error=error)

# DASHBOARD
@app.route('/dashboard')
def dashboard():

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute('SELECT * FROM portfolio')
    portfolios = cur.fetchall()

    cur.execute('SELECT COUNT(*) FROM portfolio')
    total = cur.fetchone()[0]

    conn.close()

    return render_template(
        'dashboard.html',
        portfolios=portfolios,
        total=total
    )

# CREATE PORTFOLIO
@app.route('/create', methods=['GET', 'POST'])
def create():

    if request.method == 'POST':

        data = (

            request.form['name'],
            request.form['designation'],
            request.form['location'],
            request.form['contact'],
            request.form['summary'],
            request.form['education'],
            request.form['skills'],
            request.form['achievement'],
            request.form['project'],
            request.form['subject'],
            request.form['activities']

        )

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()

        cur.execute('''

        INSERT INTO portfolio(

            name,
            designation,
            location,
            contact,
            summary,
            education,
            skills,
            achievement,
            project,
            subject,
            activities

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        ''', data)

        conn.commit()
        conn.close()

        return redirect('/dashboard')

    return render_template('create.html')

# VIEW PORTFOLIO
@app.route('/portfolio/<int:id>')
def portfolio(id):

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute(
        'SELECT * FROM portfolio WHERE id=?',
        (id,)
    )

    data = cur.fetchone()

    conn.close()

    return render_template(
        'portfolio.html',
        data=data
    )

# UPDATE PORTFOLIO
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    if request.method == 'POST':

        cur.execute('''

        UPDATE portfolio

        SET

        name=?,
        designation=?,
        location=?,
        contact=?,
        summary=?,
        education=?,
        skills=?,
        achievement=?,
        project=?,
        subject=?,
        activities=?

        WHERE id=?

        ''',

        (

            request.form['name'],
            request.form['designation'],
            request.form['location'],
            request.form['contact'],
            request.form['summary'],
            request.form['education'],
            request.form['skills'],
            request.form['achievement'],
            request.form['project'],
            request.form['subject'],
            request.form['activities'],
            id

        ))

        conn.commit()

        return redirect('/portfolio/' + str(id))

    cur.execute(
        'SELECT * FROM portfolio WHERE id=?',
        (id,)
    )

    data = cur.fetchone()

    conn.close()

    return render_template(
        'update.html',
        data=data
    )

# DELETE PORTFOLIO
@app.route('/delete/<int:id>')
def delete(id):

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute(
        'DELETE FROM portfolio WHERE id=?',
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/dashboard')

# GO LIVE
@app.route('/live/<int:id>')
def live(id):

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute(
        'SELECT * FROM portfolio WHERE id=?',
        (id,)
    )

    data = cur.fetchone()

    conn.close()

    return render_template(
        'live.html',
        data=data
    )

# EXPORT PDF
@app.route('/pdf/<int:id>')
def pdf(id):

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute(
        'SELECT * FROM portfolio WHERE id=?',
        (id,)
    )

    data = cur.fetchone()

    conn.close()

    filename = f'portfolio_{id}.pdf'

    pdf = canvas.Canvas(filename)

    pdf.drawString(100, 800, "PORTFOLIO DETAILS")

    pdf.drawString(100, 760, "Name: " + data[1])
    pdf.drawString(100, 740, "Designation: " + data[2])
    pdf.drawString(100, 720, "Location: " + data[3])
    pdf.drawString(100, 700, "Contact: " + data[4])
    pdf.drawString(100, 680, "Summary: " + data[5])
    pdf.drawString(100, 660, "Education: " + data[6])
    pdf.drawString(100, 640, "Skills: " + data[7])
    pdf.drawString(100, 620, "Achievements: " + data[8])
    pdf.drawString(100, 600, "Projects: " + data[9])
    pdf.drawString(100, 580, "Best Subject: " + data[10])
    pdf.drawString(100, 560, "Activities: " + data[11])

    pdf.save()

    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
