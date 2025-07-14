from flask import Flask, render_template, request, redirect, url_for, g, flash
import sqlite3
from datetime import datetime, timedelta, date 
from database import DATABASE, init_db 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key_for_flash' 

def get_db():
    """Получает соединение с базой данных."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row 
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Закрывает соединение с базой данных при завершении контекста приложения."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    """Главная страница: форма для добавления тренировки и список всех тренировок."""
    db = get_db()
    cursor = db.cursor()
    
    
    cursor.execute("SELECT * FROM workouts ORDER BY date DESC, id DESC")
    workouts = cursor.fetchall() 

    return render_template('index.html', workouts=workouts, title='Главная')

@app.route('/log_workout', methods=['POST'])
def log_workout():
    """Обрабатывает отправку формы для регистрации тренировки."""
    if request.method == 'POST':
        
        workout_date = request.form['date']
        activity_type = request.form['activity_type']
        duration_minutes = request.form['duration_minutes']
        calories_burned = request.form['calories_burned']

        if not workout_date or not activity_type or not duration_minutes or not calories_burned:
            flash('Пожалуйста, заполните все поля!', 'error')
            return redirect(url_for('index'))
        
        try:
            duration_minutes = int(duration_minutes)
            calories_burned = int(calories_burned)  
            datetime.strptime(workout_date, '%Y-%m-%d')
        except ValueError:
            flash('Длительность и калории должны быть числами, а дата в формате ГГГГ-ММ-ДД.', 'error')
            return redirect(url_for('index'))

        db = get_db()
        cursor = db.cursor()      
        
        try:
            cursor.execute(
                "INSERT INTO workouts (date, activity_type, duration_minutes, calories_burned) VALUES (?, ?, ?, ?)",
                (workout_date, activity_type, duration_minutes, calories_burned)
            )
            db.commit() 
            flash('Тренировка успешно добавлена!', 'success')
        except sqlite3.Error as e:
            flash(f'Ошибка при добавлении тренировки: {e}', 'error')

        return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)

