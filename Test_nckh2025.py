from flask import Flask, render_template, jsonify
import psycopg2
import os

app = Flask(__name__)

def get_data():
    try:
        # Kết nối đến cơ sở dữ liệu PostgreSQL
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            dbname=os.environ.get('DB_NAME'),
            port=os.environ.get('DB_PORT', 5432)
        )
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, temperature, humidity FROM nckh2025 ORDER BY timestamp DESC LIMIT 20")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # Debug log để kiểm tra dữ liệu trả về
        print("Dữ liệu từ CSDL:", rows)
        return rows[::-1]  # Đảo ngược để có thứ tự thời gian tăng dần

    except Exception as e:
        # In ra lỗi nếu có lỗi kết nối hoặc query
        print(f"Lỗi trong get_data: {e}")
        return []  # Trả về danh sách rỗng nếu có lỗi


@app.route('/')
def index():
    return render_template('test_nckh2025.html')

@app.route('/data')
def data():
    try:
        rows = get_data()
        timestamps = [row[0].strftime("%H:%M:%S") for row in rows]
        temperatures = [row[1] for row in rows]
        humidities = [row[2] for row in rows]
        return jsonify({'timestamps': timestamps, 'temperatures': temperatures, 'humidities': humidities})
    except Exception as e:
        print("Lỗi trong quá trình lấy dữ liệu:", e)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
