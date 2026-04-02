extends CanvasLayer

@onready var label_timer = $Topbar/LabelTimer
@onready var progress_hp = $Topbar/ProgressBar_HP

@onready var panel_hacker = $Panel_Hacker
@onready var label_banda = $Panel_Hacker/Label_Banda
@onready var progress_banda = $Panel_Hacker/ProgressBar_Banda

@onready var panel_admin = $Panel_Admin
@onready var label_mutex = $Panel_Admin/Label_Mutex
@onready var consola_logs = $Panel_Admin/Consola_Logs

@onready var overlay_game_over = $OverlayGameOver
@onready var label_titulo = $OverlayGameOver/Label_Titulo
@onready var label_subtitulo = $OverlayGameOver/Label_Subtitulo
@onready var btn_volver = $OverlayGameOver/BtnVolverLobby

func _ready():
	overlay_game_over.hide()
	panel_hacker.hide()
	panel_admin.hide()
	
	if btn_volver:
		btn_volver.pressed.connect(_on_btn_volver_pressed)

func actualizar_hud(estado: Dictionary, mi_rol: String):
	var fase = estado.get("fase", "LOBBY")
	
	# FIX: Hacemos que sea siempre visible si estamos llamando a actualizar
	self.visible = true

	# 1. Mostrar/Ocultar paneles inferiores
	if mi_rol == "CLIENTE":
		panel_hacker.show()
		panel_admin.hide()
	elif mi_rol == "ADMIN":
		panel_admin.show()
		panel_hacker.hide()

	# 2. Actualizar la Vida
	if estado.has("vida_servidor"):
		progress_hp.value = float(estado["vida_servidor"])

	# 3. Actualizar el Reloj
	if estado.has("tiempo_restante"):
		var tiempo = int(estado["tiempo_restante"])
		var mins = int(tiempo / 60.0)
		var segs = int(tiempo % 60)
		label_timer.text = "%02d:%02d" % [mins, segs]
		if tiempo <= 60:
			label_timer.modulate = Color(1.0, 0.2, 0.2)
		else:
			label_timer.modulate = Color.WHITE

	# 4. Actualizar Panel Hacker
	if mi_rol == "CLIENTE" and estado.has("banda_consumida"):
		var banda = float(estado["banda_consumida"])
		progress_banda.max_value = 500.0 
		progress_banda.value = banda
		label_banda.text = "Banda Consumida: %d/500" % int(banda)

	# 5. Actualizar Panel Admin
	if mi_rol == "ADMIN":
		var mutex_calientes = estado.get("mutex_calientes", [])
		label_mutex.visible = (mutex_calientes.size() > 0)
		
		var logs = estado.get("consola_en_vivo", [])
		if consola_logs is RichTextLabel or consola_logs is Label:
			var texto_log = ""
			for linea in logs:
				texto_log += linea + "\n"
			consola_logs.text = texto_log

	# 6. Lógica de Fin de Partida
	var partida_activa = estado.get("partida_activa", true)
	if not partida_activa and (fase == "JUGANDO" or fase == "FINALIZADA"):
		overlay_game_over.show()
		var resultado = str(estado.get("resultado_partida", ""))
		
		if resultado == "HACKERS":
			label_titulo.text = "¡HACKERS GANAN!"
			label_titulo.modulate = Color(1.0, 0.2, 0.2)
			label_subtitulo.text = "El servidor ha sido comprometido por completo."
		else:
			label_titulo.text = "¡DEFENSORES GANAN!"
			label_titulo.modulate = Color(0.2, 1.0, 0.2)
			label_subtitulo.text = "El servidor sobrevivió al ataque."

func _on_btn_volver_pressed():
	NetworkManager.socket.close()
	get_tree().change_scene_to_file("res://scenes/Menu.tscn")
