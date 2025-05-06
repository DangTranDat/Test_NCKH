from flask import Flask, render_template, jsonify
import mysql.connector

app = Flask(__name__)

# Kết nối CSDL
def get_data():
    conn = mysql.connector.connect(
        host='your-db-host',
        user='your-db-user',
        password='your-db-password',
        database='your-db-name'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, temperature, humidity FROM sensor_data ORDER BY timestamp DESC LIMIT 20")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows[::-1]  # đảo ngược để có thứ tự thời gian tăng dần

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    rows = get_data()
    timestamps = [row[0].strftime("%H:%M:%S") for row in rows]
    temperatures = [row[1] for row in rows]
    humidities = [row[2] for row in rows]
    return jsonify({'timestamps': timestamps, 'temperatures': temperatures, 'humidities': humidities})

if __name__ == '__main__':
    app.run(debug=True)
