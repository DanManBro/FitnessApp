from flask import Flask, render_template, request, redirect, url_for, g, flash
import sqlite3
from datetime import datetime, timedelta, date
from database import DATABASE, init_db # Импортируем из нашего database.py

app = Flask(__name__)
app.config['SECRET_KEY'] = 'LUBLUNPI' # Секретный ключ для flash-сообщений

# --- Функции для работы с базой данных ---
def get_db():
    """Получает соединение с базой данных."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        # Устанавливаем row_factory для получения результатов как словарей (удобно)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Закрывает соединение с базой данных при завершении контекста приложения."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Маршруты приложения ---

@app.route('/')
def index():
    """Главная страница: форма для добавления тренировки и список всех тренировок."""
    db = get_db()
    cursor = db.cursor()
    
    # Получаем все тренировки, отсортированные по дате (от новых к старым)
    cursor.execute("SELECT * FROM workouts ORDER BY date DESC, id DESC")
    workouts = cursor.fetchall() # Получаем все записи

    return render_template('index.html', workouts=workouts)

@app.route('/log_workout', methods=['POST'])
def log_workout():
    """Обрабатывает отправку формы для регистрации тренировки."""
    if request.method == 'POST':
        # Получаем данные из формы
        workout_date = request.form['date']
        activity_type = request.form['activity_type']
        duration_minutes = request.form['duration_minutes']
        calories_burned = request.form['calories_burned']

        # Базовая валидация данных
        if not workout_date or not activity_type or not duration_minutes or not calories_burned:
            flash('Пожалуйста, заполните все поля!', 'error')
            return redirect(url_for('index'))
        
        try:
            duration_minutes = int(duration_minutes)
            calories_burned = int(calories_burned)
            # Проверяем, что дата в правильном формате YYYY-MM-DD
            datetime.strptime(workout_date, '%Y-%m-%d')
        except ValueError:
            flash('Длительность и калории должны быть числами, а дата в формате ГГГГ-ММ-ДД.', 'error')
            return redirect(url_for('index'))

        db = get_db()
        cursor = db.cursor()
        
        # Вставляем новую запись в базу данных
        try:
            cursor.execute(
                "INSERT INTO workouts (date, activity_type, duration_minutes, calories_burned) VALUES (?, ?, ?, ?)",
                (workout_date, activity_type, duration_minutes, calories_burned)
            )
            db.commit() # Подтверждаем изменения
            flash('Тренировка успешно добавлена!', 'success')
        except sqlite3.Error as e:
            flash(f'Ошибка при добавлении тренировки: {e}', 'error')

        return redirect(url_for('index'))

@app.route('/dashboard')
@app.route('/dashboard/<period_str>') # Добавляем возможность указывать период в URL
def dashboard(period_str='week'):
    """Страница для визуализации данных в виде графиков и таблиц."""
    db = get_db()
    cursor = db.cursor()

    # Определяем диапазон дат в зависимости от выбранного периода
    today = date.today()
    start_date = None
    end_date = None
    
    if period_str == 'week':
        # Начало недели (понедельник)
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6) # Конец недели (воскресенье)
        title = f"за Неделю ({start_date.strftime('%d.%m')} - {end_date.strftime('%d.%m.%Y')})"
    elif period_str == 'month':
        # Начало месяца
        start_date = today.replace(day=1)
        # Конец месяца
        next_month = today.replace(day=28) + timedelta(days=4) # Уходим в следующий месяц
        end_date = next_month - timedelta(days=next_month.day) # Возвращаемся на последний день текущего
        title = f"за Месяц ({start_date.strftime('%m.%Y')})"
    else: # По умолчанию или если период не распознан
        start_date = date(1, 1, 1) # С начала времен
        end_date = date(9999, 12, 31) # До конца времен
        title = "за Весь Период"
        period_str = 'all' # Установим 'all' для корректной кнопки

    # Форматируем даты для SQL-запроса
    sql_start_date = start_date.strftime('%Y-%m-%d')
    sql_end_date = end_date.strftime('%Y-%m-%d')

    # --- Получаем агрегированные данные для графика (калории и длительность по дням) ---
    cursor.execute(
        """
        SELECT date, 
               SUM(calories_burned) AS total_calories,
               SUM(duration_minutes) AS total_duration
        FROM workouts
        WHERE date BETWEEN ? AND ?
        GROUP BY date
        ORDER BY date
        """,
        (sql_start_date, sql_end_date)
    )
    daily_summary = cursor.fetchall()

    # Подготавливаем данные для Chart.js
    chart_dates = [row['date'] for row in daily_summary]
    chart_calories = [row['total_calories'] for row in daily_summary]
    chart_duration = [row['total_duration'] for row in daily_summary]

    # --- Получаем общие итоги за выбранный период ---
    cursor.execute(
        """
        SELECT SUM(calories_burned) AS overall_calories,
               SUM(duration_minutes) AS overall_duration
        FROM workouts
        WHERE date BETWEEN ? AND ?
        """,
        (sql_start_date, sql_end_date)
    )
    overall_totals = cursor.fetchone()

    return render_template(
        'dashboard.html', 
        chart_dates=chart_dates, 
        chart_calories=chart_calories, 
        chart_duration=chart_duration,
        overall_totals=overall_totals,
        title=title,
        current_period=period_str
    )

# --- Инициализация и запуск приложения ---
if __name__ == '__main__':
    # При первом запуске приложения создаем таблицы, если их нет
    with app.app_context():
        init_db() # Убедимся, что база данных инициализирована
    app.run(debug=True) # debug=True для автоматического перезапуска при изменениях