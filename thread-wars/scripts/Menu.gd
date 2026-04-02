extends Control

# ==========================================
# RUTAS DE LAS FASES
# ==========================================
@onready var fase_1 = $Fase1_Nombre
@onready var fase_2 = $Fase2_Equipo
@onready var fase_3 = $Fase3_Avatar

# ==========================================
# RUTAS: FASE 1 (Nombre)
# ==========================================
@onready var input_nombre: LineEdit = $Fase1_Nombre/InputName
@onready var input_codigo_sala: LineEdit = $Fase1_Nombre/InputCodigoSala
@onready var label_modo_sala: Label = $Fase1_Nombre/LabelModoSala

# ==========================================
# RUTAS: FASE 2 (Equipo)
# ==========================================
@onready var btn_hacker: Button     = $Fase2_Equipo/BtnHacker
@onready var btn_admin: Button      = $Fase2_Equipo/BtnAdmin
@onready var label_status: Label    = $Fase2_Equipo/LabelStatus

# ==========================================
# RUTAS: FASE 3 (Avatar)
# ==========================================
@onready var avatar_preview: TextureRect = $Fase3_Avatar/AvatarPreview
@onready var label_avatar: Label         = $Fase3_Avatar/LabelAvatar

# Variables de memoria
var _lista_avatares: Array[String] = []   
var _indice_avatar: int = 0
const RUTA_AVATARES := "res://assets/characters/"
var _modo_sala: String = "crear"

func _ready():
	# Al iniciar, solo mostramos la Fase 1
	fase_1.show()
	fase_2.hide()
	fase_3.hide()
	
	_cargar_lista_avatares()
	_mostrar_avatar_actual()
	_actualizar_ui_modo_sala()

func _process(_delta: float):
	# Balanceo en tiempo real (solo importa si estamos en la fase 2)
	if fase_2.visible and NetworkManager.estado_mundo.has("jugadores"):
		var hackers: int = 0
		var admins: int  = 0
		var jugadores: Dictionary = NetworkManager.estado_mundo["jugadores"]
		for id: String in jugadores:
			if jugadores[id].get("rol") == "CLIENTE": hackers += 1
			if jugadores[id].get("rol") == "ADMIN":   admins  += 1

		label_status.text = "Servidor Online | Hackers: %d | Defensores: %d" % [hackers, admins]
		btn_hacker.disabled = (hackers >= admins + 2)
		btn_admin.disabled  = (admins  >= hackers + 2)
	elif fase_2.visible:
		label_status.text = "Conectando al servidor Python..."

# ==========================================
# BOTONES: FASE 1
# ==========================================
func _on_btn_continuar_pressed(): 
	var alias = input_nombre.text.strip_edges()
	if alias == "":
		alias = "Player_" + str(randi() % 1000) # Nombre por defecto si lo deja vacío
		
	NetworkManager.mi_nombre = alias
	NetworkManager.mi_rol_local = "PENDIENTE"
	
	# Ya no se elige bando aquí: el servidor lo asigna al iniciar partida.
	fase_1.hide()
	fase_3.show()

func _on_btn_modo_crear_pressed():
	_modo_sala = "crear"
	_actualizar_ui_modo_sala()

func _on_btn_modo_unirse_pressed():
	_modo_sala = "unirse"
	_actualizar_ui_modo_sala()

func _actualizar_ui_modo_sala():
	if not is_instance_valid(input_codigo_sala) or not is_instance_valid(label_modo_sala):
		return

	var es_unirse: bool = (_modo_sala == "unirse")
	input_codigo_sala.visible = es_unirse
	label_modo_sala.text = "Modo: Unirse a sala" if es_unirse else "Modo: Crear sala"

# ==========================================
# BOTONES: FASE 2
# ==========================================
func _on_btn_volver_fase2_pressed():
	# Regresar a la Fase 1
	fase_2.hide()
	fase_1.show()

func _on_btn_hacker_pressed():     avanzar_a_fase_3("CLIENTE")
func _on_btn_admin_pressed():      avanzar_a_fase_3("ADMIN")
func _on_btn_spectator_pressed():  avanzar_a_fase_3("ESPECTADOR")

