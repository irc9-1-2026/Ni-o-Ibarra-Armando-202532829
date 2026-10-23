import os
import time
import hmac
import secrets
import subprocess
import json
import unicodedata
import urllib.request
import urllib.error
from statistics import median
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') or secrets.token_hex(32)
app.config.update(
    TEMPLATES_AUTO_RELOAD=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/itsm_db')
client = MongoClient(MONGO_URI)
db = client.get_database()

# Único host objetivo de las tarjetas de auditoría
TARGET_HOST = os.getenv('TARGET_HOST', 'Rocky2')

# ---- Acceso del administrador (la contraseña solo existe como hash) ----
ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH', '')
MAX_INTENTOS = 5
BLOQUEO_SEG = 300
intentos_fallidos = {}  # ip -> (fallos, bloqueado_hasta)

# ---- Reglas de prioridad: rango del usuario + tipo de ticket ----
PUESTO_PESO = {'DIRECTOR': 4, 'GERENTE': 3, 'SUPERVISOR': 2, 'EMPLEADO': 1}
TIPO_PESO = {'Falla': 3, 'Equipo Físico': 2, 'Programas': 2, 'Soporte': 1}
PRIORIDADES_ORDEN = ['CRITICA', 'ALTA', 'MEDIA', 'BAJA']
TIPOS_ORDEN = ['Soporte', 'Falla', 'Equipo Físico', 'Programas']
ETIQUETAS = {'CRITICA': 'CRÍTICA', 'ALTA': 'ALTA', 'MEDIA': 'MEDIA', 'BAJA': 'BAJA'}
PUESTOS = ['Empleado', 'Supervisor', 'Gerente', 'Director']


def normalizar(texto):
    """Quita acentos y pasa a mayúsculas: 'CRÍTICA' -> 'CRITICA'."""
    texto = unicodedata.normalize('NFD', str(texto or ''))
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.strip().upper()


def tipo_canonico(valor):
    """Unifica 'Soporte TÉCNICO', 'Equipo Físico (Hardware)', etc."""
    n = normalizar(valor)
    if n.startswith('SOPORTE'):
        return 'Soporte'
    if n.startswith('FALLA'):
        return 'Falla'
    if n.startswith('EQUIPO') or 'HARDWARE' in n:
        return 'Equipo Físico'
    if n.startswith('PROGRAMA') or 'SOFTWARE' in n:
        return 'Programas'
    return str(valor) if valor else 'Otro'


def calcular_prioridad(puesto, tipo):
    """Devuelve (clave, puntaje, peso_puesto, peso_tipo)."""
    pp = PUESTO_PESO.get(normalizar(puesto), 1)
    pt = TIPO_PESO.get(tipo, 1)
    total = pp + pt
    if total >= 6:
        clave = 'CRITICA'
    elif total == 5:
        clave = 'ALTA'
    elif total == 4:
        clave = 'MEDIA'
    else:
        clave = 'BAJA'
    return clave, total, pp, pt


def a_utc(fecha):
    """Convierte una fecha de Mongo (naive = UTC) en fecha con zona UTC."""
    if fecha is None:
        return None
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc)


def registrar_acceso_panel(accion, estado):
    """Guarda la IP real del navegador que ejecutó la tarea."""
    try:
        db.panel_accesos.insert_one({
            'ip': request.remote_addr,
            'accion': accion,
            'estado': estado,
            'fecha': datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S'),
        })
    except Exception:
        pass  # el registro nunca debe impedir la ejecución


def comprobar_portal():
    """Devuelve (disponible, milisegundos) consultando el portal por la red interna de Docker."""
    inicio = time.time()
    try:
        urllib.request.urlopen('http://portal-web:8080/login', timeout=3)
    except urllib.error.HTTPError:
        pass  # el portal respondió, aunque sea con un código HTTP distinto de 200
    except Exception:
        return False, None
    return True, int((time.time() - inicio) * 1000)


