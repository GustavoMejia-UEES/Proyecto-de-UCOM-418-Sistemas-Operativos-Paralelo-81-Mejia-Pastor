extends Area2D

# ==========================================
# IDENTIDAD — asignada por World._ready()
# ==========================================
var id_mutex: int = 0

# ==========================================
# ESTADO (desde Python)
# ==========================================
var caliente: bool = false
var ocupado:  bool = false

const COLOR_FRIO:     Color = Color(0.85, 0.2,  0.55, 0.88)
const COLOR_CALIENTE: Color = Color(1.0,  0.1,  0.4,  1.0)
const COLOR_OCUPADO:  Color = Color(0.3,  0.3,  1.0,  1.0)

var _tiempo: float = 0.0
var _jugador_encima: Node = null

func _ready():
	collision_mask = 3

	var shape_node := CollisionShape2D.new()
	var shape_res  := RectangleShape2D.new()
	shape_res.size = Vector2(32, 128)
	shape_node.shape = shape_res
	add_child(shape_node)

	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)

func _process(delta: float):
	_tiempo += delta

	if NetworkManager.estado_mundo.has("mutex_calientes"):
		var lista: Array = NetworkManager.estado_mundo["mutex_calientes"]
		var nuevo_caliente: bool = lista.has(id_mutex)
		if nuevo_caliente != caliente:
			caliente = nuevo_caliente

	queue_redraw()

func _draw():
	var pulso: float = 1.0
	var color: Color

	if ocupado:
		pulso = sin(_tiempo * 4.0) * 0.2 + 0.8
		color = Color(COLOR_OCUPADO.r, COLOR_OCUPADO.g, COLOR_OCUPADO.b, pulso)
	elif caliente:
		pulso = sin(_tiempo * 6.0) * 0.3 + 0.7
		color = Color(COLOR_CALIENTE.r, COLOR_CALIENTE.g, COLOR_CALIENTE.b, pulso)
	else:
		color = COLOR_FRIO

	# Cuerpo del mutex
	draw_rect(Rect2(-16, -16, 32, 32), color)
	draw_rect(Rect2(-16, -16, 32, 32), Color.WHITE, false, 2.0)

	# Ícono "M"
	draw_string(ThemeDB.fallback_font, Vector2(-7, 7), "M", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)

	# Aura de calor
	if caliente:
		var aura_alfa: float = sin(_tiempo * 5.0) * 0.2 + 0.3
		draw_rect(Rect2(-24, -24, 48, 48), Color(1.0, 0.3, 0.0, aura_alfa), false, 3.0)
		draw_string(ThemeDB.fallback_font, Vector2(-22, -22), "HOT", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color(1.0, 0.5, 0.0))

	# Hint contextual según quién esté encima
	if _jugador_encima != null and is_instance_valid(_jugador_encima):
		var rol_j: String = _jugador_encima.get("rol") if _jugador_encima.get("rol") != null else ""

		if rol_j == "ADMIN" and caliente:
			# Barra de progreso del F mantenido
			var t_held: float = _jugador_encima.get("_tiempo_f_held") if _jugador_encima.get("_tiempo_f_held") != null else 0.0
			var ratio: float  = clamp(t_held / 3.0, 0.0, 1.0)

			draw_rect(Rect2(-20, 22, 40, 6), Color(0.1, 0.1, 0.1, 0.9))
			draw_rect(Rect2(-20, 22, 40.0 * ratio, 6), Color(0.3, 0.5, 1.0))
			draw_string(ThemeDB.fallback_font, Vector2(-20, 20), "[F] ENFRIAR", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(0.5, 0.8, 1.0))
		elif rol_j == "ADMIN" and not caliente:
			draw_string(ThemeDB.fallback_font, Vector2(-18, 20), "FRIO", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(0.5, 0.9, 0.5))
		elif rol_j == "CLIENTE":
			draw_string(ThemeDB.fallback_font, Vector2(-14, 20), "MUTEX", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(0.8, 0.6, 0.8))
	else:
		# Hint estático cuando nadie está encima
		draw_string(ThemeDB.fallback_font, Vector2(-12, 28), "[F]", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(1.0, 1.0, 1.0, 0.5))

# ==========================================
# DETECCIÓN
# ==========================================
func _on_body_entered(body: Node2D):
	if body.get("es_local") == true:
		body.set("en_mutex_station", true)
		body.set("mutex_id_actual",  id_mutex)
		_jugador_encima = body
		ocupado = true
		queue_redraw()

func _on_body_exited(body: Node2D):
	if body.get("es_local") == true:
		body.set("en_mutex_station", false)
		body.set("mutex_id_actual",  -1)
		_jugador_encima = null
		ocupado = false
		queue_redraw()
