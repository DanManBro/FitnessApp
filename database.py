import sqlite3

DATABASE = 'fitness.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            calories_burned INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print(f"База данных '{DATABASE}' инициализирована и таблицы созданы.")

if __name__ == '__main__':
    init_db()