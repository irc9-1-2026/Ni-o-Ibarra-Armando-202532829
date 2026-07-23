from flask import Flask, render_template, request
from builds_db import obtener_build

app = Flask(__name__)

@app.route('/')
def index():
    """Carga el dashboard con el catálogo completo de todos los personajes"""
    return render_template('portal_index.html')

@app.route('/guia')
def guia():
    """Carga la guía detallada de un personaje concreto"""
    char_id = request.args.get('personaje', 'hu-tao').lower().strip()
    build_data = obtener_build(char_id)
    return render_template('portal_guia.html', build=build_data, char_id=char_id)

@app.route('/personaje/<char_id>')
def personaje_directo(char_id):
    """Soporte para enlaces directos"""
    build_data = obtener_build(char_id)
    return render_template('portal_guia.html', build=build_data, char_id=char_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)