import servidor
import usuario
import info_estudiantes
import info_proyecto
import time
import random

def mostrar_menu_principal():
    """Menú interactivo para iniciar la simulación."""
    print("==================================================")
    print(f"Proyecto: {info_proyecto.tema}")
    print(f"Estudiantes: {info_estudiantes.nombres_estudiantes()}")
    print(f"Descripción: {info_proyecto.descripcion}")
    print("==================================================\n")
    
    while True:
        print("\n--- SISTEMA DE GESTIÓN DE DESCARGAS CONCURRENTES ---\n")
        print("1. Iniciar simulación de descargas (10 usuarios con oleadas)")
        print("2. Salir")
        print("\n" + "-" * 50)
        
        opcion = input("Selecciona una opción (1-2): ").strip()
        
        if opcion == "1":
            print("\n[*] Lanzando simulación...")
            ejecutar_simulacion()
            break
        elif opcion == "2":
            print("\n[*] Saliendo del programa.\n")
            break
        else:
            print("\n[!] Opción no válida. Intenta de nuevo.\n")

def ejecutar_simulacion():
    """
    Ejecuta la simulación de descargas concurrentes con oleadas.
    
    En lugar de lanzar todos los hilos de golpe, los lanzamos en "oleadas"
    escalonadas para simular usuarios llegando en diferentes momentos.
    Esto pone a prueba el Mutex bajo condiciones realistas de estrés.
    """
    
    # 1. Instanciación del Servidor
    print("[+] Servidor instanciado: Servidor_UEES_Cloud (Capacidad: 3 usuarios, Ancho: 100MB)")
    print("[+] Puertos disponibles: 3 (Nodo 1, Nodo 2, Nodo 3)\n")
    srv = servidor.Servidor("Servidor_UEES_Cloud", capacidad_maxima=3, ancho_banda_total=100)
    
    # 2. Crear 10 usuarios
    num_usuarios = 10
    print(f"[+] Creando {num_usuarios} usuarios con diferentes tipos de archivo...\n")
    solicitudes = [usuario.UsuarioDescarga(i, srv) for i in range(1, num_usuarios + 1)]
    
    # 3. Lanzamiento de Hilos en OLEADAS (no todos a la vez)
    print("[*] Iniciando hilos en oleadas escalonadas (simulando usuarios reales)...\n")
    print("=" * 70)
    
    oleada_tamaño = 3  # Lanzar 3 usuarios cada vez
    tiempo_entre_oleadas = 1.0  # Esperar 1 segundo entre oleadas
    
    for oleada_num in range(0, len(solicitudes), oleada_tamaño):
        oleada = solicitudes[oleada_num:oleada_num + oleada_tamaño]
        
        print(f"\n>>> OLEADA {oleada_num // oleada_tamaño + 1}: Iniciando {len(oleada)} usuarios...")
        
        for s in oleada:
            s.start()
            # Pequeño delay entre el inicio de cada usuario en la oleada
            time.sleep(random.uniform(0.1, 0.3))
        
        # Esperar antes de lanzar la siguiente oleada (si hay más)
        if oleada_num + oleada_tamaño < len(solicitudes):
            time.sleep(tiempo_entre_oleadas)
    
    # 4. Sincronización del Hilo Principal (esperar a que terminen todos)
    print("\n[*] Esperando a que todos los hilos completen sus descargas...\n")
    for s in solicitudes:
        s.join()

    # 5. Reporte Final
    print("=" * 70)
    srv.generar_reporte_estado()
    print("\n[✓] Simulación completada. Revisa bitacora.log para ver el registro detallado.")

def main():
    mostrar_menu_principal()

if __name__ == "__main__":
    main()

