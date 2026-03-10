
# Registro de Avances - Proyecto Sistemas Operativos

## Avance 4: Servidor de Descargas

**Estudiante:** Juan Fernando Pastor Huaman

### Análisis Técnico:

* **Recursos Compartidos**:
* **Básico (`int` / `float`)**: `conexiones_activas` y `bytes_transferidos_totales`. El hilo accede a estos para validar cupo antes de iniciar y reportar el peso del archivo al finalizar
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

**Estudiante:** Gustavo Jose Mejia Riofrio

### Análisis Técnico:

- **Recursos Compartidos**:
- **Básico (`int` / `float`)**: `conexiones_activas` y `bytes_transferidos_totales`. Son compartidos porque el servidor controla el límite de usuarios y el tráfico en tiempo real.

- **Complejo (`list`)**: `historial_trafico`. Es donde se registran las metadata de cada descarga al finalizar.

- **Entidad**: Clase `Servidor`. Administra la capacidad y el Mutex.

- **Sección Crítica**: Ocurre al validar el cupo disponible y actualizar los contadores. Sin protección (Mutex), el servidor podría aceptar más descargas de su capacidad real, causando una **condición de carrera** y el colapso del sistema.

### Intervención Individual:

- **Arquitectura**: Implementación de la clase `Servidor` con atributos de control (`capacidad_maxima`, `ancho_banda`).

- **Sincronización**: Definición del **Mutex** (`threading.Lock`) para asegurar la exclusión mutua en los recursos compartidos.

- **Auditoría**: Creación del método `generar_reporte_estado()` para monitorear la carga y logs del sistema.
- **Versionamiento**: Creación de la rama `gustavo-infraestructura` y estructuración inicial del repositorio.
