from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'your_secret_key'

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        database='login_system',
        user='postgres',
        password='1234'
    )

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            conn.close()
            return render_template('register.html', error="Username already exists")

        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, hashed_password))
        conn.commit()
        conn.close()
        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password_input):
            session['username'] = user[1]
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')

    username = session['username']
    conn = get_db_connection()
    cur = conn.cursor()

    # Count tasks per status
    cur.execute("SELECT status, COUNT(*) FROM tasks WHERE username = %s GROUP BY status", (username,))
    counts = cur.fetchall()
    status_counts = {'To Do': 0, 'In Progress': 0, 'Done': 0}
    for status, count in counts:
        status_counts[status] = count

    # Get all tasks sorted by due date
    cur.execute("SELECT title, description, due_date, status FROM tasks WHERE username = %s ORDER BY due_date", (username,))
    tasks = cur.fetchall()

    conn.close()
    return render_template('dashboard.html', username=username, status_counts=status_counts, tasks=tasks)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

@app.route('/create_task', methods=['GET', 'POST'])
def create_task():
    if 'username' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        status = request.form['status']
        username = session['username']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO tasks (username, title, description, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                    (username, title, description, due_date, status))
        conn.commit()
        conn.close()
        return redirect('/tasks')
    
    return render_template('create_task.html')


@app.route('/tasks')
def tasks():
    if 'username' not in session:
        return redirect('/login')

    username = session['username']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE username = %s", (username,))
    user_tasks = cur.fetchall()
    conn.close()

    return render_template('tasks.html', tasks=user_tasks)
@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'username' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        status = request.form['status']
        cur.execute("UPDATE tasks SET status = %s WHERE id = %s", (status, task_id))
        conn.commit()
        conn.close()
        return redirect('/tasks')

    cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    task = cur.fetchone()
    conn.close()
    return render_template('edit_task.html', task=task)

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'username' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    conn.close()
    return redirect('/tasks')

if __name__ == '__main__':
    app.run(debug=True)
