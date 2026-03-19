import threading
import time
import random
import bitacora

class UsuarioDescarga(threading.Thread):
    def __init__(self, id_solicitud, servidor):
        super().__init__()
        self.id_solicitud = id_solicitud
        self.servidor = servidor
        self.tamano_archivo = round(random.uniform(5.0, 50.0), 2)
        self.max_intentos = 3

    def run(self):
        intentos = 0
        conectado = False

        bitacora.registrar(f"Usuario {self.id_solicitud} INICIADO. Intentando conectar...")

        while intentos < self.max_intentos and not conectado:
            if self.servidor.solicitar_conexion(self.id_solicitud):
                conectado = True
            else:
                intentos += 1
                print(f"[!] Servidor lleno. Solicitud {self.id_solicitud} en espera... (Intento {intentos}/{self.max_intentos})")
                time.sleep(1) 

        if conectado:
            print(f"[+] Solicitud {self.id_solicitud} ACEPTADA ({self.tamano_archivo} MB). Descargando...")
            
            time.sleep(random.uniform(1, 3)) 

            self.servidor.registrar_salida(self.id_solicitud, self.tamano_archivo)
            print(f"[-] Solicitud {self.id_solicitud} COMPLETADA. Cupo liberado.")
        else:
            print(f"[x] Solicitud {self.id_solicitud} CANCELADA por Timeout tras {self.max_intentos} intentos.")
            bitacora.registrar(f"Usuario {self.id_solicitud} ABANDONÓ el sistema por Timeout.")
            