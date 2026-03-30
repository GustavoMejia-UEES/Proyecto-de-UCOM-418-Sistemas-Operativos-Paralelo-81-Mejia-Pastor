import threading
import time
import random

class UsuarioDescarga(threading.Thread):
    def __init__(self, id_solicitud, servidor):
        super().__init__()
        self.id_solicitud = id_solicitud
        self.servidor = servidor
        
        # NUEVOS ATRIBUTOS - "Vitaminas" para mayor realismo
        self.tipo_archivo = random.choice(["TEXTO", "IMAGEN", "VIDEO"])
        
        # Tamaño y ancho de banda según el tipo de archivo
        if self.tipo_archivo == "TEXTO":
            self.tamano_archivo = round(random.uniform(5.0, 15.0), 2)
            self.ancho_banda_requerido = round(random.uniform(5.0, 10.0), 2)
        elif self.tipo_archivo == "IMAGEN":
            self.tamano_archivo = round(random.uniform(20.0, 50.0), 2)
            self.ancho_banda_requerido = round(random.uniform(15.0, 25.0), 2)
        else:  # VIDEO
            self.tamano_archivo = round(random.uniform(100.0, 300.0), 2)
            self.ancho_banda_requerido = round(random.uniform(40.0, 60.0), 2)
        
        self.tiempo_timeout = random.uniform(5.0, 15.0)  # Máximo tiempo de espera
        self.max_intentos = 3
        self.name = f"Usuario {id_solicitud}"
        self.puerto_asignado = None

    def run(self):
        intentos = 0
        conectado = False
        tiempo_inicio_intento = time.time()
        
        # Usar mutex.acquire() explícitamente para reintentos
        while intentos < self.max_intentos and not conectado:
            tiempo_transcurrido = time.time() - tiempo_inicio_intento
            
            # Verificar timeout
            if tiempo_transcurrido > self.tiempo_timeout:
                print(f"[x] {self.name} TIMEOUT: Excedido tiempo máximo ({self.tiempo_timeout:.2f}s)")
                break
            
            # Solicitar conexión (ya usa mutex.acquire() internamente)
            exito, puerto, ancho_banda_asignado = self.servidor.solicitar_conexion(
                self.id_solicitud, 
                self.tipo_archivo, 
                self.ancho_banda_requerido
            )
            
            if exito:
                conectado = True
                self.puerto_asignado = puerto
            else:
                intentos += 1
                if intentos < self.max_intentos:
                    print(f"[!] {self.name} (Tipo: {self.tipo_archivo}) en espera... (Intento {intentos}/{self.max_intentos})")
                    time.sleep(random.uniform(0.5, 1.5))

        if conectado:
            # Calcular tiempo de descarga usando fórmula: tamaño / ancho_banda
            tiempo_descarga_segundos = self.tamano_archivo / self.ancho_banda_requerido
            print(f"[+] {self.name} ACEPTADO. Tipo: {self.tipo_archivo}, "
                  f"Descargando {self.tamano_archivo}MB @ {self.ancho_banda_requerido}MB/s "
                  f"(ETA: {tiempo_descarga_segundos:.2f}s)")
            
            # Dividir descarga en bloques
            bloques = 4
            tiempo_por_bloque = tiempo_descarga_segundos / bloques
            
            for i in range(bloques):
                time.sleep(tiempo_por_bloque)
                porcentaje = int(((i + 1) / bloques) * 100)
                print(f"   -> [{self.name}] {self.tipo_archivo}: {porcentaje}%")

            # Registrar salida (usa mutex.acquire() internamente)
            self.servidor.registrar_salida(self.id_solicitud, self.tamano_archivo)
            print(f"[-] {self.name} COMPLETADO. Puerto {self.puerto_asignado} liberado.")
        
        else:
            print(f"[x] {self.name} CANCELADO: No se logró conseguir cupo.")