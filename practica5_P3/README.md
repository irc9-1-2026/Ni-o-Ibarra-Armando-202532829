Ventajas Clave de usar Docker frente al Deploy Directo

1. **Entorno 100% Reproducible:** Elimina errores de "funciona en mi máquina pero no en el servidor". Todo viene empaquetado en la imagen.
2. **Aislamiento y Seguridad:** Flask no se expone directamente a internet (puerto 5000 cerrado). Nginx actúa como proxy inverso en el puerto 80 por una red interna privada.
3. **Despliegue Simplificado:** No requiere instalar librerías manualmente en el servidor. Con un solo comando (`docker compose up --build -d`) arranca toda la arquitectura.

---

## Verificación del Proxy Inverso

- `curl localhost:5000` -> **Falla/Conexión rechazada** (Demuestra que Flask está aislado).
- `curl localhost` -> **Respuesta 200 OK** (Nginx recibe en el puerto 80 y lo reenvía internamente a Flask).