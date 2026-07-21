## Estructura del Proyecto

```text
practica4_P3/
│
├── app.py              # Aplicación principal Flask (rutas y lógica de métricas)
├── test_app.py         # Pruebas unitarias con unittest
├── requirements.txt    # Dependencias de Python (Flask, etc.)
├── README.md           # Documentación general de la práctica
│
├── capturas/           # Evidencias fotográficas del funcionamiento y CI/CD
│   ├── dashboard.png       # Muestra del Dashboard corriendo en la IP de Rocky Linux
│   └── github_actions.png  # Evidencia del Pipeline CI/CD exitoso (Jobs: test & deploy)
│
└── templates/          # Plantillas HTML
    └── index.html      # Interfaz gráfica del Dashboard

## Tecnologías Utilizadas

- **Lenguaje:** Python 3.10+
- **Framework Web:** Flask
- **Pruebas Unitarias:** `unittest`
- **Servidor de Producción/Pruebas:** Rocky Linux (IP: `192.168.233.165`)
- **CI/CD:** GitHub Actions
- **Control de Versiones:** Git & GitHub