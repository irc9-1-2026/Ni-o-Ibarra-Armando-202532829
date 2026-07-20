import json
import os
from dotenv import load_dotenv
import requests

# ── Carga dinámica del archivo .env ───────────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, ".env"))

BASE = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")

# Headers actualizados con User-Agent
HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json",
    "User-Agent": "PostmanRuntime/7.39.0",
}


# ── GET — listar usuarios ─────────────────────────────────────
def listar_usuarios(pagina=1):
    r = requests.get(
        f"{BASE}/users", params={"page": pagina}, headers=HEADERS
    )
    return r.json() if r.status_code == 200 else {"error": r.status_code}


# ── POST — crear usuario ──────────────────────────────────────
def crear_usuario(nombre, puesto):
    r = requests.post(
        f"{BASE}/users",
        json={"name": nombre, "job": puesto},
        headers=HEADERS,
    )
    return r.json() if r.status_code == 201 else {"error": r.status_code}


# ── PUT — actualizar usuario ──────────────────────────────────
def actualizar_usuario(user_id, nombre, puesto):
    r = requests.put(
        f"{BASE}/users/{user_id}",
        json={"name": nombre, "job": puesto},
        headers=HEADERS,
    )
    return r.json() if r.status_code == 200 else {"error": r.status_code}


# ── DELETE — eliminar usuario ─────────────────────────────────
def eliminar_usuario(user_id):
    r = requests.delete(f"{BASE}/users/{user_id}", headers=HEADERS)
    return (
        {"ok": True}
        if r.status_code == 204
        else {"error": r.status_code}
    )


if __name__ == "__main__":
    print("Usuarios:", json.dumps(listar_usuarios(), indent=2))
    print(
        "Nuevo:",
        json.dumps(
            crear_usuario("Ana Torres", "Network Engineer"), indent=2
        ),
    )
    print(
        "Actualizado:",
        json.dumps(
            actualizar_usuario(2, "Ana Torres", "Senior NE"), indent=2
        ),
    )
    print("Eliminado:", json.dumps(eliminar_usuario(2), indent=2))