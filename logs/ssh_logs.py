import paramiko 

def leer_log_remoto(host, usuario, password, ruta_remota, puerto=22, timeout=8): 
    """Se conecta por SSH y devuelve el contenido del archivo remoto.""" 
    cliente = paramiko.SSHClient() 
    # política para hosts nuevos: añade automáticamente la llave si no está en known_hosts
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
    try: 
        cliente.connect( 
            hostname=host, 
            port=puerto, 
            username=usuario, 
            password=password, 
            timeout=timeout, 
        ) 
        # Pista: 'cat archivo' imprime el contenido completo a stdout 
        stdin, stdout, stderr = cliente.exec_command(f"cat '{ruta_remota}'") 
        # lee stdout y decodifícalo a texto (utf-8) 
        contenido = stdout.read().decode("utf-8") 
        error = stderr.read().decode("utf-8", errors="replace") 
        if error: 
            raise FileNotFoundError(error.strip()) 
        return contenido 
    finally: 
        cliente.close() # cierra la conexión siempre, haya o no error