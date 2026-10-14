FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends openssh-client sshpass && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ansible.cfg inventory.ini ./
COPY app/ ./app/
COPY entrypoint.sh /entrypoint.sh

RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

ENV ANSIBLE_CONFIG=/app/ansible.cfg

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "app/app.py"]