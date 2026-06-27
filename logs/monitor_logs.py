import re, json 
from collections import Counter 

# Patrón: "2026-06-15 08:15:47 ERROR: mensaje..." 
# Captura: Grupo 1 (Fecha/Hora), Grupo 2 (Nivel), Grupo 3 (Mensaje)
PATRON_LINEA = re.compile( 
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+([A-Z]+):\s+(.*)$" 
) 

# Patrón para capturar una IP estándar (4 octetos)
PATRON_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b") 

# ── Parsea texto ya leído (reutilizable para V1 y V2) ──────────
def parsear_texto(contenido):
    eventos = []
    for linea in contenido.splitlines():
        match = PATRON_LINEA.match(linea.strip())
        if match: # Verifica que sí hubo coincidencia
            eventos.append({
                "timestamp": match.group(1), # Grupo 1: Fecha y hora
                "nivel":     match.group(2), # Grupo 2: ERROR, INFO, etc.
                "mensaje":   match.group(3), # Grupo 3: El texto del mensaje
            })
    return eventos

# ── Lee un archivo local y lo parsea (solo V1) ──────────────────
def parsear_log(ruta="servidor.log"):
    with open(ruta, "r", encoding="utf-8") as f:
        return parsear_texto(f.read()) # Usa parsear_texto() con f.read()

# ── FASE 3: contar eventos por severidad ───────────────────────
def contar_por_nivel(eventos):
    niveles = [ev["nivel"] for ev in eventos] # Extrae el "nivel" de cada evento
    return dict(Counter(niveles))

# ── Detectar fuerza bruta: misma IP con 3+ logins fallidos ─────
def detectar_fuerza_bruta(eventos, umbral=3):
    ips_fallidas = []
    for ev in eventos:
        if ev["nivel"] == "ERROR" and "login fallido" in ev["mensaje"].lower():
            ip_match = PATRON_IP.search(ev["mensaje"])
            if ip_match:
                ips_fallidas.append(ip_match.group()) # Guarda la IP encontrada
    conteo = Counter(ips_fallidas)
    return [ip for ip, n in conteo.items() if n >= umbral] # Compara n contra umbral

# ── FASE 4: generar reporte JSON ────────────────────────────────
def generar_reporte(ruta_log="servidor.log", ruta_salida="reporte.json", contenido=None):
    # Si contenido no es None usa parsear_texto(), si no usa parsear_log(ruta_log)
    eventos = parsear_texto(contenido) if contenido is not None else parsear_log(ruta_log)
    
    reporte = {
        "total_eventos":     len(eventos),
        "eventos_por_nivel": contar_por_nivel(eventos),
        "ips_sospechosas":   detectar_fuerza_bruta(eventos),
    }
    if ruta_salida:
        with open(ruta_salida, "w", encoding="utf-8") as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
    return reporte

if __name__ == "__main__":
    # Nota: Asegúrate de tener un archivo 'servidor.log' en la misma ruta para probarlo de forma local.
    try:
        reporte = generar_reporte()
        print(json.dumps(reporte, indent=2, ensure_ascii=False))
    except FileNotFoundError:
        print("Aviso: No se encontró 'servidor.log'. Crea el archivo para probar el script localmente.")