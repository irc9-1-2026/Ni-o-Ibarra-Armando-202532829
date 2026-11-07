import os
import io
import re
import csv
import time
import hmac
import secrets
import subprocess
import json
import unicodedata
import urllib.request
import urllib.error
from collections import Counter
from statistics import median
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from pymongo import MongoClient, ReturnDocument
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

TARGET_HOST = os.getenv('TARGET_HOST', 'Rocky2')

# Hora de México (UTC-6, sin horario de verano)
HORA_MX = timezone(timedelta(hours=-6))

# ---- Acceso del administrador (la contraseña solo existe como hash) ----
ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH', '')
MAX_INTENTOS = 5
BLOQUEO_SEG = 300
intentos_fallidos = {}

# ---- Reglas de prioridad: rango del usuario + tipo de ticket ----
PUESTO_PESO = {'DIRECTOR': 4, 'GERENTE': 3, 'SUPERVISOR': 2, 'EMPLEADO': 1}
TIPO_PESO = {'Falla': 3, 'Equipo Físico': 2, 'Programas': 2, 'Soporte': 1}
PRIORIDADES_ORDEN = ['CRITICA', 'ALTA', 'MEDIA', 'BAJA']
TIPOS_ORDEN = ['Soporte', 'Falla', 'Equipo Físico', 'Programas']
ETIQUETAS = {'CRITICA': 'CRÍTICA', 'ALTA': 'ALTA', 'MEDIA': 'MEDIA', 'BAJA': 'BAJA'}
PUESTOS = ['Empleado', 'Supervisor', 'Gerente', 'Director']

# Variables que el panel puede enviar a los playbooks (lista blanca) y su largo máximo
VARIABLES_PERMITIDAS = {
    'user_name': 100, 'ticket_id': 40, 'nuevo_puesto': 40, 'nueva_prioridad': 40,
    'nueva_password': 200, 'nuevo_nombre': 100, 'tipo_usuario': 20,
    'idc_name': 100, 'resolucion': 1000,
}

# ---- Clasificación del historial de ejecuciones ----
TIPOS_PLAYBOOK = {
    'conexion.yml': 'Prueba de conexión',
    'diagnostico.yml': 'Salud del sistema',
    'auditoria_forense.yml': 'Auditoría de seguridad',
    'backup.yml': 'Copia de seguridad',
}
TIPOS_TAG = {
    'listar_tickets': 'Listar tickets',
    'resolver_ticket': 'Resolver ticket',
    'asignar_ticket': 'Asignar ticket',
    'desasignar_ticket': 'Quitar asignación',
    'listar_usuarios': 'Listar usuarios',
    'crear_usuario': 'Crear usuario',
    'editar_usuario': 'Editar usuario',
    'eliminar_usuario': 'Eliminar usuario',
    'clasificar_usuario': 'Cambio de puesto',
    'bloquear_usuario': 'Bloquear usuario',
    'desbloquear_usuario': 'Desbloquear usuario',
}
TIPO_LOGIN = 'Inicio de sesión'


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
    return str(valor) if valor else 'Otro'


def calcular_prioridad(puesto, tipo):
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
    if fecha is None:
        return None
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc)


def fecha_local(fecha):
    f = a_utc(fecha)
    return f.astimezone(HORA_MX).strftime('%d/%m/%Y %H:%M') if f else '—'


def asegurar_numeros():
    """Numera los tickets antiguos (por orden de creación) y les pone fecha de creación."""
    sin_numero = list(db.tickets.find({'numero': {'$exists': False}}, {'_id': 1}).sort('_id', 1))
    if sin_numero:
        if not db.contadores.find_one({'_id': 'tickets'}):
            mayor = db.tickets.find_one({'numero': {'$exists': True}}, sort=[('numero', -1)])
            db.contadores.update_one({'_id': 'tickets'},
                                     {'$setOnInsert': {'seq': mayor['numero'] if mayor else 0}}, upsert=True)
        for t in sin_numero:
            seq = db.contadores.find_one_and_update(
                {'_id': 'tickets'}, {'$inc': {'seq': 1}}, return_document=ReturnDocument.AFTER)['seq']
            db.tickets.update_one({'_id': t['_id']}, {'$set': {'numero': seq}})
    for t in db.tickets.find({'fecha_creacion': {'$exists': False}}, {'_id': 1}):
        db.tickets.update_one({'_id': t['_id']},
                              {'$set': {'fecha_creacion': a_utc(t['_id'].generation_time)}})


