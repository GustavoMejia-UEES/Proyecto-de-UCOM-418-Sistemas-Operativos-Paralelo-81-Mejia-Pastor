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

# ==========================================
# 🛡️ DICCIONARIOS DE PRE-CARGA WEB
# Obligan a Godot a empaquetar estas imágenes sí o sí
# ==========================================
var dic_personajes = {
	"char_01": preload("res://assets/characters/char_01.png"),
	"char_02": preload("res://assets/characters/char_02.png"),
	"char_03": preload("res://assets/characters/char_03.png"),
	"char_04": preload("res://assets/characters/char_04.png"),
	"char_05": preload("res://assets/characters/char_05.png"),
	"char_06": preload("res://assets/characters/char_06.png"),
	"char_07": preload("res://assets/characters/char_07.png"),
	"char_08": preload("res://assets/characters/char_08.png"),
	"char_09": preload("res://assets/characters/char_09.png"),
	"char_10": preload("res://assets/characters/char_10.png"),
	"char_11": preload("res://assets/characters/char_11.png"),
	"char_12": preload("res://assets/characters/char_12.png"),
	"char_13": preload("res://assets/characters/char_13.png"),
	"char_14": preload("res://assets/characters/char_14.png"),
	"char_15": preload("res://assets/characters/char_15.png"),
	"char_16": preload("res://assets/characters/char_16.png"),
	"char_17": preload("res://assets/characters/char_17.png"),
	"char_18": preload("res://assets/characters/char_18.png"),
	"char_19": preload("res://assets/characters/char_19.png"),
	"char_20": preload("res://assets/characters/char_20.png")
}

var dic_iconos = {
	"TEXTO": preload("res://assets/icons/TEXTO.png"),
	"AUDIO": preload("res://assets/icons/AUDIO.png"),
	"VIDEO": preload("res://assets/icons/VIDEO.png")
}

func _ready():
	if sprite_avatar:
		sprite_avatar.hframes = 3
		sprite_avatar.vframes = 4
		sprite_avatar.texture_filter = TEXTURE_FILTER_NEAREST

	if has_node("WeaponLabel"):
		get_node("WeaponLabel").queue_free()

	if has_node("WeaponIcon") and get_node("WeaponIcon") is Sprite2D:
		icon_arma = get_node("WeaponIcon")
	else:
		icon_arma = Sprite2D.new()
		icon_arma.name = "WeaponIcon"
		icon_arma.position = Vector2(0, -60) 
		add_child(icon_arma)

func _process(delta):
	_animar_sprite(delta)
	if core.es_local:
		queue_redraw()

func actualizar_apariencia():
	if etiqueta_info:
		if core.rol == "ESPECTADOR": etiqueta_info.text = core.nombre_jugador + " (DIOS)"
		else: etiqueta_info.text = core.nombre_jugador

	# ACTUALIZAR EL ICONO DEL ARMA (USANDO PRELOAD)
	if icon_arma:
		var item_actual = ""
		if core.rol == "CLIENTE": item_actual = core.archivo_equipado
		elif core.rol == "ADMIN": item_actual = core.herramienta_equipada
			
		if item_actual != "":
			var nombre_png = item_actual.replace("PARCHE_", "")
			
			if dic_iconos.has(nombre_png):
				icon_arma.texture = dic_iconos[nombre_png]
				icon_arma.modulate = Color(0.3, 0.8, 1.0) if "PARCHE" in item_actual else Color.WHITE
				icon_arma.show()
			else:
				icon_arma.hide()
		else:
			icon_arma.hide()

	# CARGA DE AVATAR (USANDO PRELOAD)
	if sprite_avatar and core.avatar != "" and core.avatar != _avatar_cargado:
		if dic_personajes.has(core.avatar):
			sprite_avatar.texture = dic_personajes[core.avatar]
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
