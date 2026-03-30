import servidor
import usuario
import bitacora
import info_estudiantes
import info_proyecto
import time
import random

def ejecutar_simulacion():
    # Limpiamos el log manualmente al iniciar
    bitacora.limpiar()
    
    print("--- INICIANDO SIMULACIÓN DE DESCARGAS ---")
    srv = servidor.Servidor("Servidor_UEES_Cloud", capacidad_maxima=3, ancho_banda_total=100)
    
    # Instanciamos 7 hilos para forzar el límite
    solicitudes = [usuario.UsuarioDescarga(i, srv) for i in range(1, 8)]

    for s in solicitudes:
        s.start()

    for s in solicitudes:
        s.join()

    srv.generar_reporte_estado()

def main():
    print("==================================================")
    print(f"Proyecto: {info_proyecto.tema}")
    print(f"Estudiantes: {info_estudiantes.nombres_estudiantes()}")
    print("==================================================")
    
    # MENÚ DEL SISTEMA
    while True:
        print("--- MENÚ DEL SISTEMA ---")
        print("1. Ejecutar simulación concurrente")
        print("2. Salir")
        opcion = input("Seleccione una opción (1 o 2): ")

        if opcion == '1':
            ejecutar_simulacion()
        elif opcion == '2':
            print("Cerrando el sistema... ¡Hasta luego!")
            break
        else:
            print("Opción no válida. Intente de nuevo.")
    
if __name__ == "__main__":
    main()