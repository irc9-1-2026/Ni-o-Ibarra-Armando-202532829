import os
import subprocess
from flask import Flask, render_template, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVENTARIO = os.path.join(os.path.dirname(BASE_DIR), "inventory.ini")
PLAYBOOKS_DIR = os.path.join(BASE_DIR, "playbooks")

@app.route('/', methods=['GET', 'POST'])
def index():
    output = ""
    playbook_seleccionado = ""
    
    if request.method == 'POST':
        playbook_file = request.form.get('playbook_file', 'ejemplo.yml')
        playbook_path = os.path.join(PLAYBOOKS_DIR, playbook_file)
        
        try:
            cmd = ["ansible-playbook", "-i", INVENTARIO, playbook_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            output = result.stdout + result.stderr
            playbook_seleccionado = playbook_file
        except subprocess.TimeoutExpired:
            output = "Error: El playbook excedió el tiempo límite de 5 minutos."
        except Exception as e:
            output = f"Error: {e}"
            
    return render_template('index.html', output=output, playbook_actual=playbook_seleccionado)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)