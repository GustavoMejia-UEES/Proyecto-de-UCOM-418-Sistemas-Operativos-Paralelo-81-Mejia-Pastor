extends CharacterBody2D

# ==========================================
# IDENTIDAD
# ==========================================
var id_ws: String = ""
var es_local: bool = false
var nombre_jugador: String = "Cargando..."
var rol: String = ""
var energia: int = 100
var avatar: String = ""             # "char_01" — lo manda Python en cada tick
var archivo_equipado: String    = ""   # "TEXTO" | "IMAGEN" | "VIDEO" — lo manda Python
var herramienta_equipada: String = ""  # "PARCHE" | "ANTIVIRUS" | "FIREWALL" — solo ADMIN

# ==========================================
# FLAGS DE ZONA
# ==========================================
var nodo_actual: Node      = null
var pad_actual: Node       = null
var en_mutex_station: bool = false
var mutex_id_actual: int   = -1
var item_actual: Node      = null   # FileItem cercano

# ==========================================
# FÍSICAS
# ==========================================
var velocidad_movimiento: float = 300.0
var posicion_red: Vector2 = Vector2.ZERO

# Última dirección para elegir fila del spritesheet
var _ultima_direccion: int = 0   # 0=abajo 1=izq 2=der 3=arriba

# Animación
var _tiempo_anim: float = 0.0
const ANIM_FPS: float = 6.0

# Cooldown entre E-presses
var _cooldown_press: float = 0.0
const COOLDOWN_MAX: float = 0.2

# F mantenido — liberar mutex (solo ADMIN)
var _tiempo_f_held: float = 0.0
const F_HOLD_MAX: float   = 3.0   # segundos para liberar mutex

# ==========================================
# NODOS VISUALES
# ==========================================
@onready var etiqueta_info: Label = $NameLabel
var sprite_avatar: Sprite2D = null
var label_arma: Label = null
var _avatar_cargado: String = ""

# Cámara de zona
var camara: Camera2D = null
var _rol_camara_configurado: bool = false

func _ready():
	# CollisionShape2D si el .tscn no tiene
	var tiene_col: bool = false
	for c in get_children():
		if c is CollisionShape2D:
			tiene_col = true
			break
	if not tiene_col:
		var s := CollisionShape2D.new()
		var r := RectangleShape2D.new()
		r.size = Vector2(32, 32)
		s.shape = r
		add_child(s)

	if has_node("AvatarSprite"):
		sprite_avatar = $AvatarSprite
		sprite_avatar.hframes = 3
		sprite_avatar.vframes = 4
		sprite_avatar.frame   = 1

	if has_node("WeaponLabel"):
		label_arma = $WeaponLabel

	if es_local:
		camara = Camera2D.new()
		camara.enabled = true
		add_child(camara)

# ==========================================
# INPUT
# ==========================================
func _unhandled_input(event: InputEvent):
	if not es_local:
		return
	if not (event is InputEventKey and event.pressed and not event.echo):
		return

	match event.physical_keycode:
		KEY_E: _intentar_interactuar()

# ==========================================
# ACCIONES
# ==========================================
func _intentar_interactuar():
	if _cooldown_press > 0.0:
		return

	# Prioridad: FileItem > PC > (pad se maneja con E mantenido en _physics_process)
	if item_actual != null and is_instance_valid(item_actual):
		_accion_recoger_item()
	elif nodo_actual != null:
		_accion_en_nodo()

func _accion_recoger_item():
	_cooldown_press = COOLDOWN_MAX
	NetworkManager.enviar_accion("recoger_item", {
		"id_item": item_actual.get("id_item")
	})

func _accion_en_nodo():
	_cooldown_press = COOLDOWN_MAX
	if rol == "CLIENTE":
		# Python lee la clave "nodo" (no "nodo_id")
		NetworkManager.enviar_accion("atacar_nodo", {
			"nodo": nodo_actual.id_nodo
		})
	elif rol == "ADMIN":
		NetworkManager.enviar_accion("reparar_nodo", {
			"nodo": nodo_actual.id_nodo
		})

