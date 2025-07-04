from flask import Flask, request, render_template, jsonify
import psycopg2
import os
import pandas as pd
import numpy as np
from datetime import datetime
from statsmodels.tsa.holtwinters import ExponentialSmoothing

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
        cursor.execute("""
            SELECT timestamp, temperature, humidity, water_level, rain_level,
                   soil_moisture, pressure, vibration, gyro_x, gyro_y, gyro_z, canhbao
            FROM do_an_vien_thong
            ORDER BY timestamp DESC
            LIMIT 20
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        rows = rows[::-1]  # đảo ngược thời gian tăng dần
        return jsonify({
            'timestamps': [r[0].strftime("%H:%M:%S") for r in rows],
            'temperatures': [r[1] for r in rows],
            'humidities': [r[2] for r in rows],
            'water_levels': [r[3] for r in rows],
            'rains_level': [r[4] for r in rows],
            'soil_moistures': [r[5] for r in rows],
            'pressures': [r[6] for r in rows],
            'vibrations': [r[7] for r in rows],
            'gyro_xs': [r[8] for r in rows],
            'gyro_ys': [r[9] for r in rows],
            'gyro_zs': [r[10] for r in rows],
            'canhbao': [r[11] for r in rows],
        })

    except Exception as e:
        print("Lỗi trong /data:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_data():
    try:
        data = request.json
        timestamp = datetime.now()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO do_an_vien_thong (
                timestamp, temperature, humidity, water_level, rain_level,
                soil_moisture, pressure, vibration, gyro_x, gyro_y, gyro_z,canhbao
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
        """, (
            timestamp, data.get('temperature'), data.get('humidity'),
            data.get('water_level'), data.get('rain_level'), data.get('soil_moisture'),
            data.get('pressure'), data.get('vibration'), data.get('gyro_x'),
            data.get('gyro_y'), data.get('gyro_z'),data.get('Canh bao')
        ))
        #canhbao = data.get('Canh bao')
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
            SELECT timestamp, temperature, humidity, water_level, rain_level,
                   soil_moisture, pressure, vibration
            FROM do_an_vien_thong
            ORDER BY timestamp DESC
            LIMIT 1000
        """
        df = pd.read_sql(query, conn)
        conn.close()

        df = df.sort_values('timestamp')
        result = {}
        stats = {}

        forecast_steps = 5
        parameters = ['temperature', 'humidity', 'water_level', 'rain_level',
                      'soil_moisture', 'pressure', 'vibration']

        for param in parameters:
            series = df[param].astype(float)

            if len(series) < 10:
                result[param] = {'error': 'Không đủ dữ liệu để dự đoán'}
                continue

            model = ExponentialSmoothing(series, trend='add', seasonal=None, damped_trend=True)
            fit = model.fit()
            prediction = fit.forecast(forecast_steps)

            result[param] = {
                'last_values': series[-5:].tolist(),
                'predicted_next': prediction.tolist()
            }

            stats[param] = {
                'mean': round(np.mean(series), 2),
                'std': round(np.std(series), 2),
                'min': round(np.min(series), 2),
                'max': round(np.max(series), 2)
            }
        
        # Ma trận tương quan
        corr_matrix = df[parameters].corr().round(2).to_dict()

        return jsonify({
            'prediction': result,
            'statistics': stats,
            'correlation_matrix': corr_matrix,
            'last_timestamp': df['timestamp'].iloc[-1].strftime("%Y-%m-%d %H:%M:%S")
        })

    except Exception as e:
        print("Lỗi khi dự đoán:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
