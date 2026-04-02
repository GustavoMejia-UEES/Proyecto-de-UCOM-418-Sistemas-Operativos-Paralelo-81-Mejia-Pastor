extends Node

var socket = WebSocketPeer.new()
var url = "ws://localhost:8765"
var estado_mundo = {}
var conectado = false

var mi_rol_local: String = ""
var mi_nombre: String    = ""
var mi_avatar: String    = ""   # ej: "char_01" — sin extensión
var mi_sala_codigo: String = ""
var soy_host: bool = false

var ultimo_error: String = ""
var ultima_respuesta_accion: Dictionary = {}

func _ready():
	print("Conectando al servidor Python...")
	socket.connect_to_url(url)

func _process(_delta):
	socket.poll()
	var state = socket.get_ready_state()
	
	if state == WebSocketPeer.STATE_OPEN:
		if not conectado:
			conectado = true
			print("¡Conexión establecida con Python!")
		
		while socket.get_available_packet_count():
			var packet = socket.get_packet()
			var dict = JSON.parse_string(packet.get_string_from_utf8())
			if dict == null:
				continue

			if dict is Dictionary and dict.has("tipo"):
				_procesar_evento_servidor(dict)
			else:
				# Compatibilidad con payload antiguo sin envoltura "tipo".
				estado_mundo = dict

	elif state == WebSocketPeer.STATE_CLOSED:
		if conectado:
			print("Desconectado del servidor.")
			conectado = false

func enviar_accion(accion: String, datos_extra: Dictionary = {}):
	if socket.get_ready_state() == WebSocketPeer.STATE_OPEN:
		var mensaje = {}
		if accion != "": mensaje["accion"] = accion
		if mi_sala_codigo != "" and accion not in ["crear_sala", "unirse_sala"]:
			mensaje["codigo_sala"] = mi_sala_codigo
		mensaje.merge(datos_extra)
		socket.send_text(JSON.stringify(mensaje))

func limpiar_error():
	ultimo_error = ""

func _procesar_evento_servidor(evento: Dictionary):
	var tipo: String = str(evento.get("tipo", ""))

	if tipo == "estado_mundo":
		var payload = evento.get("payload")
		if payload is Dictionary:
			estado_mundo = payload
			if payload.has("codigo_sala"):
				mi_sala_codigo = str(payload.get("codigo_sala", ""))
		return

	if tipo == "sala_creada" or tipo == "sala_unida":
		if bool(evento.get("ok", false)):
			mi_sala_codigo = str(evento.get("codigo_sala", ""))
			soy_host = bool(evento.get("es_host", false))
			ultimo_error = ""
		else:
			ultimo_error = str(evento.get("motivo", "error_sala"))
		return

	if tipo == "accion_resultado":
		ultima_respuesta_accion = evento
		if not bool(evento.get("ok", false)):
			ultimo_error = str(evento.get("motivo", "accion_rechazada"))
		return

	if tipo == "error":
		ultimo_error = str(evento.get("motivo", "error"))
