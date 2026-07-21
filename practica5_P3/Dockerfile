# Imagen base ligera
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# Copiar dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código y la carpeta de plantillas
COPY app.py .
COPY test_app.py .
COPY templates/ ./templates/

# Puerto interno expuesto
EXPOSE 5000

# Arrancar con Gunicorn
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]