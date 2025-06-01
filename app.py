from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

def init_db():
    conn = sqlite3.connect('words.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY,
                 username TEXT UNIQUE,
                 password TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS words
                 (id INTEGER PRIMARY KEY,
                 english TEXT,
                 translation TEXT,  
                 category TEXT,
                 user_id INTEGER,
                 FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute("SELECT COUNT(*) FROM words")
    if c.fetchone()[0] == 0:
        sample_words = [
            ('large', 'besar', 'adjective', 1),
            ('book', 'buku', 'noun', 1),
            ('jump', 'lompat', 'verb', 1)
        ]
        c.executemany("INSERT INTO words (english, translation, category, user_id) VALUES (?, ?, ?, ?)",
                     sample_words)
    
    conn.commit()
    conn.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('words.db')
        c = conn.cursor()
        
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                      (username, generate_password_hash(password)))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('words.db')
        c = conn.cursor()
        
        c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/add_word', methods=['GET', 'POST'])
def add_word():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        english = request.form['english']
        translation = request.form['translation'] 
        category = request.form['category']
        
        conn = sqlite3.connect('words.db')
        c = conn.cursor()
        c.execute("INSERT INTO words (english, translation, category, user_id) VALUES (?, ?, ?, ?)",
                 (english, translation, category, session['user_id']))
        conn.commit()
        conn.close()
        
        flash('Word added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_word.html')
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('words.db')
    c = conn.cursor()
    c.execute("SELECT english, translation, category FROM words WHERE user_id = ?", 
             (session['user_id'],))
    words = c.fetchall()
    conn.close()
    
    return render_template('index.html', words=words)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)