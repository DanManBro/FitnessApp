from flask import Flask, render_template, request, redirect, url_for, g, flash
import sqlite3
from database import DATABASE, init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key_here'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def index():  
    return render_template('index.html')

@app.route('/log_workout', methods=['POST'])
def log_workout():
    flash('Форма отправлена (данные пока не сохраняются)!', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        init_db() 
    app.run(debug=True)