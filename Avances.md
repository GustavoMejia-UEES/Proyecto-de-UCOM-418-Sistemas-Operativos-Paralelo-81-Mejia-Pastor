
# Registro de Avances - Proyecto Sistemas Operativos

## Avance 4: Servidor de Descargas

**Estudiante:** Juan Fernando Pastor Huaman

### Análisis Técnico:

* **Recursos Compartidos**:
* **Básico (`int` / `float`)**: `conexiones_activas` y `bytes_transferidos_totales`. El hilo accede a estos para validar cupo antes de iniciar y reportar el peso del archivo al finalizar.


* **Complejo (`list`)**: `historial_trafico`. Estructura donde el hilo añade el log de éxito de la descarga.




* **Entidad**: Clase `UsuarioDescarga`. Hereda de `threading.Thread` y es la encargada de consumir los recursos del servidor de forma asíncrona.


* 
**Sección Crítica**: Definida como el bloque de código que solicita el permiso, modifica el contador de conexiones y registra la salida en el historial. El riesgo de no protegerla con el **Mutex** del servidor es la inconsistencia de datos y la sobreventa de capacidad del sistema.



### Intervención Individual:

* 
**Desarrollo**: Implementación de la clase `UsuarioDescarga` y la lógica de ejecución en el método `run()`.


* 
**Sincronización**: Aplicación de los métodos `acquire()` y `release()` sobre el Mutex de la infraestructura para garantizar la exclusión mutua.


* **Integración**: Actualización y configuración del archivo `main.py` para instanciar los objetos y ejecutar la simulación de concurrencia.
* 
**Versionamiento**: Creación y gestión de la rama `feature-clase-usuario` y unión final a la rama principal mediante merge.

