from flask import Flask, request, render_template, jsonify
import psycopg2
import os
from datetime import datetime
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

app = Flask(__name__)

# Kết nối cơ sở dữ liệu PostgreSQL
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
        cursor.execute("""
            SELECT timestamp, temperature, humidity, water_level, rain_level,
                   soil_moisture, pressure, vibration, gyro_x, gyro_y, gyro_z
            FROM nckh2025
            ORDER BY timestamp DESC
            LIMIT 50
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        rows = rows[::-1]  # Đảo ngược lại theo thứ tự thời gian tăng dần
        return jsonify({
            'timestamps': [r[0].strftime("%H:%M:%S") for r in rows],
            'temperatures': [r[1] for r in rows],
            'humidities': [r[2] for r in rows],
            'water_levels': [r[3] for r in rows],
            'rain_levels': [r[4] for r in rows],
            'soil_moistures': [r[5] for r in rows],
            'pressures': [r[6] for r in rows],
            'vibrations': [r[7] for r in rows],
            'gyro_xs': [r[8] for r in rows],
            'gyro_ys': [r[9] for r in rows],
            'gyro_zs': [r[10] for r in rows],
        })

    except Exception as e:
        print("Lỗi trong /data:", e)
        return jsonify({'error': str(e)}), 500


@app.route('/upload', methods=['POST'])
def upload_data():
    try:
        data = request.json
        print("Dữ liệu nhận từ Gateway:", data)

        # Lấy dữ liệu từ JSON
        temperature = data.get('temperature')
        humidity = data.get('humidity')
        water_level = data.get('water_level')
        rain_level = data.get('rain_level')
        soil_moisture = data.get('soil_moisture')
        pressure = data.get('pressure')
        vibration = data.get('vibration')
        gyro_x = data.get('gyro_x')
        gyro_y = data.get('gyro_y')
        gyro_z = data.get('gyro_z')
        timestamp = datetime.now()

        # Ghi vào cơ sở dữ liệu
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO nckh2025 (
                timestamp, temperature, humidity,
                water_level, rain_level, soil_moisture,
                pressure, vibration, gyro_x, gyro_y, gyro_z
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            timestamp, temperature, humidity,
            water_level, rain_level, soil_moisture,
            pressure, vibration, gyro_x, gyro_y, gyro_z
        ))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        print("Lỗi khi ghi dữ liệu:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/predict')
def predict_trend():
    try:
        conn = get_connection()
        query = """
            SELECT timestamp, water_level, rain_level, soil_moisture
            FROM nckh2025
            ORDER BY timestamp DESC
            LIMIT 50
        """
        df = pd.read_sql(query, conn)
        conn.close()

        df = df.sort_values('timestamp')  # Sắp xếp theo thời gian tăng dần
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        result = {}

        ### Holt-Winters dự báo xu hướng 3 bước tới
        future_steps = 3
        interval = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[-2]).seconds
        future_timestamps = [
            df['timestamp'].iloc[-1] + pd.Timedelta(seconds=interval * i)
            for i in range(1, future_steps + 1)
        ]

        for col in ['water_level', 'rain_level', 'soil_moisture']:
            series = df[col].astype(float)

            if len(series) < 10:
                result[col] = {'error': 'Không đủ dữ liệu để dự đoán'}
                continue

            model = ExponentialSmoothing(series, trend='add', seasonal=None, initialization_method="estimated")
            fit = model.fit()
            prediction = fit.forecast(future_steps)

            result[col] = {
                'last_values': series[-5:].tolist(),
                'predicted_next': prediction.tolist()
            }

        ### Thống kê và tương quan
        stats = {
            'mean': df[['water_level', 'rain_level', 'soil_moisture']].mean().to_dict(),
            'std': df[['water_level', 'rain_level', 'soil_moisture']].std().to_dict(),
        }

        correlation_matrix = df[['water_level', 'rain_level', 'soil_moisture']].corr().round(3).to_dict()

        return jsonify({
            'predictions': result,
            'future_timestamps': [ts.strftime("%Y-%m-%d %H:%M:%S") for ts in future_timestamps],
            'statistics': stats,
            'correlation_matrix': correlation_matrix
        })

    except Exception as e:
        print("Lỗi khi dự đoán:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
