from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# Database Creation
def init_db():

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS portfolio (

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

# Login Page
@app.route('/')
def login():
    return render_template('login.html')

# Dashboard Page
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Create Portfolio
@app.route('/create', methods=['GET', 'POST'])
def create():

    if request.method == 'POST':

        name = request.form['name']
        designation = request.form['designation']
        location = request.form['location']
        contact = request.form['contact']
        summary = request.form['summary']
        education = request.form['education']
        skills = request.form['skills']
        achievement = request.form['achievement']
        project = request.form['project']
        subject = request.form['subject']
        activities = request.form['activities']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()

        cur.execute('''

        INSERT INTO portfolio
        (
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

        ''',

        (
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
        )

        conn.commit()
        conn.close()

        return redirect('/view')

    return render_template('create.html')

# View Portfolio
@app.route('/view')
def view():

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM portfolio")

    data = cur.fetchall()

    conn.close()

    return render_template('view.html', data=data)

# Update Portfolio
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    if request.method == 'POST':

        name = request.form['name']
        designation = request.form['designation']
        location = request.form['location']
        contact = request.form['contact']

        cur.execute('''

        UPDATE portfolio

        SET
        name=?,
        designation=?,
        location=?,
        contact=?

        WHERE id=?

        ''',

        (
            name,
            designation,
            location,
            contact,
            id
        ))

        conn.commit()

        return redirect('/view')

    cur.execute("SELECT * FROM portfolio WHERE id=?", (id,))

    data = cur.fetchone()

    conn.close()

    return render_template('update.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
