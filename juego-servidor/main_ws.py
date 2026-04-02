import asyncio
import json
import os
import random
import string
import threading

import websockets

from bitacora_juego import bitacora_global
from logica_juego import LogicaJuego
from usuario_juego import Jugador

# ==========================================
# ESTADO GLOBAL DE LA RED (MULTI-SALA)
# ==========================================
# codigo -> {"codigo", "logica", "jugadores", "conexiones", "host_id"}
salas_activas = {}
# id_ws -> codigo_sala
jugador_a_sala = {}
# websocket -> id_ws
ws_a_id = {}
# Set global para rastrear conexiones abiertas
conexiones_activas = set()

mutex_red = threading.Lock()
PORT = int(os.environ.get("PORT", 8000))


def _generar_codigo_sala():
    alfabeto = string.ascii_uppercase + string.digits
    for _ in range(1000):
        codigo = "".join(random.choice(alfabeto) for _ in range(4))
        if codigo not in salas_activas:
            return codigo
    raise RuntimeError("No se pudo generar codigo de sala unico")


def _serializar_jugadores_sala(sala):
    jugadores = {}
    for ws_id, jugador in sala["jugadores"].items():
        data = jugador.to_dict()
        data["es_host"] = (ws_id == sala["host_id"])
        jugadores[ws_id] = data
    return jugadores


async def _enviar_json(websocket, payload):
    try:
        await websocket.send(json.dumps(payload))
    except websockets.exceptions.ConnectionClosed:
        pass


def _asignar_roles_aleatorios_sala(sala):
    jugadores_ids = list(sala["jugadores"].keys())
    total = len(jugadores_ids)

    if total < 2:
        return False, "minimo_2_jugadores"

    max_admins = 1 if total <= 4 else 2
    max_admins = min(max_admins, total - 1)
    admins_asignados = random.randint(1, max_admins)
    admin_ids = set(random.sample(jugadores_ids, admins_asignados))

    for ws_id, jugador in sala["jugadores"].items():
        if ws_id in admin_ids:
            jugador.actualizar_rol("ADMIN")
            jugador.pos_x = random.randint(120, 900)
            jugador.pos_y = random.randint(120, 900)
        else:
            jugador.actualizar_rol("CLIENTE")
            jugador.pos_x = random.randint(120, 900)
            jugador.pos_y = random.randint(1200, 1900)

    bitacora_global.registrar(
        "INFO",
        "ROLES",
        f"Sala {sala['codigo']}: {admins_asignados} ADMIN(s), {total - admins_asignados} HACKER(s).",
    )
    return True, "roles_asignados"


async def _crear_sala(websocket, id_ws, datos):
    nombre = str(datos.get("nombre", f"Player_{id_ws[:4]}"))
    rol = str(datos.get("rol", "CLIENTE"))
    avatar = str(datos.get("avatar", "char_01"))

    mutex_red.acquire()
    try:
        if id_ws in jugador_a_sala:
            return False, "ya_en_sala", None

        codigo = _generar_codigo_sala()
        jugador = Jugador(id_ws, nombre, rol)
        jugador.avatar = avatar

        sala = {
            "codigo": codigo,
            "logica": LogicaJuego(total_nodos=10, ancho_banda_total=500),
            "jugadores": {id_ws: jugador},
            "conexiones": {websocket},
            "host_id": id_ws,
        }
        salas_activas[codigo] = sala
        jugador_a_sala[id_ws] = codigo
        return True, "ok", codigo
    finally:
        mutex_red.release()


async def _unirse_sala(websocket, id_ws, datos):
    nombre = str(datos.get("nombre", f"Player_{id_ws[:4]}"))
    rol = str(datos.get("rol", "CLIENTE"))
    avatar = str(datos.get("avatar", "char_01"))
    codigo = str(datos.get("codigo_sala", "")).strip().upper()

    if not codigo:
        return False, "codigo_invalido", None

    mutex_red.acquire()
    try:
        if id_ws in jugador_a_sala:
            return False, "ya_en_sala", None

        sala = salas_activas.get(codigo)
        if not sala:
            return False, "sala_no_encontrada", None

        jugador = Jugador(id_ws, nombre, rol)
        jugador.avatar = avatar

        sala["jugadores"][id_ws] = jugador
        sala["conexiones"].add(websocket)
        jugador_a_sala[id_ws] = codigo
        return True, "ok", codigo
    finally:
        mutex_red.release()


