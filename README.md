# Proyecto UCOM 418 - Sistemas Operativos

## Información Académica

- Materia: UCOM 418 - Sistemas Operativos
- Paralelo: 81
- Integrantes:
  - Gustavo Jose Mejia Riofrio
  - Juan Fernando Pastor Huaman

---

## Resumen del Monorepo

Este repositorio contiene dos líneas de trabajo del curso:

1. Simulador de Servidor de Descargas con concurrencia en Python (hilos, mutex y bitácora).
2. Videojuego multijugador Thread Wars con cliente en Godot y backend WebSocket en Python.

Estructura principal:

- main.py, servidor.py, usuario.py, analizador_bitacora.py
  - Simulación clásica de descargas concurrentes y análisis de bitácora.
- juego-servidor/
  - Backend del juego en Python con sockets WebSocket y lógica de partidas.
- thread-wars/
  - Proyecto Godot del frontend del juego y export web.

---

## Parte 1: Servidor de Descargas (Simulación SO)

El Servidor de Descargas modela múltiples usuarios concurrentes que compiten por recursos limitados. Se aplican conceptos de sección crítica, exclusión mutua y sincronización de hilos para evitar condiciones de carrera.

Componentes:

- servidor.py
  - Controla conexiones activas y capacidad del servidor.
  - Protege recursos compartidos con threading.Lock (acquire/release).
- usuario.py
  - Modela clientes concurrentes con hilos y reintentos.
- bitácora y análisis
  - Registro de eventos en archivos y análisis posterior de actividad.

Conceptos aplicados:

- Concurrencia con hilos.
- Sección crítica y mutex.
- Sincronización con join.
- Modularización por responsabilidades.

---

## Parte 2: Thread Wars (Godot + Backend Python)

Thread Wars es un juego multijugador con enfoque en conceptos de Sistemas Operativos (ataque/reparación de nodos, mutex, coordinación por roles y estado compartido).

### ¿Por qué se usó Godot?

Se eligió Godot porque permite:

- Desarrollo rápido de gameplay 2D.
- Integración sencilla de WebSocket en GDScript.
- Exportación directa a Web para despliegue en hosting estático.

### Arquitectura del juego

- Frontend (Godot Web): thread-wars/
  - Maneja UI, input del jugador y render del mundo.
  - Se conecta al backend por WebSocket desde NetworkManager.gd.
- Backend (Python): juego-servidor/
  - main_ws.py: servidor WebSocket multi-sala.
  - logica_juego.py y servidor_juego.py: reglas de juego, nodos, mutex y estado de partida.
  - usuario_juego.py: modelo de jugador.
  - bitacora_juego.py: auditoría de eventos de juego.

### Flujo de conexión

1. El cliente Godot abre WebSocket.
2. El backend asigna sala, host y roles.
3. El servidor procesa acciones (ataques, reparaciones, mutex, etc.).
4. El backend emite estado_mundo en tiempo real para sincronizar a todos.

---

## Despliegue en Producción

### Backend WebSocket (Railway)

- Servicio desplegado en Railway desde la carpeta juego-servidor (monorepo con Root Directory).
- El backend usa puerto dinámico con variable PORT y host 0.0.0.0.
- URL WebSocket de producción:
  - wss://thread-wars.up.railway.app

### Frontend Web (Netlify)

- El export web de Godot se publica en Netlify.
- URL pública del juego:
  - https://thread-wars.netlify.app/

### Integración Frontend-Backend

En thread-wars/api/NetworkManager.gd:

- En web se prioriza una URL inyectada desde JavaScript o query param ws.
- Si no se inyecta nada, usa fallback de producción:
  - wss://thread-wars.up.railway.app
- En local/editor usa:
  - ws://localhost:8000

Nota: En producción web se usa wss para evitar bloqueo del navegador por contenido mixto cuando el frontend corre sobre https.

---

## Ejecución Local

### Simulador de descargas

1. Abrir terminal en la raíz del repositorio.
2. Ejecutar:

python main.py

### Backend del juego

1. Entrar a la carpeta juego-servidor.
2. Instalar dependencias:

pip install -r requirements.txt

3. Ejecutar servidor:

python main_ws.py

El backend local corre en ws://localhost:8000 por defecto.

### Frontend Godot

1. Abrir thread-wars con Godot.
2. Ejecutar en editor para pruebas locales.
3. Para despliegue, exportar a Web y publicar la carpeta de export en Netlify.

---

## Requisitos

- Python 3.10+
- Dependencias Python en juego-servidor/requirements.txt
- Godot (para edición y export del cliente)

---

## Estado del Proyecto

El repositorio integra correctamente:

- Backend Python concurrente para simulación académica.
- Juego multijugador con backend en Railway.
- Cliente web Godot publicado en Netlify y conectado por WebSocket seguro.
