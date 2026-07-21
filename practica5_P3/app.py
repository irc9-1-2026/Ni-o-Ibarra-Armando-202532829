import os
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    # Métricas estáticas / simuladas para el Dashboard
    metrics = {
        'cpu_usage': 18.2,
        'ram_usage': 38.5,
        'latency': 8,
        'server_status': 'Online'
    }
    return render_template('index.html', **metrics)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "flask-app"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)