# ==========================================
# ACTUALIZACIÓN DESDE PYTHON
# ==========================================
func actualizar_datos(datos: Dictionary):
	nombre_jugador  = datos.get("nombre",           "Desconocido")
	rol             = datos.get("rol",              "CLIENTE")
	energia         = datos.get("energia",          0)
	posicion_red    = Vector2(datos.get("x", 0.0),  datos.get("y", 0.0))
	avatar          = datos.get("avatar",           "")
	archivo_equipado     = datos.get("archivo_equipado",    "")
	herramienta_equipada = datos.get("herramienta_equipada", "")

	if is_instance_valid(etiqueta_info):
		if rol == "ESPECTADOR":
			etiqueta_info.text = nombre_jugador + " (MODO DIOS)"
		else:
			etiqueta_info.text = nombre_jugador + " E:" + str(energia)

	# WeaponLabel — muestra archivo (hacker) o herramienta (admin)
	if is_instance_valid(label_arma):
		if rol == "CLIENTE" and archivo_equipado != "":
			var iconos_archivo: Dictionary = {
				"TEXTO":  "[TXT]",
				"IMAGEN": "[IMG]",
				"VIDEO":  "[VID]",
			}
			label_arma.text = iconos_archivo.get(archivo_equipado, archivo_equipado)
		elif rol == "ADMIN" and herramienta_equipada != "":
			var iconos_herr: Dictionary = {
				"PARCHE":    "[PAR]",
				"ANTIVIRUS": "[AV]",
				"FIREWALL":  "[FW]",
			}
			label_arma.text = iconos_herr.get(herramienta_equipada, herramienta_equipada)
		else:
			label_arma.text = ""

	_cargar_avatar_si_cambio()
	_aplicar_tinte_equipo()

	if es_local and not _rol_camara_configurado and rol != "":
		_configurar_camara_por_zona()
		_rol_camara_configurado = true

# ==========================================
# AVATAR Y COLOR DE EQUIPO
# ==========================================
func _cargar_avatar_si_cambio():
	if not is_instance_valid(sprite_avatar):
		return
	if avatar == "" or avatar == _avatar_cargado:
		return
	var ruta: String = "res://assets/characters/" + avatar + ".png"
	if ResourceLoader.exists(ruta):
		sprite_avatar.texture = load(ruta)
		_avatar_cargado = avatar
	else:
		push_warning("Player.gd: no existe el avatar '%s'" % ruta)

func _aplicar_tinte_equipo():
	if not is_instance_valid(sprite_avatar):
		queue_redraw()
		return

	var color: Color
	if rol == "ESPECTADOR":
		color = Color(1.0, 1.0, 1.0, 0.45)
		z_index = 10
	elif NetworkManager.mi_rol_local == "ESPECTADOR":
		color = Color.GREEN_YELLOW if rol == "CLIENTE" else Color.MEDIUM_PURPLE
	elif rol == NetworkManager.mi_rol_local:
		color = Color.WHITE
	else:
		color = Color(1.0, 0.4, 0.4, 1.0)
	sprite_avatar.modulate = color

# ==========================================
# DRAW — fallback + barra de energía + íconos
# ==========================================
const _COLORES_ARCHIVO: Dictionary = {
	"TEXTO":    Color(0.2,  0.5,  1.0,  0.95),
	"IMAGEN":   Color(1.0,  0.55, 0.1,  0.95),
	"VIDEO":    Color(0.85, 0.05, 0.15, 0.95),
	"PARCHE":   Color(0.2,  0.8,  0.3,  0.95),
	"ANTIVIRUS":Color(0.1,  0.7,  1.0,  0.95),
	"FIREWALL": Color(0.6,  0.2,  1.0,  0.95),
}

func _draw():
	# Siempre dibuja el rectángulo base (visible sin textura o como indicador de equipo)
	var sin_textura: bool = (not is_instance_valid(sprite_avatar)) or (sprite_avatar.texture == null)
	var color_eq: Color
	if rol == "ESPECTADOR":
		color_eq = Color(1.0, 1.0, 1.0, 0.4)
	elif rol == NetworkManager.mi_rol_local:
		color_eq = Color.DODGER_BLUE
	else:
		color_eq = Color.CRIMSON
	if sin_textura:
		draw_rect(Rect2(-16, -16, 32, 32), color_eq)
	# Borde siempre visible para saber quién eres tú
	if es_local:
		draw_rect(Rect2(-18, -18, 36, 36), Color.WHITE, false, 2.0)

	# Barra de energía (solo Hackers)
	if rol == "CLIENTE":
		var ratio: float  = clamp(float(energia) / 100.0, 0.0, 1.0)
		var bar_color: Color
		if ratio > 0.6:
			bar_color = Color(0.1, 0.9, 0.1)
		elif ratio > 0.3:
			bar_color = Color(1.0, 0.8, 0.0)
		else:
			bar_color = Color(0.9, 0.1, 0.1)
		draw_rect(Rect2(-16, -24, 32, 4), Color(0.1, 0.1, 0.1))
		draw_rect(Rect2(-16, -24, 32.0 * ratio, 4), bar_color)

	# Ícono de ítem equipado sobre la cabeza (hacker = archivo, admin = herramienta)
	var item_visual: String = ""
	if rol == "CLIENTE" and archivo_equipado != "":
		item_visual = archivo_equipado
	elif rol == "ADMIN" and herramienta_equipada != "":
		item_visual = herramienta_equipada

	if item_visual != "":
		var ic: Color = _COLORES_ARCHIVO.get(item_visual, Color(0.6, 0.6, 0.6, 0.9))
		draw_rect(Rect2(-8, -46, 16, 16), ic)
		draw_rect(Rect2(-8, -46, 16, 16), Color.WHITE, false, 1.0)
		var letra: String = item_visual.left(1) if item_visual != "ANTIVIRUS" else "AV"
		draw_string(ThemeDB.fallback_font, Vector2(-5, -32), letra, HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color.WHITE)

	# Barra de progreso de F mantenido (ADMIN en mutex caliente)
	if es_local and en_mutex_station and rol == "ADMIN" and _tiempo_f_held > 0.0:
		var f_ratio: float = clamp(_tiempo_f_held / F_HOLD_MAX, 0.0, 1.0)
		draw_rect(Rect2(-16, -32, 32, 5), Color(0.1, 0.1, 0.1))
		draw_rect(Rect2(-16, -32, 32.0 * f_ratio, 5), Color(0.3, 0.5, 1.0))

