import os
import secrets
import unicodedata
from datetime import datetime, timezone, timedelta
from bson.objectid import ObjectId
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient, ReturnDocument

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/itsm_db')

# Hora de México (UTC-6, sin horario de verano)
HORA_MX = timezone(timedelta(hours=-6))


def get_db():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client.get_database()


PUESTO_PESO = {'DIRECTOR': 4, 'GERENTE': 3, 'SUPERVISOR': 2, 'EMPLEADO': 1}
TIPO_PESO = {'Falla': 3, 'Equipo Físico': 2, 'Programas': 2, 'Soporte': 1}
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


def siguiente_numero(db):
    """Número consecutivo de ticket (1, 2, 3...). El contador parte del mayor número existente."""
    if not db.contadores.find_one({'_id': 'tickets'}):
        mayor = db.tickets.find_one({'numero': {'$exists': True}}, sort=[('numero', -1)])
        db.contadores.update_one({'_id': 'tickets'},
                                 {'$setOnInsert': {'seq': mayor['numero'] if mayor else 0}}, upsert=True)
    doc = db.contadores.find_one_and_update({'_id': 'tickets'}, {'$inc': {'seq': 1}},
                                            return_document=ReturnDocument.AFTER)
    return doc['seq']


def formato_fecha(fecha):
    if fecha is None:
        return '—'
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(HORA_MX).strftime('%d/%m/%Y %H:%M')


def ticket_para_idc(t):
    usuario = t.get('usuario') or {}
    if normalizar(t.get('estado')) == 'RESUELTO':
        estado = 'RESUELTO'
    elif t.get('resolucion_idc'):
        estado = 'EN REVISIÓN'
    else:
        estado = 'PENDIENTE'
    return {
        'id': str(t['_id']),
        'numero': t.get('numero') or '—',
        'solicitante': usuario.get('username') or '—',
        'puesto': usuario.get('puesto') or '—',
        'tipo': tipo_canonico(t.get('tipo_ticket')),
        'modalidad': t.get('modalidad') or '—',
        'equipo': t.get('detalle_afectado') or '—',
        'descripcion': t.get('descripcion') or '—',
        'prioridad': t.get('prioridad') or 'BAJA',
        'estado': estado,
        'creado': formato_fecha(t.get('fecha_creacion') or t['_id'].generation_time),
        'asignado': formato_fecha(t.get('fecha_asignacion')),
        'resolucion': t.get('resolucion') or '',
        'resolucion_idc': t.get('resolucion_idc') or '',
        'fecha_resolucion_idc': formato_fecha(t.get('fecha_resolucion_idc')),
    }


@app.errorhandler(Exception)
def handle_exception(e):
    if hasattr(e, 'code') and isinstance(e.code, int) and e.code < 500:
        return e
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

    # Portal distinto para los usuarios IDC: solo ven los tickets que se les asignaron
    if user.get('rol') == 'IDC':
        asignados = [ticket_para_idc(t) for t in
                     db.tickets.find({"asignado_a": user['username']}).sort("_id", -1)]
        orden = {'PENDIENTE': 0, 'EN REVISIÓN': 1, 'RESUELTO': 2}
        asignados.sort(key=lambda x: orden[x['estado']])
        pendientes = sum(1 for x in asignados if x['estado'] == 'PENDIENTE')
        en_revision = sum(1 for x in asignados if x['estado'] == 'EN REVISIÓN')
        resueltos = sum(1 for x in asignados if x['estado'] == 'RESUELTO')
        return render_template('idc.html', user=user, tickets=asignados,
                               pendientes=pendientes, en_revision=en_revision, resueltos=resueltos)

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


@app.route('/crear-ticket', methods=['POST'])
def crear_ticket():
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()
    user = db.users.find_one({"username": session['username']})
    if not user or user.get('status') == 'LOCKED':
        session.clear()
        return redirect(url_for('login'))

    # Los IDC atienden tickets, no los crean
    if user.get('rol') == 'IDC':
        return redirect(url_for('home'))

    tipo_ticket = tipo_canonico(request.form.get('tipo_ticket', 'Soporte'))
    modalidad = request.form.get('modalidad', 'Remoto')
    if modalidad not in MODALIDADES_VALIDAS:
        modalidad = 'Remoto'
    detalle_afectado = request.form.get('detalle_afectado', '').strip()[:120]
    descripcion = request.form.get('descripcion', '').strip()[:500]

    puesto = user.get('puesto', 'Empleado')

    ticket = {
        "numero": siguiente_numero(db),
        "fecha_creacion": datetime.now(timezone.utc),
        "usuario": {"username": user['username'], "puesto": puesto},
        "tipo_ticket": tipo_ticket,
        "modalidad": modalidad,
        "detalle_afectado": detalle_afectado,
        "descripcion": descripcion,
        "prioridad": calcular_prioridad(puesto, tipo_ticket),
        "estado": "PENDIENTE"
    }
    db.tickets.insert_one(ticket)
    return redirect(url_for('home'))


@app.route('/resolver-ticket', methods=['POST'])
def resolver_ticket_idc():
    """El IDC explica cómo resolvió su ticket; el administrador lo revisa y lo cierra."""
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()
    user = db.users.find_one({"username": session['username']})
    if not user or user.get('status') == 'LOCKED':
        session.clear()
        return redirect(url_for('login'))
    if user.get('rol') != 'IDC':
        return redirect(url_for('home'))

    resolucion = request.form.get('resolucion', '').strip()[:1000]
    try:
        oid = ObjectId(request.form.get('ticket_id', '').strip())
    except Exception:
        return redirect(url_for('home'))

    if len(resolucion) < 5:
        return redirect(url_for('home'))

    # Solo puede resolver tickets que le asignaron, que no estén cerrados ni ya enviados a revisión
    db.tickets.update_one(
        {'_id': oid, 'asignado_a': user['username'], 'estado': {'$ne': 'RESUELTO'},
         'resolucion_idc': {'$exists': False}},
        {'$set': {'resolucion_idc': resolucion,
                  'fecha_resolucion_idc': datetime.now(timezone.utc)}})
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)