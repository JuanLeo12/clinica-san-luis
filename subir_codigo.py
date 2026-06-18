import socket
import time
import base64
import sys
import os

# ¡AQUÍ ESTÁ EL CAMBIO CLAVE! Agregamos hx711.py a la lista
ARCHIVOS = ['ssd1306.py', 'hx711.py', 'main.py']
PUERTO_WOKWI = 4000

def esperar_prompt(conexion):
    buffer = b""
    while True:
        try:
            char = conexion.recv(1)
            if not char:
                break
            buffer += char
            if buffer[-4:] == b">>> ":
                break
        except socket.timeout:
            break

def enviar_sincronizado(conexion, comando):
    conexion.sendall(comando.encode('utf-8'))
    esperar_prompt(conexion)

def subir_archivo(conexion, nombre_archivo):
    if not os.path.exists(nombre_archivo):
        print(f"[X] Error: No se encontro '{nombre_archivo}'.")
        sys.exit(1)
        
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as f:
            texto = f.read()
    except UnicodeDecodeError:
        with open(nombre_archivo, 'r', encoding='windows-1252') as f:
            texto = f.read()
            
    texto = texto.replace('\xa0', ' ')
    b64 = base64.b64encode(texto.encode('utf-8')).decode('utf-8')
    
    print(f"-> Escribiendo {nombre_archivo} de forma sincronizada...")
    
    enviar_sincronizado(conexion, f"import ubinascii; f=open('{nombre_archivo}', 'wb')\r\n")
    
    chunk_size = 60
    total_chunks = (len(b64) // chunk_size) + 1
    
    for i, idx in enumerate(range(0, len(b64), chunk_size), 1):
        pedazo = b64[idx:idx+chunk_size]
        enviar_sincronizado(conexion, f"f.write(ubinascii.a2b_base64(b'{pedazo}'))\r\n")
        
        if i % 10 == 0 or i == total_chunks:
            print(f"   Progreso: {i}/{total_chunks} bloques subidos...")
            
    enviar_sincronizado(conexion, "f.close()\r\n")

print("==================================================")
print("   Subida Inteligente a Wokwi (Flujo Sincronizado)")
print("==================================================")

try:
    conexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conexion.settimeout(2.0) 
    conexion.connect(('127.0.0.1', PUERTO_WOKWI))
except Exception as e:
    print("[X] Error de conexion. Asegurate de darle Play a Wokwi primero.")
    sys.exit(1)

conexion.sendall(b'\r\n\r\n')
esperar_prompt(conexion)

for archivo in ARCHIVOS:
    subir_archivo(conexion, archivo)

print("\n-> Ejecutando el monitor clinico...")
conexion.sendall(b"exec(open('main.py', encoding='utf-8').read())\r\n")

time.sleep(0.5)
conexion.close()
print("==================================================")
print("   Inyeccion completada. Revisa el simulador.     ")
print("==================================================")