extends Area2D

# ==========================================
# IDENTIDAD
# ==========================================
var id_nodo: int = 0

# ==========================================
# ESTADO (actualizado desde Python)
# ==========================================
var estado: String      = "LIBRE"   # LIBRE | ATACADO | CORRUPTO
var progreso: int       = 0
var total: int          = 0
var hp_nodo: int        = 100
var tipo_ataque: String = ""        # TEXTO | IMAGEN | VIDEO — quién lo está atacando

# Colores por tipo de archivo atacante
const COLORES_TIPO: Dictionary = {
	"TEXTO":  Color(0.2,  0.5,  1.0,  1.0),
	"IMAGEN": Color(1.0,  0.55, 0.1,  1.0),
	"VIDEO":  Color(0.85, 0.05, 0.15, 1.0),
}

# Animación de pulso
var _tiempo: float = 0.0

# Label dentro del nodo
var _label: Label = null

# Jugador local encima (para hints)
var _jugador_encima: Node = null

func _ready():
	collision_mask = 3

	var shape_node := CollisionShape2D.new()
	var shape_res  := RectangleShape2D.new()
	shape_res.size = Vector2(60, 60)
	shape_node.shape = shape_res
	add_child(shape_node)

	_label = Label.new()
	_label.name = "LabelId"
	_label.text = "PC %d" % id_nodo
	_label.position = Vector2(-28, 34)
	_label.add_theme_font_size_override("font_size", 12)
	add_child(_label)

	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)

# ==========================================
# SINCRONIZACIÓN CON PYTHON
# ==========================================
func _process(delta: float):
	_tiempo += delta

	if not NetworkManager.estado_mundo.has("nodos"):
		return

	var nodo_data = NetworkManager.estado_mundo["nodos"].get(str(id_nodo), "LIBRE")

	var nuevo_estado: String      = "LIBRE"
	var nuevo_progreso: int       = 0
	var nuevo_total: int          = 0
	var nuevo_hp: int             = 100
	var nuevo_tipo: String        = ""

	if nodo_data is String:
		nuevo_estado = nodo_data
	elif nodo_data is Dictionary:
		nuevo_estado   = nodo_data.get("estado",      "LIBRE")
		nuevo_progreso = nodo_data.get("progreso",    0)
		nuevo_total    = nodo_data.get("total",       0)
		nuevo_hp       = nodo_data.get("hp",          100)
		nuevo_tipo     = nodo_data.get("tipo_ataque", "")

	if nuevo_estado != estado or nuevo_progreso != progreso or nuevo_hp != hp_nodo or nuevo_tipo != tipo_ataque:
		estado      = nuevo_estado
		progreso    = nuevo_progreso
		total       = nuevo_total
		hp_nodo     = nuevo_hp
		tipo_ataque = nuevo_tipo
		if is_instance_valid(_label):
			_label.text = "PC %d" % id_nodo

	queue_redraw()

