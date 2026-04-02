import threading
import time
from bitacora_juego import bitacora_global

class Jugador:
    def __init__(self, id_ws, nombre, rol):
        self.id_ws = id_ws  
        self.nombre = nombre
        self.rol = rol  # "CLIENTE" o "ADMIN"
        self.avatar = "char_01"
        
        # Posición para que Godot los dibuje
        self.pos_x = 0
        self.pos_y = 0
        
        # Arsenal hacker
        self.tipos_archivos = ["TEXTO", "AUDIO", "VIDEO"]
        self.indice_archivo = 0
        
        # FIX: Empiezan con las manos vacías obligatoriamente
        self.archivo_seleccionado = ""
        self.herramienta_seleccionada = ""

        # Throttle de recarga (segundos entre ticks aceptados)
        self.ultimo_tick_recarga = 0.0
        
        # ==========================================
        # RECURSO COMPARTIDO Y SU MUTEX (ANTI-CHEAT)
        # ==========================================
        self.energia_maxima = 100 if rol == "CLIENTE" else 0 
        self.energia_actual = self.energia_maxima
        
        # Este candado evita que si llegan 5 paquetes de red al mismo tiempo,
        # la energía baje de 0.
        self.mutex_energia = threading.Lock()

    def actualizar_rol(self, nuevo_rol):
        """Permite reasignar rol de forma segura (ej. inicio aleatorio de partida)."""
        self.rol = nuevo_rol
        self.energia_maxima = 100 if nuevo_rol == "CLIENTE" else 0
        self.energia_actual = self.energia_maxima
        self.herramienta_seleccionada = ""

    def mover(self, x, y):
        """Actualiza coordenadas (no requiere mutex porque las sobrescribe)"""
        self.pos_x = x
        self.pos_y = y

    def gastar_energia(self, cantidad):
        """SECCIÓN CRÍTICA: Restar energía de forma segura"""
        self.mutex_energia.acquire()
        try:
            if self.energia_actual >= cantidad:
                self.energia_actual -= cantidad
                return True
            return False
        finally:
            self.mutex_energia.release()

    def devolver_energia(self, cantidad):
        """SECCIÓN CRÍTICA: Reembolso seguro de energía cuando una acción se rechaza."""
        self.mutex_energia.acquire()
        try:
            self.energia_actual = min(self.energia_maxima, self.energia_actual + cantidad)
            return True
        finally:
            self.mutex_energia.release()

    def recargar_energia(self):
        """SECCIÓN CRÍTICA: Recarga incremental (+10) con throttle de 0.5s."""
        if self.rol != "CLIENTE":
            return False

        ahora = time.time()
        if (ahora - self.ultimo_tick_recarga) < 0.5:
            return False

        self.mutex_energia.acquire()
        try:
            self.ultimo_tick_recarga = ahora
            energia_antes = self.energia_actual
            self.energia_actual = min(self.energia_maxima, self.energia_actual + 10)
            if self.energia_actual != energia_antes:
                bitacora_global.registrar("INFO", "RECARGA", f"{self.nombre} recargó energía: {energia_antes} -> {self.energia_actual}.")
            return self.energia_actual != energia_antes
        finally:
            self.mutex_energia.release()

    def cambiar_archivo(self):
        """Cambia el tipo de ataque que hará el jugador"""
        if self.rol == "CLIENTE":
            self.indice_archivo = (self.indice_archivo + 1) % len(self.tipos_archivos)
            self.archivo_seleccionado = self.tipos_archivos[self.indice_archivo]
            bitacora_global.registrar("INFO", "LOADOUT", f"{self.nombre} ahora tiene equipado: {self.archivo_seleccionado}")

    def to_dict(self):
        """Empaqueta al jugador para mandarlo por JSON a Godot"""
        return {
            "nombre":             self.nombre,
            "rol":                self.rol,
            "avatar":             self.avatar,
            "x":                  self.pos_x,
            "y":                  self.pos_y,
            "energia":            self.energia_actual,
            "archivo_equipado":   self.archivo_seleccionado,
            "herramienta_equipada": self.herramienta_seleccionada,
        }