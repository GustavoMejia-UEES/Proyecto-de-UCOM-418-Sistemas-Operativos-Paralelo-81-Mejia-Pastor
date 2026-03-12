import threading
import time

class Servidor:
    
    def __init__(self, nombre_servidor, capacidad_maxima, ancho_banda_total):
        self.nombre_servidor = nombre_servidor
        self.capacidad_maxima = capacidad_maxima 
        self.ancho_banda_total = ancho_banda_total 
        
        # RECURSOS COMPARTIDOS 
        self.conexiones_activas = 0  
        self.historial_trafico = [] 
        self.bytes_transferidos_totales = 0.0 
        
        # MECANISMO DE CONTROL (Mutex explícito como en clase)
        self.mutex = threading.Lock() 

    def escribir_log(self, mensaje):
        archivo = open("servidor-trafico.log", "a")
        archivo.write(mensaje)
        archivo.close()

    def solicitar_conexion(self):
        self.mutex.acquire() # BLOQUEAMOS EL CANDADO
        
        if self.conexiones_activas < self.capacidad_maxima:
            self.conexiones_activas += 1
            self.mutex.release() # LIBERAMOS SI ENTRA
            return True
            
        self.mutex.release() # LIBERAMOS SI ESTÁ LLENO (Rechazado)
        return False

    def registrar_salida(self, id_solicitud, tamano_archivo):
        self.mutex.acquire() # BLOQUEAMOS EL CANDADO
        
        # Modificamos los recursos compartidos
        self.conexiones_activas -= 1
        self.bytes_transferidos_totales += tamano_archivo
        
        # Generamos el log
        mensaje_log = f"[{int(time.time() * 1000)}] EXITOSO - ID: {id_solicitud} - Descarga: {tamano_archivo} MB\n"
        self.historial_trafico.append(mensaje_log.strip())
        self.escribir_log(mensaje_log)
        
        self.mutex.release() # LIBERAMOS EL CANDADO AL TERMINAR

    def generar_reporte_estado(self):
        print("\n" + "="*40)
        print(f"REPORTE FINAL: {self.nombre_servidor}")
        print("="*40)
        print(f"Carga final: {self.conexiones_activas} de {self.capacidad_maxima} usuarios activos")
        print(f"Tráfico total transferido: {self.bytes_transferidos_totales:.2f} MB")
        print(f"Total de descargas exitosas: {len(self.historial_trafico)}")
        print("NOTA: Revise el archivo 'servidor-trafico.log' para la auditoría completa.")
        print("="*40 + "\n")