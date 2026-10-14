#!/bin/sh
if [ -f /keys/id_rsa ]; then
    mkdir -p /root/.ssh
    cp /keys/id_rsa /root/.ssh/id_rsa
    sed -i 's/\r$//' /root/.ssh/id_rsa
    chmod 700 /root/.ssh
    chmod 600 /root/.ssh/id_rsa
else
    echo "AVISO: no se encontró /keys/id_rsa; la conexión SSH a los servidores fallará."
fi

exec "$@"