func avanzar_a_fase_3(rol_elegido: String):
	NetworkManager.mi_rol_local = rol_elegido
	fase_2.hide()
	fase_3.show()

# ==========================================
# BOTONES: FASE 3
# ==========================================
func _on_btn_volver_fase3_pressed():
	# Regresar a la Fase 1
	fase_3.hide()
	fase_1.show()

func _on_btn_conectar_pressed():
	var avatar_elegido: String = "default"
	if not _lista_avatares.is_empty():
		avatar_elegido = _lista_avatares[_indice_avatar]
		
	NetworkManager.mi_avatar = avatar_elegido
	NetworkManager.mi_sala_codigo = ""
	NetworkManager.soy_host = false
	NetworkManager.limpiar_error()

	if _modo_sala == "crear":
		NetworkManager.enviar_accion("crear_sala", {
			"nombre": NetworkManager.mi_nombre,
			"rol": NetworkManager.mi_rol_local,
			"avatar": avatar_elegido,
		})
	else:
		var codigo = input_codigo_sala.text.strip_edges().to_upper()
		if codigo.length() != 4:
			if is_instance_valid(label_avatar):
				label_avatar.text = "Codigo invalido (4 caracteres)"
			return

		NetworkManager.enviar_accion("unirse_sala", {
			"codigo_sala": codigo,
			"nombre": NetworkManager.mi_nombre,
			"rol": NetworkManager.mi_rol_local,
			"avatar": avatar_elegido,
		})

	var timeout_s = 2.0
	var elapsed = 0.0
	while elapsed < timeout_s and NetworkManager.mi_sala_codigo == "" and NetworkManager.ultimo_error == "":
		await get_tree().create_timer(0.1).timeout
		elapsed += 0.1

	if NetworkManager.mi_sala_codigo == "":
		if is_instance_valid(label_avatar):
			if NetworkManager.ultimo_error != "":
				label_avatar.text = "Error: " + NetworkManager.ultimo_error
			else:
				label_avatar.text = "No se pudo conectar a la sala"
		return

	var ruta_mundo := "res://scenes/World/World.tscn"
	if not ResourceLoader.exists(ruta_mundo):
		ruta_mundo = "res://scenes/World/World.tscn" 
		
	get_tree().change_scene_to_file(ruta_mundo)

# ==========================================
# LÓGICA DE AVATARES
# ==========================================
func _cargar_lista_avatares():
	_lista_avatares.clear()
	if DirAccess.dir_exists_absolute(RUTA_AVATARES):
		var dir := DirAccess.open(RUTA_AVATARES)
		dir.list_dir_begin()
		var archivo: String = dir.get_next()
		while archivo != "":
			if archivo.ends_with(".png"):
				_lista_avatares.append(archivo.get_basename())
			archivo = dir.get_next()
		dir.list_dir_end()
		_lista_avatares.sort()

func _mostrar_avatar_actual():
	if _lista_avatares.is_empty():
		if is_instance_valid(label_avatar): label_avatar.text = "Sin sprites"
		return

	var nombre_avatar: String = _lista_avatares[_indice_avatar]
	var ruta_tex: String = RUTA_AVATARES + nombre_avatar + ".png"

	if is_instance_valid(avatar_preview):
		var tex := load(ruta_tex) as Texture2D
		if tex:
			var atlas = AtlasTexture.new()
			atlas.atlas = tex
			var frame_ancho = tex.get_width() / 3
			var frame_alto = tex.get_height() / 4
			atlas.region = Rect2(frame_ancho * 1, 0, frame_ancho, frame_alto)
			avatar_preview.texture = atlas

	if is_instance_valid(label_avatar):
		label_avatar.text = "%s" % [nombre_avatar]

func _on_btn_avatar_izq_pressed():
	if not _lista_avatares.is_empty():
		_indice_avatar = (_indice_avatar - 1 + _lista_avatares.size()) % _lista_avatares.size()
		_mostrar_avatar_actual()

func _on_btn_avatar_der_pressed():
	if not _lista_avatares.is_empty():
		_indice_avatar = (_indice_avatar + 1) % _lista_avatares.size()
		_mostrar_avatar_actual()
