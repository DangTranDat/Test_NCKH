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
            FROM nckh2025
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
            INSERT INTO nckh2025 (
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
            FROM nckh2025
            ORDER BY timestamp DESC
            LIMIT 100
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
            series = df[param].astype(float).dropna()
            if len(series) < 10:
                result[param] = {'error': 'Không đủ dữ liệu để dự đoán'}
                continue
            if series.std() == 0:
                 # Tất cả giá trị đều giống nhau => dự báo cũng giống nhau
                repeated_value = series.iloc[-1]
                result[param] = {
                    'last_values': series[-5:].tolist(),
                    'predicted_next': [repeated_value] * forecast_steps,
                    'note': 'Chuỗi dữ liệu không đổi - giá trị dự báo được lặp lại'
                }
                continue
            try:
                model = ExponentialSmoothing(series, trend='add', seasonal=None, damped_trend=True)
                fit = model.fit()
                prediction = fit.forecast(forecast_steps)
                result[param] = {
                    'last_values': series[-5:].tolist(),
                    'predicted_next': prediction.tolist()
                }
            except Exception as e:
                result[param] = {'error': f'Lỗi mô hình: {str(e)}'}
"""
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
"""
            stats[param] = {
                'mean': round(np.mean(series), 2),
                'std': round(np.std(series), 2),
                'min': round(np.min(series), 2),
                'max': round(np.max(series), 2)
            }
        
        # PHÂN TÍCH CẢNH BÁO từ giá trị mới nhất
        """last = df.iloc[-1]

        if last['temperature'] < 35:
            alerts.append("Cảnh báo: Nhiệt độ cao vượt ngưỡng 35°C")

        if last['humidity'] < 30:
            alerts.append("Cảnh báo: Độ ẩm thấp dưới 30%")

        if last['water_level'] > 80:
            alerts.append("Cảnh báo: Mực nước vượt ngưỡng an toàn")
        
        if last['vibration'] > 1.5:
            alerts.append("Cảnh báo: Rung động mạnh vượt ngưỡng")"""

        


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
