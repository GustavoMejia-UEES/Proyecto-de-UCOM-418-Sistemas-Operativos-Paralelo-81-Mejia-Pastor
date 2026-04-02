extends Node2D

const ESCENA_PLAYER   := preload("res://scenes/Player/Player.tscn")
var jugadores_instanciados: Dictionary = {}

const SPAWN_ADMIN:      Vector2 = Vector2(512, 512)   # Mitad de arriba
const SPAWN_HACKER:     Vector2 = Vector2(512, 1800)  # Mitad de abajo
const SPAWN_ESPECTADOR: Vector2 = Vector2(512, 1024)  # En todo el centro

var _overlay_lobby: CanvasLayer
var _label_lobby: Label
var _btn_iniciar: Button

func _ready():
	_crear_ui_lobby()

func _process(_delta: float):
	if not NetworkManager.estado_mundo.has("jugadores"):
		_actualizar_ui_lobby()
		return

	var jugadores_red: Dictionary = NetworkManager.estado_mundo["jugadores"]

	for id_ws: String in jugadores_red:
		var datos: Dictionary = jugadores_red[id_ws]

		if not jugadores_instanciados.has(id_ws):
			var nuevo := ESCENA_PLAYER.instantiate()
			nuevo.set("id_ws", id_ws)
			
			var nombre_red = datos.get("nombre")
			var rol_red = datos.get("rol")
			if nombre_red == null: nombre_red = ""
			if rol_red == null: rol_red = "CLIENTE"

			var es_yo: bool = (str(nombre_red) == NetworkManager.mi_nombre)
			nuevo.set("es_local", es_yo)

			match str(rol_red):
				"ADMIN":      nuevo.position = SPAWN_ADMIN
				"ESPECTADOR": nuevo.position = SPAWN_ESPECTADOR
				_:            nuevo.position = SPAWN_HACKER

			add_child(nuevo)
			jugadores_instanciados[id_ws] = nuevo

		if jugadores_instanciados[id_ws].has_method("actualizar_datos"):
			jugadores_instanciados[id_ws].actualizar_datos(datos)

	var ids_a_borrar: Array = []
	for id_ws_existente: String in jugadores_instanciados:
		if not jugadores_red.has(id_ws_existente):
			jugadores_instanciados[id_ws_existente].queue_free()
			ids_a_borrar.append(id_ws_existente)
	for id_borrar in ids_a_borrar:
		jugadores_instanciados.erase(id_borrar)

	var yo = _obtener_jugador_local()
	if not yo.is_empty():
		NetworkManager.mi_rol_local = str(yo.get("rol", NetworkManager.mi_rol_local))

	_actualizar_ui_lobby()

	# ==========================================
	# ACTUALIZAR EL HUD (Si la partida ya inició)
	# ==========================================
	if has_node("HUD"):
		$HUD.actualizar_hud(NetworkManager.estado_mundo, NetworkManager.mi_rol_local)


func _crear_ui_lobby():
	_overlay_lobby = CanvasLayer.new()
	add_child(_overlay_lobby)

	# El panel oscuro de arriba para el texto
	var panel := Panel.new()
	panel.set_anchors_preset(Control.PRESET_TOP_WIDE)
	panel.offset_left = 16
	panel.offset_top = 16
	panel.offset_right = -16
	panel.offset_bottom = 100 # Lo hicimos un poco más delgado
	_overlay_lobby.add_child(panel)

	# El texto que dice "Sala XXXX | Eres anfitrión..."
	_label_lobby = Label.new()
	_label_lobby.position = Vector2(20, 0)
	_label_lobby.size = Vector2(950, 84)
	_label_lobby.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER # Lo centramos
	_label_lobby.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_label_lobby.add_theme_font_size_override("font_size", 28)
	panel.add_child(_label_lobby)

	# El Botón GIGANTE centrado en la parte inferior
	_btn_iniciar = Button.new()
	_btn_iniciar.text = "INICIAR JUEGO"
	_btn_iniciar.size = Vector2(300, 80)
	# Pantalla = 1024 ancho. (1024 - 300) / 2 = 362 (Para centrarlo perfecto en X)
	# Y = 800 (Para ponerlo en la parte de abajo)
	_btn_iniciar.position = Vector2(362, 800) 
	_btn_iniciar.add_theme_font_size_override("font_size", 32)
	_btn_iniciar.pressed.connect(_on_btn_iniciar_pressed)
	
	# OJO: Lo añadimos directamente al overlay, NO al panel de arriba
	_overlay_lobby.add_child(_btn_iniciar)
	
func _on_btn_iniciar_pressed():
	NetworkManager.enviar_accion("iniciar_partida", {})

func _actualizar_ui_lobby():
	if _overlay_lobby == null:
		return

	var fase = str(NetworkManager.estado_mundo.get("fase", "LOBBY"))
	var codigo = str(NetworkManager.estado_mundo.get("codigo_sala", NetworkManager.mi_sala_codigo))

	# Si la partida ya empezó, ocultamos el overlay del lobby
	if fase != "LOBBY":
		_overlay_lobby.visible = false
		return

	_overlay_lobby.visible = true

	var jugador_local = _obtener_jugador_local()
	var es_host = bool(jugador_local.get("es_host", false))
	var rol_local = str(jugador_local.get("rol", NetworkManager.mi_rol_local))

	if es_host:
		_label_lobby.text = "Sala %s | Eres anfitrion. Espera a todos y arranca la partida." % codigo
		_btn_iniciar.visible = true
		_btn_iniciar.disabled = false
	else:
		_btn_iniciar.visible = false
		if rol_local == "CLIENTE":
			_label_lobby.text = "Sala %s | Esperando al anfitrion..." % codigo
		else:
			_label_lobby.text = "Sala %s | Esperando al lider..." % codigo

func _obtener_jugador_local() -> Dictionary:
	var jugadores = NetworkManager.estado_mundo.get("jugadores", {})
	if not (jugadores is Dictionary):
		return {}

	for id_ws in jugadores:
		var data = jugadores[id_ws]
		if str(data.get("nombre", "")) == NetworkManager.mi_nombre:
			return data

	return {}
