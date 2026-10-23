import os
import secrets
import unicodedata
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Conexión resiliente a MongoDB
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/itsm_db')

def get_db():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client.get_database()

# ---- Misma regla que el panel de administración: rango + tipo de ticket ----
PUESTO_PESO = {'DIRECTOR': 4, 'GERENTE': 3, 'SUPERVISOR': 2, 'EMPLEADO': 1}
TIPO_PESO = {'Falla': 3, 'Equipo Físico': 2, 'Programas': 2, 'Soporte': 1}
TIPOS_VALIDOS = ['Soporte', 'Falla', 'Equipo Físico', 'Programas']
MODALIDADES_VALIDAS = ['Remoto', 'Físico']

def normalizar(texto):
    texto = unicodedata.normalize('NFD', str(texto or ''))
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.strip().upper()

def tipo_canonico(valor):
    n = normalizar(valor)
    if n.startswith('SOPORTE'):
        return 'Soporte'
    if n.startswith('FALLA'):
        return 'Falla'
    if n.startswith('EQUIPO') or 'HARDWARE' in n:
        return 'Equipo Físico'
    if n.startswith('PROGRAMA') or 'SOFTWARE' in n:
        return 'Programas'
    return 'Soporte'

def calcular_prioridad(puesto, tipo_ticket):
    total = PUESTO_PESO.get(normalizar(puesto), 1) + TIPO_PESO.get(tipo_canonico(tipo_ticket), 1)
    if total >= 6:
        return 'CRÍTICA'
    if total == 5:
        return 'ALTA'
    if total == 4:
        return 'MEDIA'
    return 'BAJA'

# Capturador de errores para depuración limpia
@app.errorhandler(Exception)
def handle_exception(e):
    if hasattr(e, 'code') and isinstance(e.code, int) and e.code < 500:
        return e  # 404, 405, etc.: respuesta estándar
    return f"""
    <div style="font-family: sans-serif; padding: 20px; background: #04164f; color: #ffffff;">
        <h2 style="color: #ff4d5a;">Error de Aplicación o Base de Datos</h2>
        <pre>{str(e)}</pre>
        <a href="/login" style="color: #38bdf8;">Volver al Login</a>
    </div>
    """, 500

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()
    user = db.users.find_one({"username": session['username']})

    if user and user.get('status') == 'LOCKED':
        session.clear()
        return "<h3>Tu cuenta ha sido BLOQUEADA por el Administrador de TI.</h3><a href='/login'>Volver</a>", 403

    if not user:
        session.clear()
        return redirect(url_for('login'))

    tickets = list(db.tickets.find({"usuario.username": session['username']}).sort("_id", -1))
    return render_template('tickets.html', user=user, tickets=tickets)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        db = get_db()
        user = db.users.find_one({"username": username})
        if not user:
            error = "El usuario no existe. Solicita tu cuenta al administrador de TI."
        elif user.get('password') != password:
            error = "Contraseña incorrecta."
        elif user.get('status') == 'LOCKED':
            error = "Cuenta bloqueada por el administrador de TI."
        else:
            session['username'] = username
            return redirect(url_for('home'))

    return render_template('login.html', error=error)

# No existe registro público: las cuentas las crea el administrador desde el panel (puerto 5000)

@app.route('/crear-ticket', methods=['POST'])
def crear_ticket():
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()
    user = db.users.find_one({"username": session['username']})
    if not user or user.get('status') == 'LOCKED':
        session.clear()
        return redirect(url_for('login'))

    tipo_ticket = tipo_canonico(request.form.get('tipo_ticket', 'Soporte'))
    modalidad = request.form.get('modalidad', 'Remoto')
    if modalidad not in MODALIDADES_VALIDAS:
        modalidad = 'Remoto'
    detalle_afectado = request.form.get('detalle_afectado', '').strip()[:120]
    descripcion = request.form.get('descripcion', '').strip()[:500]

    puesto = user.get('puesto', 'Empleado')

    ticket = {
        "usuario": {
            "username": user['username'],
            "puesto": puesto
        },
        "tipo_ticket": tipo_ticket,
        "modalidad": modalidad,
        "detalle_afectado": detalle_afectado,
        "descripcion": descripcion,
        "prioridad": calcular_prioridad(puesto, tipo_ticket),
        "estado": "PENDIENTE"
    }
    db.tickets.insert_one(ticket)
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)