# ==========================================
# CÁMARA POR ZONA
# ==========================================
func _configurar_camara_por_zona():
	if not is_instance_valid(camara):
		return
	camara.limit_left  = 0
	camara.limit_right = 1024
	match rol:
		"CLIENTE":
			camara.limit_top    = 512
			camara.limit_bottom = 1024
			collision_layer = 1
			collision_mask  = 1
		"ADMIN":
			camara.limit_top    = 0
			camara.limit_bottom = 512
			collision_layer = 2
			collision_mask  = 2
		"ESPECTADOR":
			camara.limit_top    = 0
			camara.limit_bottom = 1024
			collision_layer = 4
			collision_mask  = 0

# ==========================================
# MOVIMIENTO + ANIMACIÓN + COOLDOWNS
# ==========================================
func _physics_process(delta: float):
	if _cooldown_press > 0.0:
		_cooldown_press -= delta

	if es_local:
		var direccion := Vector2.ZERO
		if Input.is_physical_key_pressed(KEY_D): direccion.x += 1
		if Input.is_physical_key_pressed(KEY_A): direccion.x -= 1
		if Input.is_physical_key_pressed(KEY_S): direccion.y += 1
		if Input.is_physical_key_pressed(KEY_W): direccion.y -= 1

		# E mantenido en pad → recargar energía
		if pad_actual != null and Input.is_physical_key_pressed(KEY_E):
			NetworkManager.enviar_accion("recargar", {})

		# F mantenido en mutex (solo ADMIN) → liberar mutex
		if en_mutex_station and rol == "ADMIN":
			if Input.is_physical_key_pressed(KEY_F):
				_tiempo_f_held += delta
				queue_redraw()
				if _tiempo_f_held >= F_HOLD_MAX:
					_tiempo_f_held = 0.0
					NetworkManager.enviar_accion("liberar_mutex", {
						"mutex_id": mutex_id_actual
					})
			else:
				if _tiempo_f_held > 0.0:
					_tiempo_f_held = 0.0
					queue_redraw()
		else:
			_tiempo_f_held = 0.0

		if direccion != Vector2.ZERO:
			direccion = direccion.normalized()

		velocity = direccion * velocidad_movimiento
		var se_movio: bool = velocity != Vector2.ZERO
		_animar_sprite(direccion, delta)
		move_and_slide()

		if se_movio:
			NetworkManager.enviar_accion("moverse", {
				"x": global_position.x,
				"y": global_position.y
			})
	else:
		var prev_pos: Vector2 = global_position
		global_position = global_position.lerp(posicion_red, delta * 15.0)
		var dir_remota: Vector2 = (global_position - prev_pos).normalized()
		_animar_sprite(dir_remota, delta)

func _animar_sprite(direccion: Vector2, delta: float):
	if not is_instance_valid(sprite_avatar):
		return

	var moviendose: bool = direccion.length() > 0.1

	if moviendose:
		if abs(direccion.y) >= abs(direccion.x):
			_ultima_direccion = 0 if direccion.y > 0 else 3
		else:
			_ultima_direccion = 2 if direccion.x > 0 else 1

	if moviendose:
		_tiempo_anim += delta * ANIM_FPS
		var anim_frames: Array[int] = [0, 1, 2, 1]
		var anim_idx: int = int(_tiempo_anim) % anim_frames.size()
		sprite_avatar.frame = _ultima_direccion * 3 + anim_frames[anim_idx]
	else:
		_tiempo_anim = 0.0
		sprite_avatar.frame = _ultima_direccion * 3 + 1
