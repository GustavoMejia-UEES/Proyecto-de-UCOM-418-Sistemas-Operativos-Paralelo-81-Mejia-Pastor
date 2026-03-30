import threading
import logging
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
        
        # PUERTOS/NODOS DISPONIBLES (Estructura de recursos específicos)
        self.puertos_disponibles = {i: "LIBRE" for i in range(1, capacidad_maxima + 1)}
        self.asignaciones = {}  # usuario_id -> {puerto, tipo_archivo, ancho_banda}
        self.ancho_banda_consumido = 0.0
        
        # MECANISMO DE CONTROL (Sincronización)
        self.mutex = threading.Lock()
        
        # SISTEMA DE BITÁCORA (Thread-safe con logging nativo)
        self._configurar_bitacora()

    def _configurar_bitacora(self):
        """
        Configura el sistema de logging para registrar en bitacora.log
        usando la librería nativa 'logging' de Python (thread-safe).
        Formato profesional con niveles: [INFO], [WARN], [ERROR], [MUTEX]
        """
        logger = logging.getLogger('servidor_descarga')
        logger.setLevel(logging.INFO)
        
        # EVITAR DUPLICADOS: limpiar handlers si ya existen
        if logger.handlers:
            logger.handlers.clear()
        
        # Handler para archivo (bitacora.log)
        file_handler = logging.FileHandler('bitacora.log', mode='w', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Formato estructurado: [TIMESTAMP] [NIVEL] [TIPO_EVENTO] [HILO_ID] [NODO_ASIGNADO] -> Descripción
        formatter = logging.Formatter('[%(asctime)s.%(msecs)03d] %(message)s', 
                                      datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        self.logger = logger

    def registrar_evento(self, usuario_id, nivel, tipo_evento, nodo_asignado="-", descripcion=""):
        """
        Registra un evento estructurado en la bitácora.
        
        Args:
            usuario_id: ID del usuario/hilo
            nivel: [INFO], [WARN], [ERROR], [MUTEX]
            tipo_evento: CONNECT, DISCONNECT, REJECT, WAIT
            nodo_asignado: Número de puerto/nodo o "-"
            descripcion: Descripción adicional
        """
        mensaje = f"[{nivel}] [{tipo_evento}] [Hilo_{usuario_id}] -> Nodo {nodo_asignado}: {descripcion}"
        self.logger.info(mensaje)

    def solicitar_conexion(self, usuario_id, tipo_archivo="TEXTO", ancho_banda_requerido=10):
        """
        Intenta adquirir el Mutex para acceder a un puerto/nodo específico.
        Usa mutex.acquire() de forma explícita.
        Retorna (éxito: bool, puerto_asignado: int o None, ancho_banda_asignado: float)
        
        Args:
            usuario_id: ID del usuario
            tipo_archivo: TEXTO, IMAGEN o VIDEO
            ancho_banda_requerido: Ancho de banda que necesita este usuario
        """
        # ANTES del Mutex: registrar INTENTO
        self.registrar_evento(usuario_id, "MUTEX", "WAIT", "-", 
                            f"Esperando Mutex. Requiere: {ancho_banda_requerido}MB, Tipo: {tipo_archivo}")
        
        # ====== ADQUIRIR MUTEX EXPLÍCITAMENTE =======
        self.mutex.acquire()
        try:
            # ====== DENTRO DE LA SECCIÓN CRÍTICA =======
            
            # Buscar el primer puerto libre
            puerto_libre = None
            for puerto, estado in self.puertos_disponibles.items():
                if estado == "LIBRE":
                    puerto_libre = puerto
                    break
            
            # Verificar si hay ancho de banda disponible
            ancho_banda_disponible = self.ancho_banda_total - self.ancho_banda_consumido
            
            if puerto_libre is not None and ancho_banda_disponible >= ancho_banda_requerido:
                # ASIGNACIÓN EXITOSA
                self.puertos_disponibles[puerto_libre] = f"OCUPADO_Usuario{usuario_id}"
                self.asignaciones[usuario_id] = {
                    'puerto': puerto_libre,
                    'tipo_archivo': tipo_archivo,
                    'ancho_banda': ancho_banda_requerido,
                    'timestamp_inicio': datetime.now()
                }
                self.conexiones_activas += 1
                self.ancho_banda_consumido += ancho_banda_requerido
                
                # Registrar CONNECT exitoso
                self.registrar_evento(usuario_id, "INFO", "CONNECT", puerto_libre,
                                    f"Asignado al Nodo {puerto_libre}. Ancho de banda restante: {ancho_banda_disponible - ancho_banda_requerido:.2f}MB")
                
                return (True, puerto_libre, ancho_banda_disponible / self.capacidad_maxima)
            else:
                # RECHAZO
                razon = "Sin puertos libres" if puerto_libre is None else "Sin ancho de banda"
                self.registrar_evento(usuario_id, "WARN", "REJECT", "-",
                                    f"Rechazado: {razon}. Conexiones activas: {self.conexiones_activas}/{self.capacidad_maxima}")
                
                return (False, None, 0)
        
        finally:
            # ====== LIBERAR MUTEX EXPLÍCITAMENTE =======
            self.mutex.release()

    def registrar_salida(self, usuario_id, bytes_descargados):
        """
        Libera la conexión y registra el evento de salida (DISCONNECT).
        Usa mutex.acquire() de forma explícita.
        """
        self.registrar_evento(usuario_id, "MUTEX", "WAIT", "-", "Esperando Mutex para liberar puerto")
        
        # ====== ADQUIRIR MUTEX EXPLÍCITAMENTE =======
        self.mutex.acquire()
        try:
            # ====== DENTRO DE LA SECCIÓN CRÍTICA =======
            
            if usuario_id in self.asignaciones:
                asignacion = self.asignaciones[usuario_id]
                puerto_liberado = asignacion['puerto']
                ancho_banda_liberado = asignacion['ancho_banda']
                
                # Actualizar recursos
                self.puertos_disponibles[puerto_liberado] = "LIBRE"
                self.conexiones_activas -= 1
                self.ancho_banda_consumido -= ancho_banda_liberado
                self.bytes_transferidos_totales += bytes_descargados
                
                self.historial_trafico.append({
                    'usuario': usuario_id,
                    'puerto': puerto_liberado,
                    'bytes': bytes_descargados,
                    'tipo': asignacion['tipo_archivo'],
                    'timestamp': datetime.now()
                })
                
                # Registrar DISCONNECT
                self.registrar_evento(usuario_id, "INFO", "DISCONNECT", puerto_liberado,
                                    f"Descargó {bytes_descargados:.2f}MB. Nodo {puerto_liberado} liberado. Ancho restante: {self.ancho_banda_total - self.ancho_banda_consumido:.2f}MB")
                
                del self.asignaciones[usuario_id]
        
        finally:
            # ====== LIBERAR MUTEX EXPLÍCITAMENTE =======
            self.mutex.release()

    def generar_reporte_estado(self):
        print(f"\n{'='*70}")
        print(f"REPORTE: {self.nombre_servidor}")
        print(f"{'='*70}")
        print(f"Carga actual: {self.conexiones_activas} de {self.capacidad_maxima} usuarios")
        print(f"Ancho de banda consumido: {self.ancho_banda_consumido:.2f}MB de {self.ancho_banda_total:.2f}MB")
        print(f"Tráfico total: {self.bytes_transferidos_totales:.2f} MB")
        
        print(f"\n--- ESTADO DE PUERTOS/NODOS ---")
        for puerto, estado in self.puertos_disponibles.items():
            simbolo = "✓" if estado == "LIBRE" else "✗"
            print(f"  {simbolo} Nodo {puerto}: {estado}")
        
        print(f"\n--- HISTORIAL DE DESCARGAS ---")
        for descarga in self.historial_trafico:
            print(f"  • Usuario {descarga['usuario']}: {descarga['bytes']:.2f}MB ({descarga['tipo']}) en Nodo {descarga['puerto']}")
        
        print(f"\nDisponibilidad: {'ALTA' if self.conexiones_activas < self.capacidad_maxima else 'LLENO'}")
        print(f"✓ Bitácora guardada en: bitacora.log")
        print(f"{'='*70}\n")

