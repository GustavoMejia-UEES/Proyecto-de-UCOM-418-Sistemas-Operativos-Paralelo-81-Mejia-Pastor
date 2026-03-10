import threading
import time
import random

class UsuarioDescarga(threading.Thread):
    def __init__(self, id_solicitud, servidor):
        super().__init__()
        self.id_solicitud = id_solicitud
        self.servidor = servidor
        self.tamano_archivo = round(random.uniform(5.0, 50.0), 2)

    def run(self):
        # --- SECCIÓN CRÍTICA: Entrada ---
        self.servidor.mutex.acquire() 
        if self.servidor.conexiones_activas < self.servidor.capacidad_maxima:
            self.servidor.conexiones_activas += 1
            print(f"Solicitud {self.id_solicitud} aceptada ({self.tamano_archivo} MB).")
            self.servidor.mutex.release() 

            # Simulación de descarga (Sección restante)
            time.sleep(random.randint(1, 3)) 

            # --- SECCIÓN CRÍTICA: Salida y Registro ---
            self.servidor.mutex.acquire()
            self.servidor.conexiones_activas -= 1
            self.servidor.bytes_transferidos_totales += self.tamano_archivo
            self.servidor.historial_trafico.append(f"ID_{self.id_solicitud}_EXITO")
            self.servidor.mutex.release()
        else:
            self.servidor.mutex.release()
            print(f"Solicitud {self.id_solicitud} rechazada: Servidor lleno.")