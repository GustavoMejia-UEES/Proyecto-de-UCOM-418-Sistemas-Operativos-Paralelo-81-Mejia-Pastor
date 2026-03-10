import servidor
import usuario
import info_estudiantes
import info_proyecto

def main():
    print(f"Estudiantes: {', '.join(info_estudiantes.lista)}")
    print(f"Proyecto: {info_proyecto.tema}")
    print(f"Descripcion: {info_proyecto.descripcion}")
    print("--- INICIANDO SISTEMA DE GESTIÓN DE DESCARGAS ---")
    
    # 1. Instanciación del Servidor 
    srv = servidor.Servidor("Servidor_UEES_Cloud", capacidad_maxima=3, ancho_banda_total=100)
    
    # 2. Instanciación de Hilos de Usuario 
    solicitudes = [usuario.UsuarioDescarga(i, srv) for i in range(1, 7)]

    # 3. Ejecución
    for s in solicitudes:
        s.start()

    for s in solicitudes:
        s.join()

    # 4. Reporte Final
    srv.generar_reporte_estado()
    
if __name__ == "__main__":
    main()