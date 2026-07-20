import requests, json, os 
from dotenv import load_dotenv 
load_dotenv() 

BASE    = os.getenv("BASE_URL") 
API_KEY = os.getenv("API_KEY") 

# Headers que se reutilizan en todas las peticiones 
HEADERS = {
    "x-api-key": API_KEY,  # Se inyecta la API Key desde la variable de entorno
    "Content-Type": "application/json",
}

# ── GET — listar usuarios ─────────────────────────────────────
def listar_usuarios(pagina=1):
    r = requests.get(
        f"{BASE}/users",
        params={"page": pagina},  # Envío de parámetros de consulta de forma limpia
        headers=HEADERS
    )
    return r.json() if r.status_code == 200 else {"error": r.status_code}

# ── POST — crear usuario ──────────────────────────────────────
def crear_usuario(nombre, puesto):
    r = requests.post(
        f"{BASE}/users",
        json={"name": nombre, "job": puesto},
        headers=HEADERS
    )
    return r.json() if r.status_code == 201 else {"error": r.status_code}

# ── PUT — actualizar usuario ──────────────────────────────────
def actualizar_usuario(user_id, nombre, puesto):
    # Verbo PUT para actualizaciones completas
    r = requests.put(
        f"{BASE}/users/{user_id}",
        json={"name": nombre, "job": puesto},
        headers=HEADERS
    )
    return r.json() if r.status_code == 200 else {"error": r.status_code}

# ── DELETE — eliminar usuario ─────────────────────────────────
def eliminar_usuario(user_id):
    # Verbo DELETE para eliminar recursos
    r = requests.delete(f"{BASE}/users/{user_id}", headers=HEADERS)
    # Al igual que en Postman, ReqRes responde con un 204 No Content ante un borrado exitoso
    return {"ok": True} if r.status_code == 204 else {"error": r.status_code}

if __name__ == "__main__":
    print("Usuarios:",  json.dumps(listar_usuarios(), indent=2))
    print("Nuevo:",     json.dumps(crear_usuario("Ana Torres", "Network Engineer"), indent=2))
    print("Actualizado:",json.dumps(actualizar_usuario(2, "Ana Torres", "Senior NE"), indent=2))
    print("Eliminado:", json.dumps(eliminar_usuario(2), indent=2))
# Practica 1 completada
