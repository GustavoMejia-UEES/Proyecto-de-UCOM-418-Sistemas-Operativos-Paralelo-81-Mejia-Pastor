# Proyecto UCOM 418: Servidor de Descargas 🖥️⬇️

## Información Académica

- **Materia:** UCOM 418 - Sistemas Operativos
- **Paralelo:** 81
- **Integrantes:**
  - Gustavo Jose Mejia Riofrio
  - Juan Fernando Pastor Huaman

---

## 📌 Explicación del Proyecto

El **Servidor de Descargas** es una plataforma concurrente que simula y gestiona múltiples solicitudes de descarga dirigidas a un servidor con capacidad limitada. El sistema administra de forma segura las conexiones activas, el control de aforo y el registro de auditoría del tráfico generado, garantizando que no existan condiciones de carrera (_race conditions_) al modificar los recursos compartidos.

---

## 🏗️ Arquitectura y Diseño de la Solución

El proyecto está diseñado bajo un modelo de concurrencia basado en la **Herencia de `threading.Thread`** y el encapsulamiento de recursos. La arquitectura se divide en tres componentes principales para asegurar alta cohesión y bajo acoplamiento:

### 1. Clase `Servidor` (Gestión de Recursos Compartidos)

Actúa como el monitor central del sistema. Posee una capacidad máxima de conexiones y controla el flujo de acceso.

- **Sincronización Lógica (Mutex Principal):** Para proteger la sección crítica (las variables `conexiones_activas` y `bytes_transferidos_totales`), el servidor instancia un candado lógico mediante `threading.Lock()`.
- **Control Explícito:** Los métodos `solicitar_conexion` y `registrar_salida` utilizan explícitamente `acquire()` y `release()` para bloquear el acceso a otros hilos mientras un usuario actualiza los contadores, previniendo la corrupción de datos y asegurando la liberación del candado en todos los caminos de ejecución para evitar _Deadlocks_.

### 2. Clase `UsuarioDescarga` (Entidad Concurrente)

Representa a los clientes. Hereda directamente de `threading.Thread`, lo que le permite tener un estado interno y comportamiento autónomo.

- **Sistema de Reintentos (Polling):** Si el servidor rechaza la conexión por aforo lleno, el hilo entra en estado de espera (`time.sleep`) y vuelve a intentar conectarse hasta un máximo de 3 veces.
- **Ejecución Asíncrona:** Una vez aceptada la solicitud, la simulación de descarga (latencia de red) se ejecuta estrictamente fuera del Mutex, permitiendo que otros hilos interactúen con el servidor mientras este usuario "descarga".

### 3. Módulo `Bitacora` (Sincronización de I/O)

Módulo independiente encargado de la auditoría física en el archivo `bitacora.log`.

- **Sincronización de I/O (Mutex Secundario):** Implementa su propio candado (`_log_mutex`) para garantizar que las operaciones de lectura/escritura (`open` y `close`) realizadas por diferentes hilos en milisegundos similares no corrompan ni mezclen las líneas de texto en el archivo físico.

---

## ⚙️ Conceptos de Sistemas Operativos Aplicados

- **Concurrencia:** Ejecución simultánea de múltiples hilos (Usuarios) peleando por recursos limitados.
- **Sección Crítica:** Segmentos del código donde se leen y escriben variables globales.
- **Exclusión Mutua (Mutex):** Uso dual de candados, tanto para la lógica de negocio (Servidor) como para la entrada/salida de datos (Bitácora).
- **Sincronización (`join`):** El hilo principal espera ordenadamente a que todos los hilos hijos terminen antes de generar el reporte.
- **Modularización:** Separación de responsabilidades mediante importación de módulos (`bitacora.py`).

---

## 🚀 Cómo ejecutar el proyecto

1. Asegúrese de tener Python instalado en su sistema.
2. Clone o descargue este repositorio.
3. Abra una terminal en la carpeta del proyecto y ejecute el archivo principal:
   ```bash
   python main.py
   ```
