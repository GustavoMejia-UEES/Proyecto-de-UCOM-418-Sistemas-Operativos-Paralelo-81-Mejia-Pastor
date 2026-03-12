# Proyecto UCOM 418: Servidor de Descargas 🖥️⬇️

## Información Académica

- **Materia:** UCOM 418 - Sistemas Operativos
- **Paralelo:** 81
- **Integrantes:**
  - Gustavo Jose Mejia Riofrio
  - Juan Fernando Pastor Huaman

---

## 📌 Explicación del Proyecto

El **Servidor de Descargas** es una plataforma concurrente que simula y gestiona múltiples solicitudes de descarga dirigidas a un servidor con capacidad limitada. El sistema administra de forma segura las conexiones activas, el control de aforo y el registro de auditoría del tráfico generado, garantizando que no existan condiciones de carrera (race conditions) al modificar los recursos compartidos.

---

## 🏗️ Arquitectura y Diseño de la Solución

El proyecto está diseñado bajo un modelo de concurrencia basado en la **Herencia de `threading.Thread`** y el encapsulamiento de recursos, dividido en dos entidades principales:

### 1. Clase `Servidor` (Gestión de Recursos Compartidos)

Actúa como el monitor central del sistema. Posee una capacidad máxima de conexiones y un ancho de banda total.

- **Mecanismo de Sincronización (Mutex):** Para proteger la sección crítica (las variables `conexiones_activas` y `bytes_transferidos_totales`), el servidor instancia un candado lógico mediante `threading.Lock()`.
- **Uso de `acquire()` y `release()`:** Los métodos de entrada (`solicitar_conexion`) y salida (`registrar_salida`) utilizan explícitamente estas instrucciones para bloquear el acceso a otros hilos mientras un usuario actualiza los contadores, previniendo la corrupción de datos y asegurando la liberación del candado en todos los flujos de ejecución para evitar _Deadlocks_.
- **Auditoría Física:** Al finalizar una descarga, el servidor genera un registro físico persistente en un archivo `servidor-trafico.log`.

### 2. Clase `UsuarioDescarga` (Entidad Concurrente)

Representa a los clientes que intentan acceder al servidor. Hereda directamente de `threading.Thread`, lo que le permite tener un estado interno, memoria y comportamiento autónomo.

- **Sistema de Reintentos (Polling):** Si el servidor rechaza la conexión por estar lleno, el hilo no finaliza; entra en un estado de espera (`time.sleep`) y vuelve a intentar conectarse hasta un máximo de veces permitido, simulando el comportamiento real de un cliente de red.
- **Simulación de Latencia:** Una vez aceptada la solicitud, el hilo calcula su tiempo de descarga basándose en el tamaño del archivo asignado aleatoriamente y el ancho de banda disponible del servidor, simulando la transferencia por bloques sin bloquear a los demás hilos (fuera del Mutex).

---

## ⚙️ Conceptos de Sistemas Operativos Aplicados

- **Concurrencia:** Ejecución simultánea de múltiples hilos (Usuarios) peleando por un recurso.
- **Sección Crítica:** Segmentos del código donde se leen y escriben variables globales compartidas.
- **Exclusión Mutua (Mutex):** Garantía de que solo un hilo a la vez puede ejecutar la sección crítica.
- **Sincronización (`join`):** El hilo principal (`main`) espera ordenadamente a que todos los hilos hijos terminen su ciclo de vida antes de imprimir el reporte final.

---

## 🚀 Cómo ejecutar el proyecto

1. Asegúrese de tener Python instalado en su sistema.
2. Clone o descargue este repositorio.
3. Abra una terminal en la carpeta del proyecto y ejecute el archivo principal:
   ```bash
   python main.py
   ```
