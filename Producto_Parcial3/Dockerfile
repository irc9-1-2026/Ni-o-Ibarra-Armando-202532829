FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Apuntamos a portal_app:app en lugar de app:app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "portal_app:app"]