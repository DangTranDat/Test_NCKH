from flask import Flask, request, render_template, jsonify
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)   

def get_connection():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        dbname=os.environ.get('DB_NAME'),
        port=os.environ.get('DB_PORT', 5432)
    )

@app.route('/')
def index():
    return render_template('test_nckh2025.html')

@app.route('/data')
def data():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, temperature, humidity FROM nckh2025 ORDER BY timestamp DESC LIMIT 20")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        timestamps = [row[0].strftime("%H:%M:%S") for row in rows]
        temperatures = [row[1] for row in rows]
        humidities = [row[2] for row in rows]
        return jsonify({'timestamps': timestamps, 'temperatures': temperatures, 'humidities': humidities})
    except Exception as e:
        print("Lỗi trong quá trình lấy dữ liệu:", e)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
