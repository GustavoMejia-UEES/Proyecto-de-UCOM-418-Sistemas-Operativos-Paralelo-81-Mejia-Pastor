import time
import threading

# Mutex exclusivo para la bitácora
_log_mutex = threading.Lock()
ARCHIVO_LOG = "bitacora.log"

def limpiar():
    _log_mutex.acquire()
    
    archivo = open(ARCHIVO_LOG, "w")
    archivo.write("=== INICIO DE NUEVA SIMULACIÓN ===\n")
    archivo.close()
    
    _log_mutex.release()

def registrar(mensaje):
    timestamp = int(time.time() * 1000)
    
    _log_mutex.acquire()
    
    archivo = open(ARCHIVO_LOG, "a")
    archivo.write(f"[{timestamp}] {mensaje}\n")
    archivo.close()
    
    _log_mutex.release() 