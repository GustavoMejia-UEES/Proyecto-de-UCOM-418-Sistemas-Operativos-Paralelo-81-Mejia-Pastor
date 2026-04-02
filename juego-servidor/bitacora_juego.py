import logging
import threading
from collections import deque
from datetime import datetime

class BitacoraJuego:
    def __init__(self):
        # 1. Configuración del Log Físico (Thread-safe por naturaleza en Python)
        self.logger = logging.getLogger('JuegoSO')
        self.logger.setLevel(logging.INFO)
        
        if self.logger.handlers:
            self.logger.handlers.clear()
            
        file_handler = logging.FileHandler('bitacora_juego.log', mode='w', encoding='utf-8')
        formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 2. Configuración de la Memoria en Vivo (Para Godot)
        # Una cola que empuja y borra automáticamente los mensajes viejos (máximo 15)
        self.cola_mensajes = deque(maxlen=15)
        
        # MUTEX para proteger la cola en memoria RAM
        self.mutex_cola = threading.Lock()

    def registrar(self, nivel, tipo_evento, mensaje):
        """Guarda en archivo y mete en la cola de RAM de forma segura"""
        hora_actual = datetime.now().strftime('%H:%M:%S')
        texto_log = f"[{nivel}] [{tipo_evento}] {mensaje}"
        
        # Escribir en archivo (Disco)
        self.logger.info(texto_log)
        
        # Escribir en memoria RAM (Sección Crítica)
        self.mutex_cola.acquire()
        try:
            self.cola_mensajes.append(f"{hora_actual} {texto_log}")
        finally:
            self.mutex_cola.release()

    def obtener_logs_para_godot(self):
        """Extrae una copia segura de los logs para enviarla por WebSocket"""
        self.mutex_cola.acquire()
        try:
            # Retornamos una lista nativa (JSON no entiende 'deque')
            return list(self.cola_mensajes)
        finally:
            self.mutex_cola.release()

# Instancia global para que todos los hilos escriban en el mismo lugar
bitacora_global = BitacoraJuego()