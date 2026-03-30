import threading
import bitacora

class Servidor:
    def __init__(self, nombre_servidor, capacidad_maxima, ancho_banda_total):
        self.nombre_servidor = nombre_servidor
        self.capacidad_maxima = capacidad_maxima 
        self.ancho_banda_total = ancho_banda_total 
        
        self.conexiones_activas = 0  
        self.historial_trafico = [] 
        self.bytes_transferidos_totales = 0.0 
        
        self.mutex = threading.Lock() 

    def solicitar_conexion(self, id_solicitud):
        bitacora.registrar(f"Hilo {id_solicitud} EN ESPERA del candado (Entrada).")
        
        self.mutex.acquire() 
        bitacora.registrar(f"Hilo {id_solicitud} ADQUIRIÓ el candado (Entrada).")
        
        if self.conexiones_activas < self.capacidad_maxima:
            self.conexiones_activas += 1
            bitacora.registrar(f"Hilo {id_solicitud} ACEPTADO. Activas: {self.conexiones_activas}.")
            
            self.mutex.release()
            bitacora.registrar(f"Hilo {id_solicitud} LIBERÓ el candado (Entrada).")
            return True
            
        bitacora.registrar(f"Hilo {id_solicitud} RECHAZADO. Servidor lleno.")
        self.mutex.release() 
        bitacora.registrar(f"Hilo {id_solicitud} LIBERÓ el candado (Rechazo).")
        return False

    def registrar_salida(self, id_solicitud, tamano_archivo):
        bitacora.registrar(f"Hilo {id_solicitud} EN ESPERA del candado (Salida).")
        
        self.mutex.acquire() 
        bitacora.registrar(f"Hilo {id_solicitud} ADQUIRIÓ el candado (Salida).")
        
        self.conexiones_activas -= 1
        self.bytes_transferidos_totales += tamano_archivo
        
        mensaje_exito = f"ID_{id_solicitud}_EXITO_MB:{tamano_archivo}"
        self.historial_trafico.append(mensaje_exito)
        bitacora.registrar(f"Hilo {id_solicitud} REGISTRÓ SALIDA. Tráfico sumado.")
        
        self.mutex.release()
        bitacora.registrar(f"Hilo {id_solicitud} LIBERÓ el candado (Fin).")

    def generar_reporte_estado(self):
        print("="*40)
        print(f"REPORTE FINAL: {self.nombre_servidor}")
        print("="*40)
        print(f"Carga final: {self.conexiones_activas} de {self.capacidad_maxima} usuarios activos")
        print(f"Tráfico total transferido: {self.bytes_transferidos_totales:.2f} MB")
        print(f"Total de descargas exitosas: {len(self.historial_trafico)}")
        print("NOTA: Revise el archivo 'bitacora.log' para la auditoría de sincronización.")
        print("="*40 )
