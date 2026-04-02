import random
import threading
import time
from copy import deepcopy

from bitacora_juego import bitacora_global


class ServidorJuego:
    def __init__(self, total_nodos=20, ancho_banda_total=500):
        self.vida_servidor = 100
        self.ancho_banda_total = ancho_banda_total
        self.ancho_banda_consumido = 0.0
        self.total_nodos = total_nodos
        self.duracion_partida = 180  # 3 minutos freneticos
        self.tiempo_inicio = None
        self.fase = "LOBBY"
        self.partida_activa = False
        self.resultado_partida = None

        self.nodos = {
            i: {
                "estado": "LIBRE",
                "hp": 100,
                "progreso": 0,
                "total": 0,
                "tipo_ataque": "",
                "ocupado_por": None,
                "reparacion_progreso": 0,
                "reparacion_total": 0,
            }
            for i in range(1, total_nodos + 1)
        }

        self.semaforos_nodo = {i: threading.Semaphore(1) for i in range(1, total_nodos + 1)}
        self.semaforo_nodos_activos = threading.Semaphore(total_nodos)
        self.nodos_con_cupo_activo = set()

        self.asignaciones = {}

        self.cinta_hacker = []
        self.max_items_cinta_hacker = 6
        self._contador_items_hacker = 0
        self.semaforo_cinta_hacker_slots = threading.Semaphore(self.max_items_cinta_hacker)

        self.cinta_admin = [
            {"id": "admin_txt", "tipo": "PARCHE_TEXTO", "x": -200, "y": 0},
            {"id": "admin_aud", "tipo": "PARCHE_AUDIO", "x": 0, "y": 0},
            {"id": "admin_vid", "tipo": "PARCHE_VIDEO", "x": 200, "y": 0},
        ]
        self.max_items_cinta_admin = 6
        self._contador_items_admin = 0
        self.semaforo_cinta_admin_slots = threading.Semaphore(self.max_items_cinta_admin)

        self.mutex_calientes = []
        self._presion_mutex_activa = False

        self.nodos_corruptos = 0
        self.drenaje_tick = 0.0

        self.mutex = threading.Lock()

    def iniciar_partida(self):
        self.mutex.acquire()
        try:
            if self.fase != "LOBBY":
                return False, "partida_ya_iniciada"

            self.fase = "JUGANDO"
            self.partida_activa = True
            self.resultado_partida = None
            self.tiempo_inicio = time.time()
            bitacora_global.registrar("INFO", "INICIO", "Partida iniciada por el anfitrion.")
            return True, "partida_iniciada"
        finally:
            self.mutex.release()

    def procesar_ataque_cliente(self, jugador, id_nodo):
        if not getattr(jugador, "archivo_seleccionado", ""):
            return False, "sin_archivo_equipado"

        pesos_archivos = {"TEXTO": 10, "AUDIO": 30, "VIDEO": 80}
        presses_archivos = {"TEXTO": 5, "AUDIO": 10, "VIDEO": 15}
        peso_ataque = pesos_archivos.get(jugador.archivo_seleccionado, 10)
        presses_total = presses_archivos.get(jugador.archivo_seleccionado, 5)

        sem_nodo = self.semaforos_nodo.get(id_nodo)
        if not sem_nodo:
            return False, "nodo_invalido"

        if not sem_nodo.acquire(timeout=0.25):
            return False, "nodo_bloqueado"

        self.mutex.acquire()
        try:
            if self.fase != "JUGANDO" or not self.partida_activa:
                return False, "partida_no_iniciada"

            if id_nodo not in self.nodos:
                return False, "nodo_invalido"

            nodo = self.nodos[id_nodo]
            ocupado_por = nodo.get("ocupado_por")
            if ocupado_por and ocupado_por != jugador.nombre:
                return False, "nodo_ocupado"

            estado_actual = nodo["estado"]

            if estado_actual == "CORRUPTO":
                self.vida_servidor = max(0, self.vida_servidor - 5)
                self._actualizar_estado_partida_locked()
                return False, "nodo_ya_corrupto"

            if estado_actual == "ATACADO":
                info_archivo = self.asignaciones.get(id_nodo)
                if not info_archivo:
                    nodo["estado"] = "LIBRE"
                    nodo["progreso"] = 0
                    nodo["total"] = 0
                    nodo["tipo_ataque"] = ""
                    nodo["ocupado_por"] = None
                    nodo["reparacion_progreso"] = 0
                    nodo["reparacion_total"] = 0
                else:
                    if info_archivo["tipo"] != jugador.archivo_seleccionado:
                        return False, "tipo_ataque_incompatible"

                    nodo["ocupado_por"] = jugador.nombre
                    nodo["tipo_ataque"] = info_archivo["tipo"]
                    nodo["progreso"] += 1

                    # Danio por tap-tap: cada teclazo exitoso erosiona vida global.
                    self.vida_servidor = max(0, self.vida_servidor - 0.5)

                    if nodo["progreso"] >= nodo["total"]:
                        nodo["estado"] = "CORRUPTO"
                        nodo["progreso"] = nodo["total"]
                        # Golpe mortal al completar corrupcion de la PC.
                        self.vida_servidor = max(0, self.vida_servidor - 5)
                        bitacora_global.registrar("INFO", "CORRUPCION", f"{jugador.nombre} corrompio el Nodo {id_nodo}.")
                    else:
                        bitacora_global.registrar("INFO", "PROGRESO", f"{jugador.nombre} avanzo Nodo {id_nodo}: {nodo['progreso']}/{nodo['total']}.")

                    self._actualizar_estado_partida_locked()
                    jugador.archivo_seleccionado = ""
                    self._actualizar_mutex_calientes_locked()
                    return True, "progreso"

            if (self.ancho_banda_total - self.ancho_banda_consumido) < peso_ataque:
                self.vida_servidor = max(0, self.vida_servidor - 10)
                self._actualizar_estado_partida_locked()
                return False, "red_saturada"

            if id_nodo not in self.nodos_con_cupo_activo:
                if not self.semaforo_nodos_activos.acquire(blocking=False):
                    return False, "sin_cupo_nodos"
                self.nodos_con_cupo_activo.add(id_nodo)

            nodo["estado"] = "ATACADO"
            nodo["hp"] = 100
            nodo["progreso"] = 1
            nodo["total"] = presses_total
            nodo["tipo_ataque"] = jugador.archivo_seleccionado
            nodo["ocupado_por"] = jugador.nombre
            nodo["reparacion_progreso"] = 0
            nodo["reparacion_total"] = 0

            self.asignaciones[id_nodo] = {
                "atacante": jugador.nombre,
                "tipo": jugador.archivo_seleccionado,
                "peso": peso_ataque,
            }

            bitacora_global.registrar("INFO", "ATAQUE", f"{jugador.nombre} inicio ataque Nodo {id_nodo} (1/{presses_total}).")
            # Danio por tap-tap del primer teclazo (inicio de ataque).
            self.vida_servidor = max(0, self.vida_servidor - 0.5)
            self._actualizar_estado_partida_locked()
            jugador.archivo_seleccionado = ""
            self._actualizar_mutex_calientes_locked()
            return True, "ataque_iniciado"
        finally:
            self.mutex.release()
            sem_nodo.release()

    def procesar_reparacion_admin(self, admin, id_nodo):
        if not getattr(admin, "herramienta_seleccionada", ""):
            return False, "sin_herramienta_equipada"

        sem_nodo = self.semaforos_nodo.get(id_nodo)
        if not sem_nodo:
            return False, "nodo_invalido"

        if not sem_nodo.acquire(timeout=0.25):
            return False, "nodo_bloqueado"

        self.mutex.acquire()
        try:
            if self.fase != "JUGANDO" or not self.partida_activa:
                return False, "partida_no_iniciada"

            if id_nodo not in self.nodos:
                return False, "nodo_invalido"

            nodo = self.nodos[id_nodo]

            # 1. ¿Está dañado y es reparable?
            if nodo["estado"] == "CORRUPTO":
                # Regla: lo corrupto es irrecuperable.
                return False, "nodo_irrecuperable"

            if nodo["estado"] == "LIBRE":
                return False, "sin_cambios"

            # 2. ¿Tiene el parche correcto?
            tipo_ataque = nodo.get("tipo_ataque", "")
            parche_necesario = "PARCHE_" + tipo_ataque
            
            if admin.herramienta_seleccionada != parche_necesario:
                print(f"[RECHAZO] {admin.nombre} tiene {admin.herramienta_seleccionada} pero necesita {parche_necesario}")
                return False, "herramienta_incorrecta"

            info_archivo = self.asignaciones.get(id_nodo)
            if not info_archivo:
                return False, "sin_asignacion"

            # ==========================================
            # 🔨 REPARACIÓN TIPO HACKER (1 Golpe = 1 Parche Consumido)
            # ==========================================
            # Le restamos 1 punto de daño
            nodo["progreso"] -= 1
            
            # ¡TE QUITAMOS EL PARCHE INMEDIATAMENTE! Tienes que ir por más.
            admin.herramienta_seleccionada = ""

            # Si el daño aún es mayor a 0, la PC sigue infectada pero con menos daño
            if nodo["progreso"] > 0:
                print(f"[REPARANDO] {admin.nombre} reparando Nodo {id_nodo} ({nodo['progreso']}/{nodo['total']})")
                return True, "reparacion_progreso"

            # --- SI LLEGA A 0, EL SERVIDOR SE SALVÓ POR COMPLETO ---
            self.asignaciones.pop(id_nodo, None)
            recuperacion = info_archivo["peso"]
            self.ancho_banda_consumido = max(0.0, self.ancho_banda_consumido - recuperacion)

            nodo["estado"] = "LIBRE"
            nodo["hp"] = 100
            nodo["progreso"] = 0
            nodo["total"] = 0
            nodo["tipo_ataque"] = ""
            nodo["ocupado_por"] = None
            nodo["reparacion_progreso"] = 0
            nodo["reparacion_total"] = 0

            if id_nodo in self.nodos_con_cupo_activo:
                self.nodos_con_cupo_activo.remove(id_nodo)
                self.semaforo_nodos_activos.release()

            bitacora_global.registrar("INFO", "LIMPIEZA", f"Admin {admin.nombre} curo por completo el Nodo {id_nodo}.")
            self._actualizar_mutex_calientes_locked()
            return True, "nodo_limpio"
        finally:
            self.mutex.release()
            sem_nodo.release()

    def cancelar_interaccion(self, jugador):
        self.mutex.acquire()
        try:
            for id_nodo, nodo in self.nodos.items():
                if nodo.get("ocupado_por") == jugador.nombre:
                    nodo["ocupado_por"] = None
                    if nodo.get("estado") == "LIBRE":
                        nodo["tipo_ataque"] = ""
                    bitacora_global.registrar("INFO", "CANCELAR", f"{jugador.nombre} libero Nodo {id_nodo}.")
                    return True, "interaccion_cancelada"
            return False, "sin_interaccion_activa"
        finally:
            self.mutex.release()

    def obtener_tiempo_restante(self):
        if self.fase == "LOBBY" or self.tiempo_inicio is None:
            return self.duracion_partida
        return max(0, int(self.duracion_partida - (time.time() - self.tiempo_inicio)))

    def _actualizar_estado_partida_locked(self):
        if self.fase != "JUGANDO" or not self.partida_activa:
            return

        if self.vida_servidor <= 0:
            self.vida_servidor = 0
            self.partida_activa = False
            self.fase = "FINALIZADA"
            self.resultado_partida = "HACKERS"
            bitacora_global.registrar("INFO", "FIN", "Partida finalizada: HACKERS GANAN.")
            return

        if self.obtener_tiempo_restante() <= 0:
            self.partida_activa = False
            self.fase = "FINALIZADA"
            self.resultado_partida = "ADMINS"
            bitacora_global.registrar("INFO", "FIN", "Partida finalizada: ADMINS GANAN.")

    def _actualizar_mutex_calientes_locked(self):
        corruptos = 0
        for nodo in self.nodos.values():
            if nodo.get("estado") == "CORRUPTO":
                corruptos += 1

        if corruptos >= 1 and not self._presion_mutex_activa:
            self.mutex_calientes = [int(x) for x in [0, 1, 2]]
            self._presion_mutex_activa = True
            bitacora_global.registrar("WARN", "MUTEX_CALIENTE", "Mutex en estado CALIENTE por 1+ nodos CORRUPTOS.")
        elif corruptos < 1 and self._presion_mutex_activa:
            self.mutex_calientes = []
            self._presion_mutex_activa = False
            bitacora_global.registrar("INFO", "MUTEX_FRIO", "Mutex volvio a estado normal.")

    def obtener_snapshot_estado(self):
        self.mutex.acquire()
        try:
            self._actualizar_estado_partida_locked()
            return {
                "vida_servidor": self.vida_servidor,
                "banda_consumida": self.ancho_banda_consumido,
                "tiempo_restante": self.obtener_tiempo_restante(),
                "partida_activa": self.partida_activa,
                "resultado_partida": self.resultado_partida,
                "fase": self.fase,
                "nodos": deepcopy(self.nodos),
                "cinta_hacker": deepcopy(self.cinta_hacker),
                "cinta_admin": deepcopy(self.cinta_admin),
                "mutex_calientes": deepcopy(self.mutex_calientes),
                "nodos_corruptos": self.nodos_corruptos,
                "drenaje_tick": self.drenaje_tick,
            }
        finally:
            self.mutex.release()

    def aplicar_drenaje_pasivo(self, segundos_tick=1):
        self.mutex.acquire()
        try:
            if self.fase != "JUGANDO" or not self.partida_activa:
                return

            corruptos = 0
            for _, nodo in self.nodos.items():
                if nodo.get("estado") == "CORRUPTO":
                    corruptos += 1

            self.nodos_corruptos = corruptos
            self.drenaje_tick = float(corruptos)

            if corruptos > 0:
                danio = float(corruptos) * 1.0
                self.vida_servidor = max(0, self.vida_servidor - danio)

            self._actualizar_estado_partida_locked()
            self._actualizar_mutex_calientes_locked()
        finally:
            self.mutex.release()

    def procesar_liberar_mutex(self, admin, mutex_id):
        self.mutex.acquire()
        try:
            if admin.rol != "ADMIN":
                return False, "rol_no_permitido"

            try:
                mutex_id = int(mutex_id)
            except (TypeError, ValueError):
                return False, "mutex_id_invalido"

            if mutex_id not in [0, 1, 2]:
                return False, "mutex_id_invalido"

            # Normaliza cualquier valor previo para asegurar que siempre sean enteros.
            self.mutex_calientes = [int(x) for x in self.mutex_calientes]

            if mutex_id in self.mutex_calientes:
                self.mutex_calientes.remove(mutex_id)

                # Habilidad definitiva: limpiar exactamente 1 nodo corrupto y su asignacion activa.
                for id_nodo, nodo in self.nodos.items():
                    if nodo.get("estado") == "CORRUPTO":
                        nodo["estado"] = "LIBRE"
                        nodo["hp"] = 100
                        nodo["progreso"] = 0
                        nodo["total"] = 0
                        nodo["tipo_ataque"] = ""
                        nodo["ocupado_por"] = None
                        nodo["reparacion_progreso"] = 0
                        nodo["reparacion_total"] = 0
                        self.asignaciones.pop(id_nodo, None)
                        bitacora_global.registrar("INFO", "MUTEX_PURGA", f"Admin {admin.nombre} purgo Nodo {id_nodo} con mutex {mutex_id}.")
                        break

                self._actualizar_estado_partida_locked()
                self._actualizar_mutex_calientes_locked()
                bitacora_global.registrar("INFO", "LIBERAR_MUTEX", f"Admin {admin.nombre} libero mutex {mutex_id}.")
                return True, "exito"
            return False, "mutex_no_caliente"
        finally:
            self.mutex.release()

    def agregar_item_aleatorio_hacker(self):
        if not self.semaforo_cinta_hacker_slots.acquire(blocking=False):
            return False

        conservar_slot = True
        self.mutex.acquire()
        try:
            if len(self.cinta_hacker) >= self.max_items_cinta_hacker:
                return False

            self._contador_items_hacker += 1
            nuevo_item = {
                "id": f"f{self._contador_items_hacker:04d}",
                "tipo": random.choice(["TEXTO", "AUDIO", "VIDEO"]),
                "x": random.randint(-460, 460),
                "y": 0,
            }
            self.cinta_hacker.append(nuevo_item)
            conservar_slot = False
            return True
        finally:
            self.mutex.release()
            if conservar_slot:
                self.semaforo_cinta_hacker_slots.release()

    def procesar_recoger_item_hacker(self, jugador, id_item):
        self.mutex.acquire()
        try:
            if jugador.rol != "CLIENTE":
                return False, "rol_no_permitido"

            for i, item in enumerate(self.cinta_hacker):
                if item.get("id") == id_item:
                    item_recogido = self.cinta_hacker.pop(i)
                    jugador.archivo_seleccionado = item_recogido.get("tipo", "TEXTO")
                    self.semaforo_cinta_hacker_slots.release()
                    return True, "exito"

            return False, "item_no_encontrado"
        finally:
            self.mutex.release()

    def agregar_item_aleatorio_admin(self):
        # Admin usa cajas fijas e infinitas; no hay spawn aleatorio ni crecimiento.
        return True

    def procesar_recoger_item_admin(self, jugador, id_item):
        self.mutex.acquire()
        try:
            if jugador.rol != "ADMIN":
                return False, "rol_no_permitido"

            for item in self.cinta_admin:
                if item.get("id") == id_item:
                    jugador.herramienta_seleccionada = item.get("tipo", "PARCHE_TEXTO")
                    return True, "exito"

            return False, "item_no_encontrado"
        finally:
            self.mutex.release()
