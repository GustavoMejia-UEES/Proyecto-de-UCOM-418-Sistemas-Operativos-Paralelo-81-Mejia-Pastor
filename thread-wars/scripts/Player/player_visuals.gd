extends Node2D

@onready var core = get_parent()
@onready var interactor = $"../Interactor"
@onready var sprite_avatar = $AvatarSprite
@onready var etiqueta_info = $NameLabel

var icon_arma: Sprite2D = null

var _avatar_cargado: String = ""
var _tiempo_anim: float = 0.0
var _ultima_direccion: int = 0
const ANIM_FPS: float = 6.0

func _ready():
	if sprite_avatar:
		sprite_avatar.hframes = 3
		sprite_avatar.vframes = 4
		sprite_avatar.texture_filter = TEXTURE_FILTER_NEAREST

	# MAGIA: Destruir el texto feo si el usuario olvidó borrarlo en el editor
	if has_node("WeaponLabel"):
		get_node("WeaponLabel").queue_free()

	# MAGIA 2: Crear el Sprite2D de la cabeza automáticamente si no existe
	if has_node("WeaponIcon") and get_node("WeaponIcon") is Sprite2D:
		icon_arma = get_node("WeaponIcon")
	else:
		icon_arma = Sprite2D.new()
		icon_arma.name = "WeaponIcon"
		icon_arma.position = Vector2(0, -60) # Flotando sobre la cabeza
		add_child(icon_arma)

func _process(delta):
	_animar_sprite(delta)
	if core.es_local:
		queue_redraw()

func actualizar_apariencia():
	if etiqueta_info:
		if core.rol == "ESPECTADOR": etiqueta_info.text = core.nombre_jugador + " (DIOS)"
		else: etiqueta_info.text = core.nombre_jugador

	# ACTUALIZAR EL ICONO DEL ARMA
	if icon_arma:
		var item_actual = ""
		if core.rol == "CLIENTE": item_actual = core.archivo_equipado
		elif core.rol == "ADMIN": item_actual = core.herramienta_equipada
			
		if item_actual != "":
			var nombre_png = item_actual.replace("PARCHE_", "")
			var ruta_icono = "res://assets/icons/" + nombre_png + ".png"
			
			# CARGA DIRECTA A PRUEBA DE WEB
			var tex_icono = load(ruta_icono)
			if tex_icono != null:
				icon_arma.texture = tex_icono
				icon_arma.modulate = Color(0.3, 0.8, 1.0) if "PARCHE" in item_actual else Color.WHITE
				icon_arma.show()
			else:
				icon_arma.hide()
		else:
			icon_arma.hide()

	# CARGA DE AVATAR A PRUEBA DE WEB
	if sprite_avatar and core.avatar != "" and core.avatar != _avatar_cargado:
		var ruta: String = "res://assets/characters/" + core.avatar + ".png"
		var tex_avatar = load(ruta)
		
		if tex_avatar != null:
			sprite_avatar.texture = tex_avatar
			_avatar_cargado = core.avatar

	if sprite_avatar:
		if core.rol == "ESPECTADOR": sprite_avatar.modulate = Color(1.0, 1.0, 1.0, 0.45)
		elif core.rol == NetworkManager.mi_rol_local: sprite_avatar.modulate = Color.WHITE
		else: sprite_avatar.modulate = Color(1.0, 0.4, 0.4, 1.0)
			
	queue_redraw()

func _animar_sprite(delta: float):
	if not sprite_avatar: return
	var vel = core.velocity
	var direccion = vel.normalized()
	var moviendose: bool = vel.length() > 10.0

	if moviendose:
		if abs(direccion.y) >= abs(direccion.x):
			_ultima_direccion = 0 if direccion.y > 0 else 3
		else:
			_ultima_direccion = 2 if direccion.x > 0 else 1

		_tiempo_anim += delta * ANIM_FPS
		var anim_frames: Array[int] = [0, 1, 2, 1]
		var anim_idx: int = int(_tiempo_anim) % anim_frames.size()
		sprite_avatar.frame = _ultima_direccion * 3 + anim_frames[anim_idx]
	else:
		_tiempo_anim = 0.0
		sprite_avatar.frame = _ultima_direccion * 3 + 1

func _draw():
	if not core.es_local: return

	if core.rol == "CLIENTE":
		var ratio: float  = clamp(float(core.energia) / 100.0, 0.0, 1.0)
		draw_rect(Rect2(-60, -40, 8, 80), Color(0.1, 0.1, 0.1))
		var altura_llena = 80.0 * ratio
		draw_rect(Rect2(-60, -40 + (80.0 - altura_llena), 8, altura_llena), Color.YELLOW)

	if interactor:
		# TEXTOS FLOTANTES
		if interactor.item_actual != null:
			var pos = to_local(interactor.item_actual.global_position)
			draw_string(ThemeDB.fallback_font, pos + Vector2(-35, -30), "[E] RECOGER", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color.GREEN)
		elif interactor.nodo_actual != null:
			var pos = to_local(interactor.nodo_actual.global_position)
			var txt = "[E] ATACAR" if core.rol == "CLIENTE" else "[E] REPARAR"
			var col = Color.YELLOW if core.rol == "CLIENTE" else Color.CYAN
			draw_string(ThemeDB.fallback_font, pos + Vector2(-35, -80), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, col)
		elif interactor.pad_actual != null:
			var pos = to_local(interactor.pad_actual.global_position)
			draw_string(ThemeDB.fallback_font, pos + Vector2(-40, -40), "[E] RECARGAR", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color.ORANGE)