def registrar_acceso_panel(accion, estado, playbook=None, tag=None, duracion=None):
    """Guarda cada ejecución del panel (también alimenta el historial de la sección 5)."""
    try:
        db.panel_accesos.insert_one({
            'ip': request.remote_addr,
            'accion': accion,
            'estado': estado,
            'playbook': playbook,
            'tag': tag,
            'duracion_seg': duracion,
            'ts': datetime.now(timezone.utc),
            'fecha': datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S'),
        })
    except Exception:
        pass


def parsear_accion(accion):
    """'conexion.yml [tag]' -> ('conexion.yml', 'tag'). Sirve para los registros anteriores."""
    accion = accion or ''
    if accion == 'LOGIN':
        return 'LOGIN', None
    if accion.endswith(']') and ' [' in accion:
        playbook, tag = accion[:-1].split(' [', 1)
        return playbook, tag
    return accion, None


def tipo_de_registro(playbook, tag):
    if playbook == 'LOGIN':
        return TIPO_LOGIN
    if playbook in TIPOS_PLAYBOOK:
        return TIPOS_PLAYBOOK[playbook]
    if tag in TIPOS_TAG:
        return TIPOS_TAG[tag]
    return playbook or 'Otro'


def normalizar_registro(d):
    """Convierte un documento de panel_accesos (nuevo o antiguo) en un registro uniforme."""
    playbook, tag = d.get('playbook'), d.get('tag')
    if playbook is None:
        playbook, tag = parsear_accion(d.get('accion'))

    if d.get('ts'):
        ts = a_utc(d['ts'])
    else:
        try:
            ts = datetime.strptime(d.get('fecha', ''), '%Y-%m-%d %H:%M:%S').astimezone(timezone.utc)
        except ValueError:
            return None

    local = ts.astimezone(HORA_MX)
    return {
        'ts': ts,
        'dia': local.strftime('%Y-%m-%d'),
        'dia_txt': local.strftime('%d/%m/%Y'),
        'fecha_txt': local.strftime('%d/%m/%Y %H:%M:%S'),
        'fecha_corta': local.strftime('%d/%m/%Y, %H:%M'),
        'tipo': tipo_de_registro(playbook, tag),
        'detalle': 'Acceso al panel' if playbook == 'LOGIN' else (playbook or '—'),
        'tag': tag,
        'estado': d.get('estado') or '—',
        'duracion': d.get('duracion_seg'),
        'ip': d.get('ip') or '—',
    }


def comprobar_portal():
    inicio = time.time()
    try:
        urllib.request.urlopen('http://portal-web:8080/login', timeout=3)
    except urllib.error.HTTPError:
        pass
    except Exception:
        return False, None
    return True, int((time.time() - inicio) * 1000)


def celda_csv(valor):
    """Evita que Excel interprete una celda como fórmula."""
    s = '' if valor is None else str(valor).replace('\r', ' ').replace('\n', ' ')
    if s[:1] in ('=', '+', '-', '@', '\t'):
        s = "'" + s
    return s


