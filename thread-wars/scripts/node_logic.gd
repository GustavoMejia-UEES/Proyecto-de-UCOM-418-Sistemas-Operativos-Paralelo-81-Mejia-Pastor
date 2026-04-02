extends Area2D

@export var id_nodo: String = "1"
@onready var sprite = $Sprite2D
@onready var barra_progreso = $ProgressBar
@onready var icono_ataque = $IconoAtaque # NUEVO NODO

var estado_actual = "LIBRE"

func _ready():
	if barra_progreso: barra_progreso.hide()
	if icono_ataque: icono_ataque.hide()

func _process(_delta):
	if not NetworkManager.estado_mundo.has("nodos"): return
	
	var diccionario_nodos = NetworkManager.estado_mundo["nodos"]
	
	if diccionario_nodos.has(id_nodo):
		var mis_datos = diccionario_nodos[id_nodo]
		
		# Mostrar Barra e Ícono si está siendo atacado
		if mis_datos["estado"] == "ATACADO" or mis_datos["estado"] == "CORRUPTO":
			if barra_progreso:
				barra_progreso.show()
				barra_progreso.max_value = float(mis_datos.get("total", 1))
				barra_progreso.value = float(mis_datos.get("progreso", 0))
				barra_progreso.modulate = Color.RED if mis_datos["estado"] == "CORRUPTO" else Color.YELLOW
			
			# Mostrar el ícono del archivo atacante
			if icono_ataque and mis_datos.has("tipo_ataque"):
				var tipo = str(mis_datos["tipo_ataque"]).replace("PARCHE_", "")
				var ruta = "res://assets/icons/" + tipo + ".png"
				if ResourceLoader.exists(ruta):
					icono_ataque.texture = load(ruta)
					icono_ataque.show()
		else:
			if barra_progreso: barra_progreso.hide()
			if icono_ataque: icono_ataque.hide()
		
		if mis_datos["estado"] != estado_actual:
			estado_actual = mis_datos["estado"]
			actualizar_visuales()

func actualizar_visuales():
	if estado_actual == "LIBRE": sprite.modulate = Color.WHITE 
	elif estado_actual == "ATACADO": sprite.modulate = Color.YELLOW
	elif estado_actual == "CORRUPTO": sprite.modulate = Color.RED
