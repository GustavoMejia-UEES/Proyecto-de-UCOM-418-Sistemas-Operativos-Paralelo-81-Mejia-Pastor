extends Area2D

@onready var core = get_parent()

var nodo_actual: Area2D = null
var pad_actual: Area2D = null
var item_actual: Area2D = null
var mutex_actual: Area2D = null

var _cooldown_press: float = 0.0
var _cooldown_recarga: float = 0.0 
const COOLDOWN_MAX: float = 0.2

func _ready():
	# HACK INDESTRUCTIBLE: Obligamos a esta área a detectar TODAS las capas
	collision_layer = 0
	collision_mask = 1 | 2 | 4 | 8 | 16 | 32 
	
	area_entered.connect(_on_area_entered)
	area_exited.connect(_on_area_exited)

func _unhandled_input(event: InputEvent):
	if not core.es_local: return
	if _cooldown_press > 0.0: return
	
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode == KEY_E:
			_intentar_interactuar_e()

func _physics_process(delta: float):
	if _cooldown_press > 0.0: _cooldown_press -= delta
	if _cooldown_recarga > 0.0: _cooldown_recarga -= delta

	if not core.es_local: return

	# Mutex (F)
	if mutex_actual != null and core.rol == "ADMIN":
		if Input.is_physical_key_pressed(KEY_F):
			core.tiempo_f_held += delta
			if core.tiempo_f_held >= core.F_HOLD_MAX:
				core.tiempo_f_held = 0.0
				NetworkManager.enviar_accion("liberar_mutex", {"mutex_id": mutex_actual.get("id_mutex")})
		else:
			core.tiempo_f_held = 0.0
	else:
		core.tiempo_f_held = 0.0

func _intentar_interactuar_e():
	# 1. PRIORIDAD: Recoger Ítems
	if item_actual != null:
		_cooldown_press = COOLDOWN_MAX
		NetworkManager.enviar_accion("recoger_item", {"id_item": item_actual.get("id_item")})
		
	# 2. PRIORIDAD: Recargar Energía
	elif pad_actual != null:
		if _cooldown_recarga <= 0.0:
			NetworkManager.enviar_accion("recargar", {})
			_cooldown_recarga = 0.5 
			
	# 3. PRIORIDAD: Atacar / Reparar PC
	elif nodo_actual != null:
		var id_n = str(nodo_actual.get("id_nodo"))

		# ==========================================
		# 📡 LEEMOS EL ESTADO REAL DE LA RED
		# ==========================================
		var estado_nodo = "LIBRE"
		if NetworkManager.estado_mundo.has("nodos") and NetworkManager.estado_mundo["nodos"].has(id_n):
			estado_nodo = NetworkManager.estado_mundo["nodos"][id_n].get("estado", "LIBRE")

		# --- REGLAS DEL HACKER ---
		if core.rol == "CLIENTE":
			if core.archivo_equipado == "":
				print("¡Bloqueado! No tienes archivo.")
				return
			if estado_nodo == "CORRUPTO":
				print("¡Esa PC ya está destruida!")
				return

		# --- REGLAS DEL ADMIN ---
		elif core.rol == "ADMIN":
			if core.herramienta_equipada == "":
				print("¡Manos vacías! Ve a la caja por un parche.")
				return
			if estado_nodo == "LIBRE":
				print("¡El servidor está sano! No gastes tu parche aquí.")
				return
			if estado_nodo == "CORRUPTO":
				print("¡Demasiado tarde! Este servidor está frito y no se puede reparar.")
				return # <-- ESTO BLOQUEA QUE EL ADMIN SE BUGEE

		# ¡Vía libre! Enviamos la acción a Python
		_cooldown_press = COOLDOWN_MAX
		core.global_position = nodo_actual.global_position + Vector2(0, 80)
		NetworkManager.enviar_accion("moverse", {"x": core.global_position.x, "y": core.global_position.y})
		
		var nodo_visuals = core.get_node("Visuals")
		if nodo_visuals:
			nodo_visuals._ultima_direccion = 3 
			nodo_visuals.sprite_avatar.frame = 10 

		if core.rol == "CLIENTE":
			NetworkManager.enviar_accion("atacar_nodo", {"nodo": int(id_n)})
		elif core.rol == "ADMIN":
			print("¡Godot SÍ envió curación al Nodo ", id_n, "!") 
			NetworkManager.enviar_accion("reparar_nodo", {"nodo": int(id_n)})

# DETECCIÓN A PRUEBA DE BALAS
func _on_area_entered(area: Area2D):
	if not core.es_local: return
	
	if area.get("id_item") != null: 
		item_actual = area
	elif area.get("id_nodo") != null: 
		nodo_actual = area
	elif area.get("id_mutex") != null: 
		mutex_actual = area
	elif area.get("es_pad") != null: 
		pad_actual = area

func _on_area_exited(area: Area2D):
	if not core.es_local: return
	if area == item_actual: 
		item_actual = null
	elif area == nodo_actual: 
		nodo_actual = null
		# ==========================================
		# 🔥 LA SALSA SECRETA: Le avisa a Python que soltaste la PC
		# ==========================================
		NetworkManager.enviar_accion("cancelar_interaccion", {})
	elif area == mutex_actual: 
		mutex_actual = null
	elif area == pad_actual: 
		pad_actual = null
