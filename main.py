import servidor
import usuario
import info_estudiantes
import info_proyecto
import time
import random
import subprocess
import sys
import os

def mostrar_menu_principal():
    """Menú interactivo unificado para todas las herramientas del proyecto."""
    print("==================================================")
    print(f"Proyecto: {info_proyecto.tema}")
    print(f"Estudiantes: {info_estudiantes.nombres_estudiantes()}")
    print(f"Descripción: {info_proyecto.descripcion}")
    print("==================================================\n")
    
    while True:
        print("\n" + "="*50)
        print("    SISTEMA DE GESTIÓN DE DESCARGAS Y JUEGO WS")
        print("="*50)
        print("1. Iniciar Simulación Local (Proyecto Original SO)")
        print("2. Iniciar Servidor Multijugador (Juego Godot)")
        print("3. Ejecutar Analizador de Bitácora (Verificar Mutex)")
        print("4. Salir")
        print("-" * 50)
        
        opcion = input("Selecciona una opción (1-4): ").strip()
        
        if opcion == "1":
            configurar_y_ejecutar_simulacion()
        elif opcion == "2":
            iniciar_servidor_juego()
        elif opcion == "3":
            analizar_bitacora()
        elif opcion == "4":
            print("\n[*] Cerrando el sistema principal. ¡Hasta luego!\n")
            break
        else:
            print("\n[!] Opción no válida. Intenta de nuevo.\n")

def configurar_y_ejecutar_simulacion():
    """Permite al usuario definir los parámetros antes de lanzar los hilos."""
    print("\n--- CONFIGURACIÓN DE LA SIMULACIÓN LOCAL ---")
    print("(Presiona Enter para usar los valores por defecto)")
    
    try:
        cap = input("Capacidad máxima de nodos [Defecto: 3]: ").strip()
        capacidad = int(cap) if cap else 3
        
        ab = input("Ancho de banda total (MB) [Defecto: 100]: ").strip()
        ancho_banda = int(ab) if ab else 100
        
        num_user = input("Cantidad de usuarios (hilos) a simular [Defecto: 10]: ").strip()
        num_usuarios = int(num_user) if num_user else 10
    except ValueError:
        print("\n[!] Error: Valores inválidos. Usando configuración por defecto...")
        capacidad, ancho_banda, num_usuarios = 3, 100, 10

    print("\n[*] Lanzando simulación...")
    ejecutar_simulacion(capacidad, ancho_banda, num_usuarios)

def ejecutar_simulacion(capacidad, ancho_banda, num_usuarios):
    """Ejecuta la simulación de SO clásica con los parámetros ingresados."""
    
    print(f"[+] Servidor instanciado: Servidor_UEES_Cloud (Capacidad: {capacidad}, Ancho: {ancho_banda}MB)")
    srv = servidor.Servidor("Servidor_UEES_Cloud", capacidad_maxima=capacidad, ancho_banda_total=ancho_banda)
    
    print(f"[+] Creando {num_usuarios} usuarios con diferentes tipos de archivo...\n")
    solicitudes = [usuario.UsuarioDescarga(i, srv) for i in range(1, num_usuarios + 1)]
    
    print("[*] Iniciando hilos en oleadas escalonadas (simulando usuarios reales)...\n")
    print("=" * 70)
    
    # Adaptamos el tamaño de la oleada a la capacidad del servidor para forzar el Mutex
    oleada_tamaño = capacidad + 1 
    tiempo_entre_oleadas = 1.0 
    
    for oleada_num in range(0, len(solicitudes), oleada_tamaño):
        oleada = solicitudes[oleada_num:oleada_num + oleada_tamaño]
        print(f"\n>>> OLEADA {oleada_num // oleada_tamaño + 1}: Iniciando {len(oleada)} usuarios...")
        
        for s in oleada:
            s.start()
            time.sleep(random.uniform(0.1, 0.3))
        
        if oleada_num + oleada_tamaño < len(solicitudes):
            time.sleep(tiempo_entre_oleadas)
    
    print("\n[*] Esperando a que todos los hilos completen sus descargas...\n")
    for s in solicitudes:
        s.join()

    print("=" * 70)
    srv.generar_reporte_estado()
    print("\n[✓] Simulación completada. Revisa bitacora.log para ver el registro detallado.")

def iniciar_servidor_juego():
    """Delega la ejecución al script de WebSockets usando subprocess."""
    print("\n" + "="*60)
    print("🚀 PREPARANDO ENTORNO MULTIJUGADOR (WEBSOCKETS)")
    print("="*60)
    
    ruta_script = os.path.join("juego-servidor", "main_ws.py")
    
    if not os.path.exists(ruta_script):
        print(f"\n[ERROR] No se encontró el archivo: {ruta_script}")
        print("Asegúrate de haber creado la carpeta 'juego-servidor' con su código.")
        return

    print("[*] Levantando proceso del servidor WebSockets...")
    print("[!] Para detener el servidor y volver a este menú, presiona CTRL+C.")
    print("-" * 60)
    
    try:
        # Ejecuta el script asíncrono como un proceso seguro e independiente
        subprocess.run([sys.executable, ruta_script])
    except KeyboardInterrupt:
        print("\n\n[*] Servidor de juego detenido por el usuario.")
    except Exception as e:
        print(f"\n[ERROR] Ocurrió un problema inesperado: {e}")
    
    print("[*] Volviendo al menú principal...")

def analizar_bitacora():
    """Ejecuta el script analizador como un subproceso visual."""
    print("\n[*] Iniciando Analizador de Exclusión Mutua...")
    
    if not os.path.exists("analizador_bitacora.py"):
        print("[ERROR] No se encontró 'analizador_bitacora.py' en la raíz.")
        return
        
    try:
        subprocess.run([sys.executable, "analizador_bitacora.py"])
        input("\nPresiona ENTER para volver al menú...")
    except Exception as e:
        print(f"[ERROR] Falló la ejecución del analizador: {e}")

if __name__ == "__main__":
    mostrar_menu_principal()