from flask import Flask, render_template, jsonify 
import platform  
import psutil    

app = Flask(__name__) 

# Inicialización en segundo plano de la CPU
psutil.cpu_percent(interval=None)

def obtener_top_procesos(n=5):
    procesos = []
    num_cpus = psutil.cpu_count() or 1 
    
    # Usamos un bloque try global por si el sistema operativo bloquea el acceso inicial
    try:
        for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent']):
            try:
                with proc.oneshot():
                    info = proc.info
                    if info['pid'] == 0 or 'idle' in (info['name'] or '').lower():
                        continue
                    
                    if info['cpu_percent'] is not None:
                        info['cpu_percent'] = round(info['cpu_percent'] / num_cpus, 1)
                    else:
                        info['cpu_percent'] = 0.0
                        
                    procesos.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception:
        return [] # Retorna lista vacía temporal si el SO está ocupado
            
    return sorted(procesos, key=lambda p: p['cpu_percent'], reverse=True)[:n]

@app.route("/") 
def index(): 
    # Forzamos explícitamente a Flask a renderizar el archivo de la carpeta templates
    return render_template("index.html")

@app.route("/datos") 
def datos(): 
    return jsonify({ 
        "os":       platform.system(),              
        "cpu":      psutil.cpu_percent(interval=None), 
        "memoria":  psutil.virtual_memory().percent, 
        "procesos": obtener_top_procesos()          
    })

if __name__ == "__main__": 
    app.run(debug=True)