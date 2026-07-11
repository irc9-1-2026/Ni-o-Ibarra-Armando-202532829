from flask import Flask, jsonify, request 

app = Flask(__name__) 

# Base de datos en memoria (lista de dicts) 
dispositivos = [ 
    {"id": 1, "nombre": "SW-Core-01", "tipo": "switch",  "ip": "10.0.0.1", "estado": "activo"}, 
    {"id": 2, "nombre": "RT-Edge-01", "tipo": "router",  "ip": "10.0.0.2", "estado": "activo"}, 
    {"id": 3, "nombre": "FW-DMZ-01",  "tipo": "firewall", "ip": "10.0.0.3", "estado": "inactivo"}, 
] 
siguiente_id = 4   # contador para nuevos IDs 

# ── GET /dispositivos — listar todos ────────────────────────── 
@app.route("/dispositivos", methods=["GET"]) 
def listar(): 
    # jsonify con la lista y status 200
    return jsonify(dispositivos), 200 

# ── GET /dispositivos/<id> — buscar uno ────────────────────── 
@app.route("/dispositivos/<int:device_id>", methods=["GET"]) 
def obtener(device_id): 
    disp = next((d for d in dispositivos if d["id"] == device_id), None) 
    if disp is None: 
        # Error y status 404
        return jsonify({"error": "Dispositivo no encontrado"}), 404 
    # jsonify el dispositivo con status 200
    return jsonify(disp), 200 

# ── POST /dispositivos — agregar nuevo ──────────────────────── 
@app.route("/dispositivos", methods=["POST"]) 
def agregar(): 
    global siguiente_id 
    # Leer JSON del body de la petición
    datos = request.get_json() 
    nuevo = { 
        "id":     siguiente_id, 
        "nombre": datos.get("nombre", "Sin nombre"), 
        "tipo":   datos.get("tipo", "desconocido"), 
        "ip":     datos.get("ip", "0.0.0.0"), 
        "estado": datos.get("estado", "activo"), 
    } 
    dispositivos.append(nuevo) 
    siguiente_id += 1 
    # Status 201 cuando se crea un recurso
    return jsonify(nuevo), 201 

# ── PUT /dispositivos/<id> — actualizar completo ───────────── 
@app.route("/dispositivos/<int:device_id>", methods=["PUT"]) 
def actualizar(device_id): 
    disp = next((d for d in dispositivos if d["id"] == device_id), None) 
    if disp is None: 
        return jsonify({"error": "No encontrado"}), 404 
    datos = request.get_json() 
    disp["nombre"] = datos.get("nombre", disp["nombre"]) 
    disp["tipo"]   = datos.get("tipo",   disp["tipo"]) 
    disp["ip"]     = datos.get("ip",     disp["ip"]) 
    # Actualizar estado igual que los anteriores
    disp["estado"] = datos.get("estado", disp["estado"]) 
    # jsonify el dispositivo actualizado con status 200
    return jsonify(disp), 200 

# ── DELETE /dispositivos/<id> — eliminar ───────────────────── 
@app.route("/dispositivos/<int:device_id>", methods=["DELETE"]) 
def eliminar(device_id): 
    global dispositivos 
    original = len(dispositivos) 
    # Filtrar manteniendo los que NO coinciden con el ID que se quiere borrar
    dispositivos = [d for d in dispositivos if d["id"] != device_id] 
    if len(dispositivos) == original: 
        return jsonify({"error": "No encontrado"}), 404 
    # Retorna un body vacío y status 204 cuando no hay contenido de vuelta
    return "", 204 

if __name__ == "__main__": 
    app.run(debug=True, port=5000)