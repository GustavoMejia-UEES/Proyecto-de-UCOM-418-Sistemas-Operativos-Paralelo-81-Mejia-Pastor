import threading
import time
import random

class UsuarioDescarga(threading.Thread):
    def __init__(self, id_solicitud, servidor):
        super().__init__()
        self.id_solicitud = id_solicitud
        self.servidor = servidor
        self.tamano_archivo = round(random.uniform(10.0, 50.0), 2)
        self.max_intentos = 3

    def run(self):
        intentos = 0
        conectado = False
        while intentos < self.max_intentos and not conectado:
            if self.servidor.solicitar_conexion():
                conectado = True
            else:
                intentos += 1
                print(f"[!] Servidor lleno. Solicitud {self.id_solicitud} en espera... (Intento {intentos}/{self.max_intentos})")
                time.sleep(random.uniform(1.0, 2.0)) 

        if conectado:
            ancho_banda_asignado = self.servidor.ancho_banda_total / self.servidor.capacidad_maxima
            tiempo_estimado_segundos = self.tamano_archivo / ancho_banda_asignado
            print(f"[+] Solicitud {self.id_solicitud} ACEPTADA. Descargando {self.tamano_archivo} MB. (Tiempo est: {tiempo_estimado_segundos:.2f}s)")
            bloques = 3
            tiempo_por_bloque = tiempo_estimado_segundos / bloques
            
            for i in range(bloques):
                time.sleep(tiempo_por_bloque)
                print(f"   -> [Descargando] Solicitud {self.id_solicitud}: {int(((i+1)/bloques)*100)}%")

            self.servidor.registrar_salida(self.id_solicitud, self.tamano_archivo)
            print(f"[-] Solicitud {self.id_solicitud} COMPLETADA. Cupo liberado.")
        
        else:
            print(f"[x] Solicitud {self.id_solicitud} CANCELADA por Timeout: No se logró conseguir cupo.")