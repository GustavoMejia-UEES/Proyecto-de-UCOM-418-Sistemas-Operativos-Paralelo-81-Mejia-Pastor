# Registro de Avances - Proyecto Sistemas Operativos

## Avance 4: Servidor de Descargas

### Contexto del proyecto

Servidor de descargas: plataforma que gestiona multiples solicitudes desde un servidor con capacidad limitada, administrando conexiones activas y el trafico total generado.

## 1) Recurso compartido identificado

### Tipo basico

- `conexiones_activas` (`int`): contador global de cupos ocupados en el servidor.
- `bytes_transferidos_totales` (`float`): acumulador global del trafico de descargas.

Por que son compartidos:
Son variables unicas del objeto `Servidor` que todos los hilos `UsuarioDescarga` leen y modifican durante su ejecucion.

### Tipo complejo

- `historial_trafico` (`list`): bitacora compartida donde cada hilo registra el resultado de su solicitud.

Por que es compartido:
Todos los hilos escriben sobre la misma estructura para mantener un unico historial del sistema.

## 2) Entidades que acceden al recurso compartido

- Clase `Servidor` (`servidor.py`)
  Atributos principales: `nombre_servidor`, `capacidad_maxima`, `ancho_banda_total`, `conexiones_activas`, `bytes_transferidos_totales`, `historial_trafico`, `mutex`.
  Rol: centralizar el estado comun y proveer el reporte final.

- Clase `UsuarioDescarga` (`usuario.py`)
  Atributos principales: `id_solicitud`, `servidor`, `tamano_archivo`.
  Rol: representar cada solicitud concurrente y competir por el acceso al recurso compartido del servidor.

## 3) Reflexion sobre la seccion critica (sin codigo)

La seccion critica ocurre cuando un hilo:

- valida si hay cupo disponible,
- incrementa o decrementa `conexiones_activas`,
- actualiza `bytes_transferidos_totales`,
- escribe en `historial_trafico`.

Riesgo de no protegerla:
Sin exclusion mutua puede ocurrir condicion de carrera. El resultado seria inconsistente: aceptar mas usuarios que la capacidad real, perder actualizaciones del trafico total o registrar logs incompletos/incoherentes.

## 4) Desarrollo implementado

- `Servidor`: constructor con estado compartido + `threading.Lock` + metodo `generar_reporte_estado()`.
- `UsuarioDescarga`: hereda de `threading.Thread`; simula solicitudes y actualiza recursos compartidos usando el mutex.
- `main.py`: instancia un objeto `Servidor`, crea varios objetos `UsuarioDescarga`, ejecuta `start()` y `join()`, y genera reporte final.

## 5) Distribucion de actividades

### Estudiante: Juan Fernando Pastor Huaman

- Implementacion de `UsuarioDescarga` y su flujo concurrente en `run()`.
- Integracion de ejecucion concurrente en `main.py`.
- Documentacion tecnica de seccion critica y riesgos.

### Estudiante: Gustavo Jose Mejia Riofrio

- Implementacion de `Servidor` y atributos de control compartido.
- Definicion de sincronizacion con `threading.Lock`.
- Construccion del reporte de estado y bitacora de trafico.

## 6) Versionamiento (checklist para la entrega)

- Versionado local y remoto por ramas individuales.
- Merge de ramas de trabajo hacia `main`.
- Obtencion del SHA del ultimo commit.

Comandos utiles:

```bash
git checkout main
git pull origin main
git branch
git log --oneline -n 5
git rev-parse HEAD
git push origin main
```
