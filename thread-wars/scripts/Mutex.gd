extends Area2D

@export var id_mutex: int = 0 

@onready var sprite = $Sprite2D
var reproductor_audio: AudioStreamPlayer2D

var estaba_caliente: bool = false
var audio_ruta: String = "res://assets/audio/Mutex.mp3"

func _ready():
	collision_layer = 16 
	collision_mask = 0
	
	reproductor_audio = AudioStreamPlayer2D.new()
	add_child(reproductor_audio)
	
	var sonido_cargado = load(audio_ruta)
	if sonido_cargado:
		reproductor_audio.stream = sonido_cargado
		reproductor_audio.volume_db = 2.0 

func _process(_delta):
	var calientes: Array = []
	if NetworkManager.estado_mundo.has("mutex_calientes"):
		calientes = NetworkManager.estado_mundo["mutex_calientes"]
		
	# 🛡️ BLINDAJE: Verificamos convirtiendo todo a entero por si Python envía Strings
	var es_caliente: bool = false
	for m in calientes:
		if int(m) == id_mutex:
			es_caliente = true
			break
	
	if es_caliente:
		# VISUAL: Arcoíris
		var tiempo = Time.get_ticks_msec() / 600.0
		sprite.modulate = Color.from_hsv(wrapf(tiempo, 0.0, 1.0), 1.0, 1.0)
		
		# AUDIO Y LOG: Solo se ejecuta el primer frame que se enciende
		if not estaba_caliente:
			estaba_caliente = true
			print("[MUTEX] 🚨 El Mutex ", id_mutex, " se ha CALENTADO!")
			if reproductor_audio.stream:
				reproductor_audio.play()
	else:
		# APAGADO: Volvemos a la normalidad
		sprite.modulate = Color.WHITE
		if estaba_caliente:
			estaba_caliente = false
			print("[MUTEX] ✅ El Mutex ", id_mutex, " se ha ENFRIADO.")
			reproductor_audio.stop()
