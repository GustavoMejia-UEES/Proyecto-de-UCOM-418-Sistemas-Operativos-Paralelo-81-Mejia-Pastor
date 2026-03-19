import servidor
import usuario
import info_estudiantes
import info_proyecto

def mostrar_menu_principal():
    print("==================================================")
    print(f"Proyecto: {info_proyecto.tema}")
    print(f"Estudiantes: {info_estudiantes.nombres_estudiantes()}")
    print(f"Descripción: {info_proyecto.descripcion}")
    print("==================================================")
    
    while True:
        print("--- SISTEMA DE GESTIÓN DE DESCARGAS CONCURRENTES ---")
        print("1. Iniciar simulación de descargas (6 usuarios)")
        print("2. Salir")
        print("" + "-" * 50)
        
        opcion = input("Selecciona una opción (1-2): ").strip()
        
        if opcion == "1":
            print("[*] Lanzando simulación...")
            ejecutar_simulacion()
            break
        elif opcion == "2":
            print("[*] Saliendo del programa.")
            break
        else:
            print("[!] Opción no válida. Intenta de nuevo.")

def ejecutar_simulacion():
    # 1. Instanciación del Servidor
    print("[+] Servidor instanciado: Servidor_UEES_Cloud (Capacidad: 3 usuarios)")
    srv = servidor.Servidor("Servidor_UEES_Cloud", capacidad_maxima=3, ancho_banda_total=100)
    
    # 2. Instanciación del grupo de hilos (6 solicitudes para probar los reintentos)
    print("[+] Creando 6 usuarios que solicitarán acceso al servidor...")
    solicitudes = [usuario.UsuarioDescarga(i, srv) for i in range(1, 7)]

    # 3. Lanzamiento de Hilos
    print("[*] Iniciando hilos (simulación en concurrencia)...")
    print("=" * 60)
    for s in solicitudes:
        s.start()

    # 4. Sincronización del Hilo Principal (esperar a que terminen todos)
    for s in solicitudes:
        s.join()

    # 5. Reporte Final
    print("=" * 60)
    srv.generar_reporte_estado()
    print("[✓] Simulación completada. Revisa bitacora.log para ver el registro detallado.")

def main():
    mostrar_menu_principal()

if __name__ == "__main__":
    main()