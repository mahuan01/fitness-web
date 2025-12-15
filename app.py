from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import date, timedelta
import os

app = Flask(__name__)
DB_PATH = "fitness.db"

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        log_date TEXT UNIQUE,
                        duration INTEGER,
                        notes TEXT
                    )''')
        conn.commit()
        conn.close()

def get_all_dates():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT log_date FROM logs ORDER BY log_date")
    dates = [date.fromisoformat(row[0]) for row in c.fetchall()]
    conn.close()
    return dates

@app.route('/')
def index():
    # 获取当前 streak
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT log_date FROM logs")
    dates_set = {date.fromisoformat(row[0]) for row in c.fetchall()}
    conn.close()

    streak = 0
    current = date.today()
    while current in dates_set:
        streak += 1
        current -= timedelta(days=1)

    # 获取最长 streak
    all_dates = get_all_dates()
    max_streak = 0
    if all_dates:
        current_streak = 1
        for i in range(1, len(all_dates)):
            if all_dates[i] == all_dates[i-1] + timedelta(days=1):
                current_streak += 1
            else:
                max_streak = max(max_streak, current_streak)
                current_streak = 1
        max_streak = max(max_streak, current_streak)

    return render_template('index.html', streak=streak, max_streak=max_streak)

@app.route('/api/log', methods=['POST'])
def log_workout():
    today_str = str(date.today())
    data = request.get_json()
    duration = data.get('duration', 0)
    notes = data.get('notes', '').strip()

    if duration <= 0:
        return jsonify({"success": False, "message": "时长必须大于0"})

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO logs (log_date, duration, notes) VALUES (?, ?, ?)",
                  (today_str, duration, notes))
        conn.commit()
        success = True
        message = "打卡成功！"
    except sqlite3.IntegrityError:
        success = False
        message = "今天已经打过卡啦！"
    conn.close()
    return jsonify({"success": success, "message": message})

@app.route('/history')
def history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT log_date, duration, notes FROM logs ORDER BY log_date DESC")
    logs = c.fetchall()
    conn.close()
    return render_template('history.html', logs=logs)

# 可选：删除某天记录（谨慎使用）
@app.route('/api/delete/<log_date>', methods=['DELETE'])
def delete_log(log_date):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM logs WHERE log_date = ?", (log_date,))
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()
    return jsonify({"success": deleted})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)