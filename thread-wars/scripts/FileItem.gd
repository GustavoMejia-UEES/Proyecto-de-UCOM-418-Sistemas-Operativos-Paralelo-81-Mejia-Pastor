extends Area2D

var id_item: String = ""
var tipo: String = "TEXTO" 

@onready var sprite = $Icono

func _ready():
	# Magia: Reemplaza "PARCHE_TEXTO" por "TEXTO" solo para buscar el archivo
	var nombre_png = tipo.replace("PARCHE_", "")
	var ruta_imagen = "res://assets/icons/" + nombre_png + ".png"
	
	if ResourceLoader.exists(ruta_imagen):
		sprite.texture = load(ruta_imagen)
		
		# Si es un ítem de Admin, lo teñimos de celeste para diferenciarlo de los virus
		if "PARCHE" in tipo:
			sprite.modulate = Color(0.3, 0.8, 1.0) 
	else:
		print("Falta el sprite: ", ruta_imagen)
