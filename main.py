import servidor
import usuario
import info_estudiantes
import info_proyecto

def main():
    print("==================================================")
    print(f"Proyecto: {info_proyecto.tema}")
    print(f"Estudiantes: {info_estudiantes.nombres_estudiantes()}")
    print(f"Descripción: {info_proyecto.descripcion}")
    print("==================================================\n")
    print("--- INICIANDO SISTEMA DE GESTIÓN DE DESCARGAS ---\n")
    
    # 1. Instanciación del Servidor
    srv = servidor.Servidor("Servidor_UEES_Cloud", capacidad_maxima=3, ancho_banda_total=100)
    
    # 2. Instanciación del grupo de hilos (6 solicitudes para probar los reintentos)
    solicitudes = [usuario.UsuarioDescarga(i, srv) for i in range(1, 7)]

    # 3. Lanzamiento de Hilos
    for s in solicitudes:
        s.start()

    # 4. Sincronización del Hilo Principal
    for s in solicitudes:
        s.join()

    # 5. Reporte Final
    srv.generar_reporte_estado()
    
if __name__ == "__main__":
    main()