# ==========================================
# VISUAL
# ==========================================
func _draw():
	var pulso_alfa: float = 1.0
	var color_base: Color
	var color_borde: Color

	match estado:
		"LIBRE":
			color_base  = Color(0.05, 0.75, 0.2, 0.88)
			color_borde = Color(0.0,  1.0,  0.4, 1.0)
		"ATACADO":
			pulso_alfa  = sin(_tiempo * 3.0) * 0.25 + 0.75
			color_base  = Color(0.9, 0.7, 0.0, pulso_alfa)
			color_borde = Color(1.0, 0.9, 0.1, 1.0)
		"CORRUPTO":
			pulso_alfa  = sin(_tiempo * 8.0) * 0.3 + 0.7
			color_base  = Color(0.85, 0.05, 0.05, pulso_alfa)
			color_borde = Color(1.0,  0.2,  0.2,  1.0)
		_:
			color_base  = Color(0.4, 0.4, 0.4, 0.7)
			color_borde = Color.WHITE

	# Cuerpo del nodo
	draw_rect(Rect2(-30, -30, 60, 60), color_base)
	draw_rect(Rect2(-30, -30, 60, 60), color_borde, false, 2.0)

	# Ícono "PC" en el centro
	draw_string(ThemeDB.fallback_font, Vector2(-12, 6), "PC", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)

	# Indicador del tipo de archivo que lo ataca (esquina superior derecha)
	if tipo_ataque != "" and estado in ["ATACADO", "CORRUPTO"]:
		var color_tipo: Color = COLORES_TIPO.get(tipo_ataque, Color.WHITE)
		draw_rect(Rect2(16, -30, 14, 14), color_tipo)
		var letra: String = tipo_ataque.left(1)   # T / I / V
		draw_string(ThemeDB.fallback_font, Vector2(18, -18), letra, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color.WHITE)

	# Hint del jugador local encima
	if _jugador_encima != null and is_instance_valid(_jugador_encima):
		var rol_j: String       = _jugador_encima.get("rol")                 if _jugador_encima.get("rol")                 != null else ""
		var archivo: String     = _jugador_encima.get("archivo_equipado")     if _jugador_encima.get("archivo_equipado")     != null else ""
		var herramienta: String = _jugador_encima.get("herramienta_equipada") if _jugador_encima.get("herramienta_equipada") != null else ""

		var hint: String      = ""
		var hint_color: Color = Color.WHITE

		if rol_j == "CLIENTE":
			if estado == "CORRUPTO":
				hint       = "YA CORRUPTO"
				hint_color = Color(0.8, 0.3, 0.3)
			else:
				hint       = "[E] %s" % (archivo if archivo != "" else "sin archivo")
				hint_color = Color(1.0, 0.9, 0.2)
				# Advertir si tipo equivocado
				if estado == "ATACADO" and archivo != "" and archivo != tipo_ataque:
					hint       = "✗ Nodo: %s" % tipo_ataque
					hint_color = Color(1.0, 0.3, 0.3)
		elif rol_j == "ADMIN":
			if estado in ["ATACADO", "CORRUPTO"]:
				if herramienta != "":
					hint       = "[E] +%s" % herramienta
					hint_color = Color(0.3, 1.0, 0.6)
				else:
					hint       = "[E] REPARAR"
					hint_color = Color(0.4, 0.9, 1.0)
			else:
				hint       = "PC LIMPIA"
				hint_color = Color(0.4, 1.0, 0.4)

		if hint != "":
			draw_rect(Rect2(-34, -52, 68, 18), Color(0.0, 0.0, 0.0, 0.8))
			draw_string(ThemeDB.fallback_font, Vector2(-30, -38), hint, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, hint_color)

	# Barra de progreso de ataque
	if total > 0 and progreso > 0:
		var ratio: float = clamp(float(progreso) / float(total), 0.0, 1.0)
		var color_barra: Color = COLORES_TIPO.get(tipo_ataque, Color(1.0, 0.4, 0.0))
		draw_rect(Rect2(-30, 32, 60, 6), Color(0.1, 0.1, 0.1, 0.9))
		draw_rect(Rect2(-30, 32, 60.0 * ratio, 6), color_barra)
		# Texto de progreso
		draw_string(ThemeDB.fallback_font, Vector2(-30, 30), "%d/%d" % [progreso, total], HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color.WHITE)

	# Barra de HP
	var hp_ratio: float = clamp(float(hp_nodo) / 100.0, 0.0, 1.0)
	var hp_color: Color
	if hp_ratio > 0.6:
		hp_color = Color(0.1, 0.9, 0.1)
	elif hp_ratio > 0.3:
		hp_color = Color(1.0, 0.8, 0.0)
	else:
		hp_color = Color(0.9, 0.1, 0.1)
	draw_rect(Rect2(-30, 40, 60, 5), Color(0.05, 0.05, 0.05, 0.9))
	draw_rect(Rect2(-30, 40, 60.0 * hp_ratio, 5), hp_color)

# ==========================================
# DETECCIÓN
# ==========================================
func _on_body_entered(body: Node2D):
	if body.get("es_local") == true:
		body.nodo_actual = self
		_jugador_encima = body
		queue_redraw()

func _on_body_exited(body: Node2D):
	if body.get("nodo_actual") == self:
		body.nodo_actual = null
		_jugador_encima = null
		queue_redraw()
