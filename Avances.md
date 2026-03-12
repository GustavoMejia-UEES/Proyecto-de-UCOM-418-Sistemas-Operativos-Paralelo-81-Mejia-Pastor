# Registro de Avances - Proyecto Sistemas Operativos

## Avance 4 y 5: Servidor de Descargas y Sincronización Avanzada

### Contexto del proyecto

Servidor de descargas: plataforma que gestiona múltiples solicitudes desde un servidor con capacidad limitada, administrando conexiones activas y el tráfico total generado.

---

## 1) Recurso compartido identificado

### Tipo básico

- `conexiones_activas` (`int`): contador global de cupos ocupados en el servidor.
- `bytes_transferidos_totales` (`float`): acumulador global del tráfico de descargas.

**Por qué son compartidos:**
Son variables únicas del objeto `Servidor` que todos los hilos `UsuarioDescarga` necesitan leer y modificar indirectamente durante su ejecución para reservar cupo y registrar su consumo.

### Tipo complejo

- `historial_trafico` (`list`): bitácora en memoria compartida.
- `servidor-trafico.log` (`Archivo físico`): registro de auditoría en disco.

**Por qué es compartido:**
Todos los hilos reportan el resultado de su solicitud al servidor, el cual escribe sobre la misma estructura de memoria y el mismo archivo físico para mantener un historial unificado del sistema.

---

## 2) Entidades que acceden al recurso compartido

- **Clase `Servidor` (`servidor.py`)**
- **Atributos principales:** `nombre_servidor`, `capacidad_maxima`, `ancho_banda_total`, `conexiones_activas`, `bytes_transferidos_totales`, `historial_trafico`, `mutex`.
- **Rol:** Actuar como monitor central. Encapsula la lógica de sincronización, administrando el acceso a sus recursos mediante métodos seguros y proveyendo el reporte final.

- **Clase `UsuarioDescarga` (`usuario.py`)**
- **Atributos principales:** `id_solicitud`, `servidor`, `tamano_archivo`, `max_intentos`.
- **Rol:** Entidad concurrente que hereda de `threading.Thread`. Representa cada solicitud que negocia el acceso al servidor, gestiona sus propios reintentos en caso de rechazo y simula el tiempo de descarga.

---

## 3) Reflexión sobre la sección crítica (sin código)

La sección crítica ocurre en dos momentos exactos gestionados por el servidor:

1. **Entrada:** Cuando se valida si hay cupo disponible y se incrementa `conexiones_activas`.
2. **Salida:** Cuando se decrementa `conexiones_activas`, se suma el tráfico a `bytes_transferidos_totales` y se escribe en el historial/log.

**Riesgo de no protegerla:**
Sin exclusión mutua, ocurriría una condición de carrera (_race condition_). El resultado sería inconsistente: el servidor podría aceptar más usuarios que su capacidad física (sobrepasando el límite de 3), los cálculos de tráfico se sobrescribirían perdiendo datos, y el archivo `.log` quedaría corrupto o mezclado.

---

## 4) Desarrollo implementado (Evolución Avance 5)

- **Arquitectura de Hilos:** Se consolidó el uso de herencia de `threading.Thread` para dotar de estado y autonomía a cada usuario.
- **Encapsulamiento del Mutex:** El objeto `Servidor` ahora administra su propio `threading.Lock()` utilizando explícitamente `acquire()` y `release()` dentro de métodos específicos (`solicitar_conexion` y `registrar_salida`).
- **Sistema de Polling (Reintentos):** Los hilos de usuario ahora implementan un ciclo `while` para insistir en la conexión si el servidor los rechaza inicialmente, simulando clientes reales.
- **Cálculo de Ancho de Banda:** El tiempo de simulación (`sleep`) de cada hilo ya no es puramente aleatorio, sino que se calcula matemáticamente dividiendo el tamaño del archivo para el ancho de banda asignado.
- **Auditoría Física:** Implementación de escritura de logs en un archivo físico `.log`.

---

## 5) Distribución de actividades

### Estudiante: Juan Fernando Pastor Huaman

- Refactorización de `UsuarioDescarga` implementando el ciclo de vida del hilo (`run()`).
- Desarrollo del algoritmo de reintentos (Polling) ante servidor lleno.
- Implementación de la simulación de descarga por bloques basada en el ancho de banda.
- Orquestación del sistema concurrente (`start` y `join` masivo) en `main.py`.

### Estudiante: Gustavo Jose Mejia Riofrio

- Refactorización de la clase `Servidor` aplicando principios de encapsulamiento.
- Implementación de los métodos de control de acceso a la sección crítica usando `.acquire()` y `.release()`.
- Desarrollo de la escritura persistente en disco (`escribir_log`).
- Actualización de la generación de reportes de estado.

---

## 6) Versionamiento (Checklist para la entrega)

- [x] Versionado local por ramas individuales (`feature/servidor` y `feature/usuarios-orquestacion`).
- [x] Subida de ramas al repositorio remoto.
- [x] Merge de ambas ramas de trabajo hacia la rama `main`.
- [x] Obtención del SHA del último commit de integración.
