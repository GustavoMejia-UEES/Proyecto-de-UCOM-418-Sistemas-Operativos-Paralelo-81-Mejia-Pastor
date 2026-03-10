import threading
from datetime import datetime

class Servidor:
    
    def __init__(self, nombre_servidor, capacidad_maxima, ancho_banda_total):
        # Atributos de identificación y capacidad
        self.nombre_servidor = nombre_servidor
        self.capacidad_maxima = capacidad_maxima 
        self.ancho_banda_total = ancho_banda_total 
        
        # RECURSOS COMPARTIDOS (Objetos de la Sección Crítica)
        self.conexiones_activas = 0  
        self.historial_trafico = [] 
        self.bytes_transferidos_totales = 0.0 
        
        # MECANISMO DE CONTROL (Sincronización)
        self.mutex = threading.Lock() 

    def generar_reporte_estado(self):
        print(f"REPORTE: {self.nombre_servidor}")
        print(f"Carga actual: {self.conexiones_activas} de {self.capacidad_maxima} usuarios")
        print(f"Tráfico total: {self.bytes_transferidos_totales} MB")
        print(f"Logs generados: {len(self.historial_trafico)}")
        print(f"Disponibilidad: {'ALTA' if self.conexiones_activas < self.capacidad_maxima else 'LLENO'}")