async def procesar_mensaje(websocket, id_ws, mensaje_str):
    """Traduce el JSON de Godot a acciones del motor (multi-sala)."""
    try:
        datos = json.loads(mensaje_str)
    except json.JSONDecodeError:
        await _enviar_json(websocket, {"tipo": "error", "motivo": "json_invalido"})
        return

    accion = datos.get("accion")
    if not accion:
        await _enviar_json(websocket, {"tipo": "error", "motivo": "accion_invalida"})
        return

    if accion == "crear_sala":
        ok, motivo, codigo = await _crear_sala(websocket, id_ws, datos)
        if ok:
            bitacora_global.registrar("INFO", "SALA", f"{datos.get('nombre')} creo la sala {codigo}.")
            await _enviar_json(websocket, {
                "tipo": "sala_creada",
                "ok": True,
                "codigo_sala": codigo,
                "es_host": True,
            })
        else:
            await _enviar_json(websocket, {"tipo": "sala_creada", "ok": False, "motivo": motivo})
        return

    if accion == "unirse_sala":
        ok, motivo, codigo = await _unirse_sala(websocket, id_ws, datos)
        if ok:
            bitacora_global.registrar("INFO", "SALA", f"{datos.get('nombre')} se unio a la sala {codigo}.")
            await _enviar_json(websocket, {
                "tipo": "sala_unida",
                "ok": True,
                "codigo_sala": codigo,
                "es_host": False,
            })
        else:
            await _enviar_json(websocket, {"tipo": "sala_unida", "ok": False, "motivo": motivo})
        return

    mutex_red.acquire()
    try:
        codigo = jugador_a_sala.get(id_ws)
        sala = salas_activas.get(codigo) if codigo else None
        jugador = sala["jugadores"].get(id_ws) if sala else None
    finally:
        mutex_red.release()

    if not sala or not jugador:
        await _enviar_json(websocket, {"tipo": "error", "motivo": "jugador_sin_sala"})
        return

    if accion == "iniciar_partida":
        es_host = (id_ws == sala["host_id"])
        if not es_host:
            await _enviar_json(websocket, {
                "tipo": "accion_resultado",
                "accion": accion,
                "ok": False,
                "motivo": "solo_host",
            })
            return

        ok_roles, motivo_roles = _asignar_roles_aleatorios_sala(sala)
        if not ok_roles:
            await _enviar_json(websocket, {
                "tipo": "accion_resultado",
                "accion": accion,
                "ok": False,
                "motivo": motivo_roles,
            })
            return

        ok, motivo = await asyncio.to_thread(sala["logica"].iniciar_partida)
        await _enviar_json(websocket, {
            "tipo": "accion_resultado",
            "accion": accion,
            "ok": ok,
            "motivo": motivo,
        })
        return

    if accion == "moverse":
        jugador.mover(datos.get("x"), datos.get("y"))
        return

    if accion == "cambiar_arma":
        jugador.cambiar_archivo()
        return

    if accion == "recargar":
        jugador.recargar_energia()
        return

    if accion in ["atacar_nodo", "reparar_nodo", "recoger_item", "liberar_mutex", "cancelar_interaccion"]:
        ok, motivo = await asyncio.to_thread(sala["logica"].procesar_accion, jugador, accion, datos)
        await _enviar_json(websocket, {
            "tipo": "accion_resultado",
            "accion": accion,
            "ok": ok,
            "motivo": motivo,
        })
        return

    await _enviar_json(websocket, {
        "tipo": "accion_resultado",
        "accion": accion,
        "ok": False,
        "motivo": "accion_no_manejada",
    })


async def ciclo_cinta_hacker():
    while True:
        mutex_red.acquire()
        try:
            logicas = [s["logica"] for s in salas_activas.values()]
        finally:
            mutex_red.release()

        for logica in logicas:
            await asyncio.to_thread(logica.tick_cinta_hacker)

        await asyncio.sleep(1.5)


async def ciclo_cinta_admin():
    while True:
        mutex_red.acquire()
        try:
            logicas = [s["logica"] for s in salas_activas.values()]
        finally:
            mutex_red.release()

        for logica in logicas:
            await asyncio.to_thread(logica.tick_cinta_admin)

        await asyncio.sleep(7)


