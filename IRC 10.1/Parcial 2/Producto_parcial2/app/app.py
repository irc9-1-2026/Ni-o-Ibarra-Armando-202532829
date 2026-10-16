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
    target_host = data.get('target_host', 'AnsibleRocky')

    playbooks_permitidos = [
        'conexion.yml',
        'diagnostico.yml',
        'backup.yml',
        'auditoria_forense.yml'
    ]

    if playbook not in playbooks_permitidos:
        return jsonify({'status': 'error', 'output': 'Playbook no permitido.'}), 400

    # Pasa el target_host a Ansible mediante --limit y la variable target_host
    cmd = f"ansible-playbook -i /app/inventory.ini /app/app/playbooks/{playbook} --limit {target_host} -e 'target_host={target_host}'"
    
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