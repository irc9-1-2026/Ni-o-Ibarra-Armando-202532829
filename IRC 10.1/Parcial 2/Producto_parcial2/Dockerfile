FROM python:3.12-slim

# Dependencias esenciales: ansible y cliente SSH
RUN apt-get update && apt-get install -y \
    ansible \
    openssh-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir flask pymongo

COPY . /app

# Quita saltos de línea de Windows y deja ejecutable el entrypoint (instala la llave SSH)
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["sh", "/app/entrypoint.sh"]
CMD ["python", "app/app.py"]