def filas_resueltos():
    asegurar_numeros()
    filas = []
    for t in db.tickets.find().sort('numero', -1):
        if normalizar(t.get('estado')) != 'RESUELTO':
            continue
        filas.append({
            'id': str(t['_id']),
            'numero': t.get('numero'),
            'fecha': fecha_local(t.get('fecha_creacion') or t['_id'].generation_time),
            'tipo': tipo_canonico(t.get('tipo_ticket')),
            'modalidad': t.get('modalidad') or '',
            'equipo': t.get('detalle_afectado') or '',
            'problema': t.get('descripcion') or '',
            'resolucion': t.get('resolucion') or '',
        })
    return filas


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

    if not playbook:
        return jsonify({'output': '[ERROR] Nombre de playbook no especificado.', 'status': 'error'}), 400

    playbook = os.path.basename(str(playbook))
    accion = playbook + (' [' + tag + ']' if tag else '')
    playbook_path = os.path.join('/app/app/playbooks', playbook)

    cmd = ['ansible-playbook', playbook_path, '-i', '/app/inventory.ini', '-e', f'target_host={target_host}']

    if tag:
        cmd.extend(['--tags', tag])

    extra_vars = {}
    for clave, largo in VARIABLES_PERMITIDAS.items():
        valor = data.get(clave)
        if valor not in (None, ''):
            extra_vars[clave] = str(valor)[:largo]
    if data.get('borrar_tickets'):
        extra_vars['borrar_tickets'] = True

    if extra_vars:
        cmd.extend(['-e', json.dumps(extra_vars)])

    inicio = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = (result.stdout or '') + (result.stderr or '')
        ok = result.returncode == 0

        if ok and tag and 'TASK [' not in output:
            ok = False
            output += '\nERROR: el playbook no tiene tareas con la etiqueta "%s". Actualiza el archivo en el servidor.' % tag

        registrar_acceso_panel(accion, 'OK' if ok else 'FALLO', playbook, tag, round(time.time() - inicio, 1))
        return jsonify({'output': output, 'status': 'success' if ok else 'error'})
    except subprocess.TimeoutExpired:
        registrar_acceso_panel(accion, 'TIMEOUT', playbook, tag, round(time.time() - inicio, 1))
        return jsonify({'output': '[ERROR] El playbook excedió el tiempo límite (60s).', 'status': 'error'}), 500
    except Exception as e:
        registrar_acceso_panel(accion, 'ERROR', playbook, tag, round(time.time() - inicio, 1))
        return jsonify({'output': f'[ERROR] {str(e)}', 'status': 'error'}), 500


@app.route('/api/ultimas-ejecuciones')
def api_ultimas_ejecuciones():
    """Fecha de la última ejecución de cada playbook de la sección 1."""
    salida = {}
    for pb in TIPOS_PLAYBOOK:
        d = db.panel_accesos.find_one(
            {'accion': {'$regex': '^' + re.escape(pb) + '( |$)'}}, sort=[('_id', -1)])
        r = normalizar_registro(d) if d else None
        salida[pb] = {'fecha': r['fecha_corta'], 'estado': r['estado']} if r else None
    return jsonify(salida)


@app.route('/api/logs')
def api_logs():
    """Historial de ejecuciones con filtros por tipo, día y resultado."""
    tipo = request.args.get('tipo', '').strip()
    dia = request.args.get('dia', '').strip()
    resultado = request.args.get('resultado', '').strip().upper()

    registros = []
    for d in db.panel_accesos.find().sort('_id', -1).limit(5000):
        r = normalizar_registro(d)
        if r:
            registros.append(r)

    if tipo:
        base = [r for r in registros if r['tipo'] == tipo]
    else:
        base = [r for r in registros if r['tipo'] != TIPO_LOGIN]
    if resultado:
        base = [r for r in base if r['estado'] == resultado]

    dias_conteo = Counter(r['dia'] for r in base)
    dias_texto = {r['dia']: r['dia_txt'] for r in base}
    dias = [{'valor': k, 'texto': dias_texto[k], 'total': dias_conteo[k]}
            for k in sorted(dias_conteo, reverse=True)]

    filtrados = [r for r in base if not dia or r['dia'] == dia]

    tipos_conteo = Counter(r['tipo'] for r in registros)
    tipos = [{'tipo': k, 'total': tipos_conteo[k]} for k in sorted(tipos_conteo)]

    return jsonify({
        'total': len(filtrados),
        'registros': [{
            'fecha': r['fecha_txt'],
            'tipo': r['tipo'],
            'detalle': r['detalle'] + (' [' + r['tag'] + ']' if r['tag'] else ''),
            'estado': r['estado'],
            'duracion': r['duracion'],
            'ip': r['ip'],
        } for r in filtrados[:200]],
        'dias': dias,
        'tipos': tipos,
    })


@app.route('/api/usuarios')
def api_usuarios():
    """Usuarios del portal. Incluye la contraseña porque solo el administrador accede a esta ruta."""
    pendientes, totales = {}, {}
    asig_pend, asig_total = {}, {}
    for t in db.tickets.find({}, {'usuario.username': 1, 'estado': 1, 'asignado_a': 1}):
        resuelto = normalizar(t.get('estado')) == 'RESUELTO'
        nombre = (t.get('usuario') or {}).get('username')
        totales[nombre] = totales.get(nombre, 0) + 1
        if not resuelto:
            pendientes[nombre] = pendientes.get(nombre, 0) + 1
        idc = t.get('asignado_a')
        if idc:
            asig_total[idc] = asig_total.get(idc, 0) + 1
            if not resuelto:
                asig_pend[idc] = asig_pend.get(idc, 0) + 1

    usuarios = []
    for u in db.users.find({}).sort('username', 1):
        nombre = u.get('username')
        rol = u.get('rol', 'USUARIO')
        es_idc = rol == 'IDC'
        usuarios.append({
            'username': nombre,
            'password': u.get('password', ''),
            'rol': rol,
            'puesto': u.get('puesto'),
            'prioridad_base': u.get('prioridad_base'),
            'status': u.get('status', 'ACTIVE'),
            'tickets_pendientes': (asig_pend if es_idc else pendientes).get(nombre, 0),
            'tickets_total': (asig_total if es_idc else totales).get(nombre, 0),
        })
    return jsonify({'puestos': PUESTOS, 'usuarios': usuarios})


