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
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, temperature, humidity, water_level, rain,
                   soil_moisture, pressure, vibration, gyro_x, gyro_y, gyro_z
            FROM nckh2025
            ORDER BY timestamp DESC
            LIMIT 20
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        data = [{
            'timestamp': row[0].strftime("%Y-%m-%d %H:%M:%S"),
            'temperature': row[1],
            'humidity': row[2],
            'water_level': row[3],
            'rain': row[4],
            'soil_moisture': row[5],
            'pressure': row[6],
            'vibration': row[7],
            'gyro_x': row[8],
            'gyro_y': row[9],
            'gyro_z': row[10]
        } for row in rows[::-1]]  # đảo ngược để thời gian tăng dần

        return render_template('dashboard.html', data=data)

    except Exception as e:
        print("Lỗi khi truy vấn dữ liệu:", e)
        return "Lỗi khi tải dữ liệu từ cơ sở dữ liệu."

@app.route('/upload', methods=['POST'])
def upload_data():
    try:
        data = request.json
        print("Dữ liệu nhận từ Gateway:", data)

        temperature = data.get('temperature')
        humidity = data.get('humidity')
        water_level = data.get('water_level')
        rain = data.get('rain')
        soil_moisture = data.get('soil_moisture')
        pressure = data.get('pressure')
        vibration = data.get('vibration')
        gyro_x = data.get('gyro_x')
        gyro_y = data.get('gyro_y')
        gyro_z = data.get('gyro_z')
        timestamp = datetime.now()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO nckh2025 (
                timestamp, temperature, humidity,
                water_level, rain, soil_moisture,
                pressure, vibration, accel_x, accel_y, accel_z
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            timestamp, temperature, humidity,
            water_level, rain, soil_moisture,
            pressure, vibration, gyro_x, gyro_y, gyro_z
        ))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        print("Lỗi khi ghi dữ liệu:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