# ===================== Autenticación del administrador =====================
@app.before_request
def exigir_sesion():
    if request.endpoint in ('login', 'static') or session.get('admin'):
        return None
    if request.path.startswith('/api/') or request.path == '/run-playbook':
        return jsonify({'output': '[ERROR] Sesión no válida. Inicia sesión de nuevo.',
                        'status': 'error'}), 401
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin'):
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        ip = request.remote_addr
        ahora = time.time()
        fallos, bloqueado_hasta = intentos_fallidos.get(ip, (0, 0))

        if not ADMIN_PASSWORD_HASH:
            error = 'El acceso de administración no está configurado en el servidor.'
        elif bloqueado_hasta > ahora:
            error = 'Demasiados intentos fallidos. Espera %d min.' % (int((bloqueado_hasta - ahora) // 60) + 1)
        else:
            usuario = request.form.get('username', '').strip()
            clave = request.form.get('password', '')
            usuario_ok = hmac.compare_digest(usuario.encode(), ADMIN_USER.encode())
            clave_ok = check_password_hash(ADMIN_PASSWORD_HASH, clave)

            if usuario_ok and clave_ok:
                intentos_fallidos.pop(ip, None)
                session.clear()
                session['admin'] = True
                session.permanent = True
                registrar_acceso_panel('LOGIN', 'OK')
                return redirect(url_for('index'))

            fallos += 1
            if fallos >= MAX_INTENTOS:
                intentos_fallidos[ip] = (0, ahora + BLOQUEO_SEG)
            else:
                intentos_fallidos[ip] = (fallos, 0)
            registrar_acceso_panel('LOGIN', 'FALLO')
            error = 'Usuario o contraseña incorrectos.'

    return render_template('login.html', error=error)


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


# ===================== Rutas del panel =====================
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/run-playbook', methods=['POST'])
def run_playbook():
    data = request.json or {}
    playbook = data.get('playbook')
    target_host = data.get('target_host') or TARGET_HOST
    tag = data.get('tag')
    user_name = data.get('user_name')
    ticket_id = data.get('ticket_id')
    nuevo_puesto = data.get('nuevo_puesto')
    nueva_prioridad = data.get('nueva_prioridad')
    nueva_password = data.get('nueva_password')
    borrar_tickets = data.get('borrar_tickets')

    if not playbook:
        return jsonify({'output': '[ERROR] Nombre de playbook no especificado.', 'status': 'error'}), 400

    accion = playbook + (' [' + tag + ']' if tag else '')
    playbook_path = os.path.join('/app/app/playbooks', os.path.basename(playbook))

    cmd = ['ansible-playbook', playbook_path, '-i', '/app/inventory.ini', '-e', f'target_host={target_host}']

    if tag:
        cmd.extend(['--tags', tag])

    extra_vars = {}
    if user_name: extra_vars['user_name'] = user_name
    if ticket_id: extra_vars['ticket_id'] = ticket_id
    if nuevo_puesto: extra_vars['nuevo_puesto'] = nuevo_puesto
    if nueva_prioridad: extra_vars['nueva_prioridad'] = nueva_prioridad
    if nueva_password: extra_vars['nueva_password'] = nueva_password
    if borrar_tickets: extra_vars['borrar_tickets'] = True

    if extra_vars:
        cmd.extend(['-e', json.dumps(extra_vars)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = (result.stdout or '') + (result.stderr or '')
        ok = result.returncode == 0

        # Si se pidió una etiqueta y no corrió ninguna tarea, el playbook del servidor está desactualizado
        if ok and tag and 'TASK [' not in output:
            ok = False
            output += '\nERROR: el playbook no tiene tareas con la etiqueta "%s". Actualiza el archivo en el servidor.' % tag

        registrar_acceso_panel(accion, 'OK' if ok else 'FALLO')
        return jsonify({'output': output, 'status': 'success' if ok else 'error'})
    except subprocess.TimeoutExpired:
        registrar_acceso_panel(accion, 'TIMEOUT')
        return jsonify({'output': '[ERROR] El playbook excedió el tiempo límite (60s).', 'status': 'error'}), 500
    except Exception as e:
        registrar_acceso_panel(accion, 'ERROR')
        return jsonify({'output': f'[ERROR] {str(e)}', 'status': 'error'}), 500


@app.route('/api/usuarios')
def api_usuarios():
    """Usuarios del portal con su conteo de tickets. Nunca devuelve contraseñas."""
    pendientes, totales = {}, {}
    for t in db.tickets.find({}, {'usuario.username': 1, 'estado': 1}):
        nombre = (t.get('usuario') or {}).get('username')
        totales[nombre] = totales.get(nombre, 0) + 1
        if normalizar(t.get('estado')) != 'RESUELTO':
            pendientes[nombre] = pendientes.get(nombre, 0) + 1

    usuarios = []
    for u in db.users.find({}, {'password': 0}).sort('username', 1):
        nombre = u.get('username')
        usuarios.append({
            'username': nombre,
            'puesto': u.get('puesto'),
            'prioridad_base': u.get('prioridad_base'),
            'status': u.get('status', 'ACTIVE'),
            'tickets_pendientes': pendientes.get(nombre, 0),
            'tickets_total': totales.get(nombre, 0),
        })
    return jsonify({'puestos': PUESTOS, 'usuarios': usuarios})


@app.route('/api/tickets')
def api_tickets():
    """Tickets pendientes clasificados por rango del usuario + tipo de ticket."""
    columnas = {p: [] for p in PRIORIDADES_ORDEN}

    for t in db.tickets.find():
        usuario = t.get('usuario', {}) or {}
        puesto = usuario.get('puesto')
        tipo = tipo_canonico(t.get('tipo_ticket'))
        clave, total, pp, pt = calcular_prioridad(puesto, tipo)

        etiqueta = ETIQUETAS[clave]
        if t.get('prioridad') != etiqueta:
            db.tickets.update_one({'_id': t['_id']}, {'$set': {'prioridad': etiqueta}})

        if normalizar(t.get('estado')) == 'RESUELTO':
            continue

        columnas[clave].append({
            'id': str(t.get('_id')),
            'usuario': usuario.get('username'),
            'puesto': puesto,
            'tipo': tipo,
            'afectado': t.get('detalle_afectado'),
            'modalidad': t.get('modalidad'),
            'descripcion': t.get('descripcion'),
            'estado': t.get('estado'),
            'puntaje': total,
            'regla': f"{puesto or 'Sin puesto'} {pp} + {tipo} {pt}",
            'peso_puesto': pp,
            'peso_tipo': pt,
        })

    for lista in columnas.values():
        lista.sort(key=lambda x: (-x['peso_tipo'], x['tipo'], -x['peso_puesto']))

    return jsonify(columnas)


@app.route('/api/metricas')
def api_metricas():
    """Métricas de tickets para la pestaña de telemetría (tiempos en segundos)."""
    ahora = datetime.now(timezone.utc)
    hace_24h = ahora - timedelta(hours=24)

    pendientes = resueltos = sin_fecha = creados_24h = resueltos_24h = 0
    tiempos = []
    edades = []
    tiempos_por_prioridad = {p: [] for p in PRIORIDADES_ORDEN}
    pendientes_por_prioridad = {p: 0 for p in PRIORIDADES_ORDEN}
    por_tipo = {t: {'pendientes': 0, 'resueltos': 0} for t in TIPOS_ORDEN}

    for t in db.tickets.find():
        usuario = t.get('usuario', {}) or {}
        tipo = tipo_canonico(t.get('tipo_ticket'))
        clave = calcular_prioridad(usuario.get('puesto'), tipo)[0]
        creado = a_utc(t['_id'].generation_time)
        por_tipo.setdefault(tipo, {'pendientes': 0, 'resueltos': 0})

        if creado >= hace_24h:
            creados_24h += 1

        if normalizar(t.get('estado')) == 'RESUELTO':
            resueltos += 1
            por_tipo[tipo]['resueltos'] += 1
            fecha_res = a_utc(t.get('fecha_resolucion'))
            if fecha_res:
                duracion = max((fecha_res - creado).total_seconds(), 0)
                tiempos.append(duracion)
                tiempos_por_prioridad[clave].append(duracion)
                if fecha_res >= hace_24h:
                    resueltos_24h += 1
            else:
                sin_fecha += 1
        else:
            pendientes += 1
            por_tipo[tipo]['pendientes'] += 1
            pendientes_por_prioridad[clave] += 1
            edades.append(max((ahora - creado).total_seconds(), 0))

    total = pendientes + resueltos
    portal_ok, portal_ms = comprobar_portal()

    por_prioridad = {}
    for p in PRIORIDADES_ORDEN:
        lista = tiempos_por_prioridad[p]
        por_prioridad[p] = {
            'pendientes': pendientes_por_prioridad[p],
            'resueltos_con_fecha': len(lista),
            'promedio_seg': (sum(lista) / len(lista)) if lista else None,
        }

    return jsonify({
        'estado_portal': 'ONLINE' if portal_ok else 'OFFLINE',
        'portal_ms': portal_ms,
        'total': total,
        'pendientes': pendientes,
        'resueltos': resueltos,
        'tasa_resolucion': round(100 * resueltos / total, 1) if total else 0,
        'usuarios': db.users.count_documents({}),
        'usuarios_bloqueados': db.users.count_documents({'status': 'LOCKED'}),
        'tiempo_promedio_seg': (sum(tiempos) / len(tiempos)) if tiempos else None,
        'tiempo_mediana_seg': median(tiempos) if tiempos else None,
        'resueltos_con_fecha': len(tiempos),
        'resueltos_sin_fecha': sin_fecha,
        'antiguedad_promedio_seg': (sum(edades) / len(edades)) if edades else None,
        'mas_antiguo_seg': max(edades) if edades else None,
        'creados_24h': creados_24h,
        'resueltos_24h': resueltos_24h,
        'por_prioridad': por_prioridad,
        'por_tipo': por_tipo,
        'actualizado': datetime.now().astimezone().strftime('%H:%M:%S'),
    })


@app.route('/api/telemetria')
def telemetria():
    return jsonify({
        'total_tickets': db.tickets.count_documents({}),
        'tickets_pendientes': db.tickets.count_documents({"estado": "PENDIENTE"}),
        'tickets_resueltos': db.tickets.count_documents({"estado": "RESUELTO"}),
        'total_usuarios': db.users.count_documents({}),
        'status': 'ONLINE'
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)