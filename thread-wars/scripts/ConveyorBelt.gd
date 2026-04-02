extends Area2D

const ESCENA_FILE_ITEM := preload("res://scenes/World/FileItem.tscn")

@export var zona: String = "HACKER"
var _items_instanciados: Dictionary = {}

func _ready():
	collision_mask = 3

func _process(delta: float):
	var clave: String = "cinta_hacker" if zona == "HACKER" else "cinta_admin"
	var items_red: Array = NetworkManager.estado_mundo.get(clave, [])
	_sincronizar_items(items_red)
	
	# MAGIA VISUAL: Movimiento solo para la cinta de los Hackers
	if zona == "HACKER":
		for id in _items_instanciados:
			var fi = _items_instanciados[id]
			fi.position.x += 250.0 * delta # Avance rápido
			
			# Efecto de cinta infinita visual
			if fi.position.x > 550:
				fi.position.x = -550

func _sincronizar_items(items_red: Array):
	var ids_red: Array = []
	for i in items_red:
		if i.get("id", "") != "": ids_red.append(i.get("id"))

	var ids_a_borrar: Array = []
	for id in _items_instanciados:
		if not ids_red.has(id):
			_items_instanciados[id].queue_free()
			ids_a_borrar.append(id)
	
	for id in ids_a_borrar: 
		_items_instanciados.erase(id)

	var idx = 0 # Contador para ordenar a los Admins
	for item_data in items_red:
		var id: String   = item_data.get("id", "")
		var tipo: String = item_data.get("tipo", "TEXTO")

		if id != "" and not _items_instanciados.has(id):
			var fi := ESCENA_FILE_ITEM.instantiate()
			fi.set("tipo", tipo)
			fi.set("id_item", id)
			
			if zona == "HACKER":
				# Nacen a la izquierda y avanzan
				fi.position = Vector2(-500 - (randf() * 50), 0)
			else:
				# ADMIN: 3 Posiciones FIJAS (-200, 0, 200)
				fi.position = Vector2(-200 + (idx * 200), 0)
				
			add_child(fi)
			_items_instanciados[id] = fi
			
		elif _items_instanciados.has(id) and zona == "ADMIN":
			# Obligamos a los items de Admin a QUEDARSE QUIETOS siempre
			_items_instanciados[id].position = Vector2(-200 + (idx * 200), 0)
			
		idx += 1
