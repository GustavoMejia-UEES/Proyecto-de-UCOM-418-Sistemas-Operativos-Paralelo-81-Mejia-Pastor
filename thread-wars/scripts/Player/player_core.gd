extends CharacterBody2D

var id_ws: String = ""
var es_local: bool = false
var nombre_jugador: String = "Cargando..."
var rol: String = ""
var energia: int = 100
var avatar: String = ""
var archivo_equipado: String = ""
var herramienta_equipada: String = ""

var velocidad_movimiento: float = 300.0
var posicion_red: Vector2 = Vector2.ZERO
var tiempo_f_held: float = 0.0 
const F_HOLD_MAX: float = 3.0

@onready var visuals = $Visuals
@onready var camara = $Camera2D

var _rol_camara_configurado: bool = false

func _ready():
	if camara and not es_local:
		camara.enabled = false

func actualizar_datos(datos: Dictionary):
	var rol_anterior = rol
	var _nombre = datos.get("nombre")
	nombre_jugador = str(_nombre) if _nombre != null else "Desconocido"
	
	var _rol = datos.get("rol")
	rol = str(_rol) if _rol != null else "CLIENTE"
	
	var _energia = datos.get("energia")
	energia = int(_energia) if _energia != null else 0
	
	var _x = datos.get("x")
	var _y = datos.get("y")
	posicion_red = Vector2(float(_x) if _x != null else 0.0, float(_y) if _y != null else 0.0)
	
	if es_local and posicion_red.distance_to(global_position) > 200:
		global_position = posicion_red
	
	var _avatar = datos.get("avatar")
	avatar = str(_avatar) if _avatar != null else ""
	
	var _archivo = datos.get("archivo_equipado")
	archivo_equipado = str(_archivo) if _archivo != null else ""
	
	var _herr = datos.get("herramienta_equipada")
	herramienta_equipada = str(_herr) if _herr != null else ""

	if visuals and visuals.has_method("actualizar_apariencia"):
		visuals.actualizar_apariencia()

	if es_local and rol != "":
		if not _rol_camara_configurado or rol != rol_anterior:
			_configurar_camara()
			_rol_camara_configurado = true

func _physics_process(delta: float):
	if es_local:
		var direccion := Vector2.ZERO
		if Input.is_physical_key_pressed(KEY_D): direccion.x += 1
		if Input.is_physical_key_pressed(KEY_A): direccion.x -= 1
		if Input.is_physical_key_pressed(KEY_S): direccion.y += 1
		if Input.is_physical_key_pressed(KEY_W): direccion.y -= 1

		if direccion != Vector2.ZERO: direccion = direccion.normalized()

		velocity = direccion * velocidad_movimiento
		var se_movio: bool = velocity != Vector2.ZERO
		move_and_slide()

		if se_movio:
			NetworkManager.enviar_accion("moverse", {"x": global_position.x, "y": global_position.y})
	else:
		global_position = global_position.lerp(posicion_red, delta * 15.0)
		velocity = (posicion_red - global_position) / delta

func _configurar_camara():
	if not camara: return
	camara.enabled = true
	camara.make_current() 
	camara.limit_left  = 0
	camara.limit_right = 1024
	match rol:
		"CLIENTE":
			camara.limit_top    = 1024
			camara.limit_bottom = 2048
		"ADMIN":
			camara.limit_top    = 0
			camara.limit_bottom = 1024
		"ESPECTADOR":
			camara.limit_top    = 0
			camara.limit_bottom = 2048
