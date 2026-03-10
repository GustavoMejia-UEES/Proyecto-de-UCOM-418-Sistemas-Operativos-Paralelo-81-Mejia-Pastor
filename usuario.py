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
        # Seccion critica de entrada: validacion y reserva de cupo.
        with self.servidor.mutex:
            if self.servidor.conexiones_activas < self.servidor.capacidad_maxima:
                self.servidor.conexiones_activas += 1
                solicitud_aceptada = True
            else:
                solicitud_aceptada = False

        if solicitud_aceptada:
            print(f"Solicitud {self.id_solicitud} aceptada ({self.tamano_archivo} MB).")

            # Simulación de descarga (Sección restante)
            time.sleep(random.randint(1, 3)) 

            # Seccion critica de salida: liberacion de cupo y auditoria.
            with self.servidor.mutex:
                self.servidor.conexiones_activas -= 1
                self.servidor.bytes_transferidos_totales += self.tamano_archivo
                self.servidor.historial_trafico.append(f"ID_{self.id_solicitud}_EXITO")
        else:
            print(f"Solicitud {self.id_solicitud} rechazada: Servidor lleno.")
