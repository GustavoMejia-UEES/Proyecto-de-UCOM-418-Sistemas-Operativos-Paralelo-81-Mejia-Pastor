# Registro de Avances - Proyecto Sistemas Operativos

## Avance 4: Servidor de Descargas

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