async def ciclo_drenaje_pasivo():
    while True:
        mutex_red.acquire()
        try:
            logicas = [s["logica"] for s in salas_activas.values()]
        finally:
            mutex_red.release()

        for logica in logicas:
            await asyncio.to_thread(logica.tick_drenaje_pasivo, 1)

        await asyncio.sleep(1)


async def enviar_estado_mundo():
    while True:
        mutex_red.acquire()
        try:
            salas_snapshot = []
            for codigo, sala in salas_activas.items():
                conexiones = list(sala["conexiones"])
                jugadores = _serializar_jugadores_sala(sala)
                logica = sala["logica"]
                host_id = sala["host_id"]
                salas_snapshot.append((codigo, conexiones, jugadores, logica, host_id))
        finally:
            mutex_red.release()

        for codigo, conexiones, jugadores, logica, host_id in salas_snapshot:
            if not conexiones:
                continue

            estado_servidor = await asyncio.to_thread(logica.obtener_estado_snapshot)
            estado = {
                "vida_servidor": estado_servidor["vida_servidor"],
                "banda_consumida": estado_servidor["banda_consumida"],
                "tiempo_restante": estado_servidor["tiempo_restante"],
                "partida_activa": estado_servidor["partida_activa"],
                "resultado_partida": estado_servidor["resultado_partida"],
                "nodos": estado_servidor["nodos"],
                "cinta_hacker": estado_servidor["cinta_hacker"],
                "cinta_admin": estado_servidor["cinta_admin"],
                "mutex_calientes": estado_servidor["mutex_calientes"],
                "nodos_corruptos": estado_servidor["nodos_corruptos"],
                "drenaje_tick": estado_servidor["drenaje_tick"],
                "fase": estado_servidor["fase"],
                "codigo_sala": codigo,
                "host_id": host_id,
                "jugadores": jugadores,
                "consola_en_vivo": bitacora_global.obtener_logs_para_godot(),
            }

            mensaje = json.dumps({"tipo": "estado_mundo", "payload": estado})
            websockets.broadcast(conexiones, mensaje)

        await asyncio.sleep(0.05)


async def manejador_cliente(websocket):
    id_ws = str(websocket.id)

    mutex_red.acquire()
    try:
        conexiones_activas.add(websocket)
        ws_a_id[websocket] = id_ws
    finally:
        mutex_red.release()

    print(f"[+] Nueva conexion entrante: {id_ws}")

    try:
        async for mensaje in websocket:
            await procesar_mensaje(websocket, id_ws, mensaje)

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        mutex_red.acquire()
        try:
            if websocket in conexiones_activas:
                conexiones_activas.remove(websocket)
            ws_a_id.pop(websocket, None)

            codigo = jugador_a_sala.pop(id_ws, None)
            sala = salas_activas.get(codigo) if codigo else None

            if sala:
                jugador = sala["jugadores"].pop(id_ws, None)
                sala["conexiones"].discard(websocket)

                if jugador:
                    try:
                        sala["logica"].cancelar_interaccion(jugador)
                    except Exception:
                        pass
                    bitacora_global.registrar("INFO", "DESCONEXION", f"{jugador.nombre} salio de la sala {codigo}.")
                    print(f"[-] {jugador.nombre} se desconecto de sala {codigo}.")

                if sala["host_id"] == id_ws:
                    if sala["jugadores"]:
                        sala["host_id"] = next(iter(sala["jugadores"].keys()))
                    else:
                        salas_activas.pop(codigo, None)
                        bitacora_global.registrar("INFO", "SALA", f"Sala {codigo} cerrada por falta de jugadores.")
                elif not sala["jugadores"]:
                    salas_activas.pop(codigo, None)
                    bitacora_global.registrar("INFO", "SALA", f"Sala {codigo} cerrada por falta de jugadores.")
        finally:
            mutex_red.release()


async def main():
    print("=" * 60)
    print("INICIANDO SERVIDOR DE JUEGO (MULTI-SALA)")
    print(f"Escuchando en 0.0.0.0:{PORT}")
    print("=" * 60)

    asyncio.create_task(enviar_estado_mundo())
    asyncio.create_task(ciclo_cinta_hacker())
    asyncio.create_task(ciclo_drenaje_pasivo())

    async with websockets.serve(manejador_cliente, "0.0.0.0", PORT):
        await asyncio.Future()


if __name__ == "__main__":
    import sys

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
