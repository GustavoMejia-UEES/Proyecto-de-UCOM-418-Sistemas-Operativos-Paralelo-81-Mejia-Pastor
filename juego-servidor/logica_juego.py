from servidor_juego import ServidorJuego
from bitacora_juego import bitacora_global


class LogicaJuego:
    """Capa de dominio del juego: valida y procesa acciones de gameplay."""

    def __init__(self, total_nodos=10, ancho_banda_total=500):
        self.servidor = ServidorJuego(total_nodos=total_nodos, ancho_banda_total=ancho_banda_total)

    @property
    def partida_activa(self):
        return self.servidor.partida_activa

    def _normalizar_nodo(self, valor_nodo):
        try:
            return int(valor_nodo)
        except (TypeError, ValueError):
            return None

    def _normalizar_mutex(self, valor_mutex):
        try:
            return int(valor_mutex)
        except (TypeError, ValueError):
            return None

    def procesar_accion(self, jugador, accion, datos):
        """
        Procesa una accion de gameplay y retorna (ok, motivo).
        Esta funcion es sync para ejecutarse con asyncio.to_thread desde WS.
        """
        if accion == "atacar_nodo":
            return self._procesar_ataque(jugador, datos)

        if accion == "reparar_nodo":
            return self._procesar_reparacion(jugador, datos)

        if accion == "recoger_item":
            return self._procesar_recoger_item(jugador, datos)

        if accion == "liberar_mutex":
            return self._procesar_liberar_mutex(jugador, datos)

        if accion == "cancelar_interaccion":
            return self.cancelar_interaccion(jugador)

        return False, "accion_no_manejada"

    def _procesar_ataque(self, jugador, datos):
        if jugador.rol != "CLIENTE":
            return False, "rol_no_permitido"

        if self.servidor.fase != "JUGANDO" or not self.servidor.partida_activa:
            return False, "partida_no_iniciada"

        nodo_raw = datos.get("nodo")
        nodo = self._normalizar_nodo(nodo_raw)
        if nodo is None or nodo not in self.servidor.nodos:
            bitacora_global.registrar("WARN", "NODO_INVALIDO", f"atacar_nodo rechazado. valor recibido={nodo_raw}")
            return False, "nodo_invalido"

        if not jugador.gastar_energia(10):
            return False, "sin_energia"

        ok, motivo = self.servidor.procesar_ataque_cliente(jugador, nodo)
        if not ok and motivo in {"tipo_ataque_incompatible", "nodo_bloqueado", "sin_cupo_nodos"}:
            jugador.devolver_energia(10)

        return ok, motivo

    def _procesar_reparacion(self, jugador, datos):
        if jugador.rol != "ADMIN":
            return False, "rol_no_permitido"

        if self.servidor.fase != "JUGANDO" or not self.servidor.partida_activa:
            return False, "partida_no_iniciada"

        nodo_raw = datos.get("nodo")
        nodo = self._normalizar_nodo(nodo_raw)
        if nodo is None or nodo not in self.servidor.nodos:
            bitacora_global.registrar("WARN", "NODO_INVALIDO", f"reparar_nodo rechazado. valor recibido={nodo_raw}")
            return False, "nodo_invalido"

        return self.servidor.procesar_reparacion_admin(jugador, nodo)

    def _procesar_recoger_item(self, jugador, datos):
        id_item = datos.get("id_item")
        if not id_item:
            return False, "id_item_invalido"

        if jugador.rol == "CLIENTE":
            return self.servidor.procesar_recoger_item_hacker(jugador, id_item)

        if jugador.rol == "ADMIN":
            return self.servidor.procesar_recoger_item_admin(jugador, id_item)

        return False, "rol_no_permitido"

    def _procesar_liberar_mutex(self, jugador, datos):
        if jugador.rol != "ADMIN":
            return False, "rol_no_permitido"

        mutex_raw = datos.get("mutex_id")
        mutex_id = self._normalizar_mutex(mutex_raw)
        if mutex_id is None:
            bitacora_global.registrar("WARN", "MUTEX_INVALIDO", f"liberar_mutex rechazado. valor recibido={mutex_raw}")
            return False, "mutex_id_invalido"

        return self.servidor.procesar_liberar_mutex(jugador, mutex_id)

    def iniciar_partida(self):
        return self.servidor.iniciar_partida()

    def cancelar_interaccion(self, jugador):
        return self.servidor.cancelar_interaccion(jugador)

    def tick_cinta_hacker(self):
        return self.servidor.agregar_item_aleatorio_hacker()

    def tick_cinta_admin(self):
        return self.servidor.agregar_item_aleatorio_admin()

    def tick_drenaje_pasivo(self, segundos_tick=2):
        self.servidor.aplicar_drenaje_pasivo(segundos_tick)
        return True

    def obtener_estado_snapshot(self):
        return self.servidor.obtener_snapshot_estado()
