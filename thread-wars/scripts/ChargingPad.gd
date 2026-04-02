extends Area2D

@export var es_pad: bool = true  # <--- ESTA ES LA VARIABLE MÁGICA
@export var zona: String = "HACKER"
@onready var sprite = $Sprite2D

# (El resto de tu código de opacidad queda igualito)
func _process(delta: float):
	var alguien_cargando = false
	for body in get_overlapping_areas():
		if body.get("pad_actual") == self:
			alguien_cargando = true
			break
			
	if alguien_cargando:
		sprite.modulate.a = 1.0 
	else:
		sprite.modulate.a = 0.4
