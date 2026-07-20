Práctica 2: Postman y Autenticación con REST APIs

Este proyecto extiende el consumo de la API de ReqRes incorporando autenticación mediante cabeceras HTTP (`x-api-key`) y el uso de variables de entorno con `python-dotenv` para proteger las credenciales sensibles.

---

## 🚀 Cómo levantar y probar

Abre tu terminal en la carpeta de la práctica:
   ```bash
   cd practica2_P3

Instala las dependencias necesarias:
pip install requests python-dotenv

Crea un archivo .env en la raíz de esta carpeta basándote en la plantilla .env.example:
BASE_URL=[https://reqres.in/api](https://reqres.in/api)
API_KEY=tu_api_key_aqui

Ejecuta el script principal:
python usuarios_api.py