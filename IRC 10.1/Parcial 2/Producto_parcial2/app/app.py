from flask import Flask, render_template, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-playbook', methods=['POST'])
def run_playbook():
    data = request.get_json()
    playbook = data.get('playbook')

    # Validar que el playbook sea uno de los permitidos por seguridad
    playbooks_permitidos = [
        'conexion.yml',
        'diagnostico.yml',
        'backup.yml',
        'auditoria_forense.yml'
    ]

    if playbook not in playbooks_permitidos:
        return jsonify({'status': 'error', 'output': 'Playbook no permitido o no encontrado.'}), 400

    cmd = f"ansible-playbook -i /app/inventory.ini /app/app/playbooks/{playbook}"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return jsonify({
            'status': 'success' if result.returncode == 0 else 'failed',
            'output': result.stdout if result.stdout else result.stderr
        })
    except Exception as e:
        return jsonify({'status': 'error', 'output': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)