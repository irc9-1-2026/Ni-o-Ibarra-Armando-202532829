# Importa las librerías necesarias 
import platform  # librería para info del sistema 
import psutil    # librería para CPU y memoria 
import time
import os

# Inicialización para evitar que el primer cálculo de CPU devuelva 0.0
psutil.cpu_percent(interval=None)

def obtener_info_sistema(): 
    """Retorna un dict con información básica del sistema de manera instantánea.""" 
    return { 
        "os":      platform.system(),               # nombre del sistema operativo
        "cpu":     psutil.cpu_percent(interval=None), # Cambiado a None para evitar congelar el script 1 segundo
        "memoria": psutil.virtual_memory().percent, # porcentaje de uso de memoria RAM
    }

def top_procesos(n=5):
    """Retorna los N procesos con mayor uso de CPU de forma eficiente."""
    procesos = []
    # Pedimos solo los atributos necesarios desde el inicio para mejorar el rendimiento
    for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent']):  
        try:
            # oneshot() realiza una única lectura rápida del proceso al sistema operativo
            with proc.oneshot():
                procesos.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess): 
            pass
            
    # El "or 0" evita que el programa falle si el porcentaje de un proceso llega como None
    return sorted(procesos, key=lambda p: p['cpu_percent'] or 0, reverse=True)[:n]

# ── Bucle principal ────────────────────────────────────────────
if __name__ == "__main__":
    while True:  # condición para bucle infinito
        # Limpia la pantalla antes de imprimir los nuevos datos
        os.system('cls' if os.name == 'nt' else 'clear')
        
        info = obtener_info_sistema()
        print(f"Sistema : {info['os']}")
        print(f"CPU     : {info['cpu']}%")
        print(f"Memoria : {info['memoria']}%")
        print("\n── Top procesos ──")
        
        for p in top_procesos():
            # Controlamos que no imprima valores None visualmente
            cpu_disp = p['cpu_percent'] if p['cpu_percent'] is not None else 0.0
            print(f"  [{p['pid']}] {p['name']:20} {cpu_disp}%")
            
        time.sleep(3)  # pausa de 3 segundos antes del siguiente ciclo