import json
import os
from dotenv import load_dotenv
import requests

# ── Cargar variables de entorno si existen ──────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, ".env"))

API_KEY = os.getenv("API_KEY", "reqres_92dd24390cf940678a9d0cf8497b1769")

# Headers requeridos para evitar bloqueos y autenticar en ReqRes
HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json",
    "User-Agent": "PostmanRuntime/7.39.0",
}


# ── 1. Clasificar un código de estado por categoría ──────────────
def clasificar_status(codigo):
    """Devuelve un dict con categoría, nombre y acción sugerida."""
    if 200 <= codigo <= 299:
        return {
            "categoria": "2xx",
            "tipo": "Éxito",
            "accion": "Procesar la respuesta normalmente",
        }
    elif 300 <= codigo <= 399:
        return {
            "categoria": "3xx",
            "tipo": "Redirección",
            "accion": "Seguir la redirección o actualizar la URL",
        }
    elif codigo == 400:
        return {
            "categoria": "4xx",
            "tipo": "Bad Request",
            "accion": (
                "Revisar la sintaxis del cuerpo de la petición"
                " (JSON, parámetros)"
            ),
        }
    elif codigo == 401:
        return {
            "categoria": "4xx",
            "tipo": "Unauthorized",
            "accion": (
                "Verificar token, clave API o credenciales de"
                " autenticación"
            ),
        }
    elif codigo == 403:
        return {
            "categoria": "4xx",
            "tipo": "Forbidden",
            "accion": "Verificar permisos del token o usuario",
        }
    elif codigo == 404:
        return {
            "categoria": "4xx",
            "tipo": "Not Found",
            "accion": "Verificar que el ID o la ruta de la URL sea correcta",
        }
    elif codigo == 429:
        return {
            "categoria": "4xx",
            "tipo": "Too Many Requests",
            "accion": "Esperar antes de reintentar (rate limit)",
        }
    elif 500 <= codigo <= 599:
        return {
            "categoria": "5xx",
            "tipo": "Error del servidor",
            "accion": (
                "El problema está en el servidor, no en tu código."
                " Reportar."
            ),
        }

    return {
        "categoria": "desconocido",
        "tipo": "?",
        "accion": "Consultar documentación",
    }


# ── 2. Hacer petición y generar registro de diagnóstico ──────────
def diagnosticar_url(metodo, url, **kwargs):
    """Realiza la petición y devuelve un dict con todo el diagnóstico."""
    try:
        # Asignar headers por defecto si no vienen especificados
        if "headers" not in kwargs:
            kwargs["headers"] = HEADERS

        r = requests.request(metodo, url, timeout=8, **kwargs)
        info = clasificar_status(r.status_code)

        return {
            "url": url,
            "metodo": metodo.upper(),
            "status": r.status_code,
            "categoria": info["categoria"],
            "tipo": info["tipo"],
            "accion": info["accion"],
            "exitoso": 200 <= r.status_code <= 299,
        }
    except requests.exceptions.Timeout:
        return {
            "url": url,
            "metodo": metodo.upper(),
            "error": "Timeout",
            "accion": (
                "Aumentar el tiempo de espera o revisar latencia de"
                " red"
            ),
            "exitoso": False,
        }
    except requests.exceptions.ConnectionError:
        return {
            "url": url,
            "metodo": metodo.upper(),
            "error": "Sin conexión",
            "accion": "Verificar red y URL",
            "exitoso": False,
        }


# ── 3. Generar la tabla de diagnóstico en JSON ───────────────────
def generar_tabla_diagnostico(pruebas, archivo_salida="diagnostico.json"):
    """Pruebas: lista de dicts con claves 'metodo' y 'url'."""
    resultados = []

    for prueba in pruebas:
        # Extraer metodo y url, pasando el resto de parámetros (como json, headers, etc.)
        metodo = prueba.pop("metodo") if "metodo" in prueba else "GET"
        url = prueba.pop("url")

        resultado = diagnosticar_url(metodo=metodo, url=url, **prueba)
        resultados.append(resultado)

        estado = "✅" if resultado.get("exitoso") else "❌"
        status_display = resultado.get("status", "ERR")
        print(f"{estado} {resultado['metodo']:6} {status_display} — {url}")

    exitosas_count = sum(
        1 for r in resultados if r.get("exitoso") is True
    )

    tabla = {
        "total_pruebas": len(resultados),
        "exitosas": exitosas_count,
        "fallidas": len(resultados) - exitosas_count,
        "resultados": resultados,
    }

    with open(archivo_salida, "w", encoding="utf-8") as f:
        json.dump(tabla, f, indent=2, ensure_ascii=False)

    return tabla


# ── Ejecución de pruebas ──────────────────────────────────────────
if __name__ == "__main__":
    pruebas = [
        {"metodo": "GET", "url": "https://reqres.in/api/users/1"},
        {"metodo": "GET", "url": "https://reqres.in/api/users/9999"},
        {
            "metodo": "POST",
            "url": "https://reqres.in/api/users",
            "json": {"name": "Armando", "job": "Developer"},
        },
        {"metodo": "DELETE", "url": "https://reqres.in/api/users/2"},
        {
            "metodo": "GET",
            "url": "https://jsonplaceholder.typicode.com/invalid-500-test",
        },
        {"metodo": "GET", "url": "https://reqres.in/api/unknown/23"},
    ]

    tabla = generar_tabla_diagnostico(pruebas)

    print(
        "\nResumen:",
        json.dumps(
            {
                "total": tabla["total_pruebas"],
                "exitosas": tabla["exitosas"],
                "fallidas": tabla["fallidas"],
            },
            indent=2,
        ),
    )