@app.route('/api/tickets')
def api_tickets():
    """Tablero de pendientes. Parámetro opcional q: número de ticket o nombre de usuario."""
    asegurar_numeros()
    q = request.args.get('q', '').strip()
    q_num = int(q.lstrip('#')) if q.lstrip('#').isdigit() else None
    columnas = {p: [] for p in PRIORIDADES_ORDEN}

    for t in db.tickets.find().sort('_id', 1):
        usuario = t.get('usuario', {}) or {}
        puesto = usuario.get('puesto')
        tipo = tipo_canonico(t.get('tipo_ticket'))
        clave, total, pp, pt = calcular_prioridad(puesto, tipo)

        etiqueta = ETIQUETAS[clave]
        if t.get('prioridad') != etiqueta:
            db.tickets.update_one({'_id': t['_id']}, {'$set': {'prioridad': etiqueta}})

        if normalizar(t.get('estado')) == 'RESUELTO':
            continue

        # Búsqueda por número de ticket, o por nombre de usuario (todos sus pendientes)
        if q:
            if q_num is not None:
                if t.get('numero') != q_num:
                    continue
            elif q.lower() not in (usuario.get('username') or '').lower():
                continue

        columnas[clave].append({
            'id': str(t.get('_id')),
            'numero': t.get('numero'),
            'fecha': fecha_local(t.get('fecha_creacion') or t['_id'].generation_time),
            'usuario': usuario.get('username'),
            'puesto': puesto,
            'tipo': tipo,
            'afectado': t.get('detalle_afectado'),
            'modalidad': t.get('modalidad'),
            'descripcion': t.get('descripcion'),
            'estado': t.get('estado'),
            'asignado_a': t.get('asignado_a'),
            'resolucion_idc': t.get('resolucion_idc'),
            'fecha_resolucion_idc': fecha_local(t.get('fecha_resolucion_idc')) if t.get('fecha_resolucion_idc') else None,
            'puntaje': total,
            'regla': f"{puesto or 'Sin puesto'} {pp} + {tipo} {pt}",
            'peso_puesto': pp,
            'peso_tipo': pt,
        })

    for lista in columnas.values():
        lista.sort(key=lambda x: (-x['peso_tipo'], x['tipo'], -x['peso_puesto'], x['numero'] or 0))

    resultado = dict(columnas)
    resultado['idcs'] = [u['username'] for u in
                         db.users.find({'rol': 'IDC', 'status': {'$ne': 'LOCKED'}}, {'username': 1}).sort('username', 1)]
    return jsonify(resultado)


@app.route('/api/resueltos')
def api_resueltos():
    filas = filas_resueltos()
    return jsonify({'total': len(filas), 'tickets': filas[:100]})


@app.route('/exportar/resueltos.csv')
def exportar_resueltos():
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(['ID', 'Fecha del ticket', 'Tipo de fallo', 'Modalidad de la falla',
                       'Equipo comprometido', 'Problema', 'Resolución'])
    for f in filas_resueltos():
        escritor.writerow([celda_csv(f['numero']), celda_csv(f['fecha']), celda_csv(f['tipo']),
                           celda_csv(f['modalidad']), celda_csv(f['equipo']), celda_csv(f['problema']),
                           celda_csv(f['resolucion'] or '(sin registro)')])
    nombre = 'tickets_resueltos_%s.csv' % datetime.now().strftime('%Y%m%d_%H%M')
    return Response(salida.getvalue().encode('utf-8-sig'), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=' + nombre})


@app.route('/api/metricas')
def api_metricas():
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
        creado = a_utc(t.get('fecha_creacion') or t['_id'].generation_time)
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