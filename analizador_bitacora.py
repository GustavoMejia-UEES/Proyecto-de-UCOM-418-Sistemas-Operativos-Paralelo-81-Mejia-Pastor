
import re
import threading
import sys
from collections import defaultdict
from datetime import datetime

class AnalizadorBitacora:
    def __init__(self, archivo_log='bitacora.log'):
        self.archivo = archivo_log
        self.eventos = []
        self.usuarios_activos = set()
        self.errores = []
        self.mutex = threading.Lock()
        
    def leer_log(self):
        self.mutex.acquire()
        try:
            try:
                with open(self.archivo, 'r', encoding='utf-8') as f:
                    lineas = f.readlines()
            except FileNotFoundError:
                print(f"[ERROR] Archivo {self.archivo} no encontrado.")
                return False
            
            self.eventos.clear()
            patron = r'\[(.*?)\] \[.*?\] \[(\w+)\] \[Hilo_(\d+)\]'
            estado_actual_usuario = {}
            
            for i, linea in enumerate(lineas, 1):
                match = re.search(patron, linea)
                
                if match:
                    timestamp = match.group(1)
                    tipo_evento = match.group(2)
                    usuario_id = match.group(3)
                    
                    usuario = f"Usuario {usuario_id}"
                    accion = ""
                    
                    if tipo_evento == "WAIT":
                        if estado_actual_usuario.get(usuario) != "ACCESO":
                            accion = "INTENTO"
                        else:
                            continue 
                    elif tipo_evento == "CONNECT":
                        accion = "ACCESO"
                        estado_actual_usuario[usuario] = "ACCESO"
                    elif tipo_evento == "DISCONNECT":
                        accion = "SALIDA"
                        estado_actual_usuario[usuario] = "SALIDA"
                    else:
                        continue 
                        
                    self.eventos.append({
                        'linea': i,
                        'timestamp': timestamp,
                        'usuario': usuario,
                        'accion': accion,
                        'texto_original': linea.strip()
                    })
            
            return len(self.eventos) > 0
        finally:
            self.mutex.release()
    
    def verificar_exclusion_mutua(self, capacidad_maxima):
        usuarios_en_acceso = {}
        self.mutex.acquire()
        try:
            for evento in self.eventos:
                usuario = evento['usuario']
                accion = evento['accion']
                
                if accion == 'ACCESO':
                    usuarios_en_acceso[usuario] = evento['timestamp']
                    if len(usuarios_en_acceso) > capacidad_maxima:
                        self.errores.append(
                            f"[CRITICAL] Violación de exclusión mutua (línea {evento['linea']}): "
                            f"{len(usuarios_en_acceso)} usuarios en ACCESO simultáneamente. "
                            f"Usuarios: {list(usuarios_en_acceso.keys())}"
                        )
                elif accion == 'SALIDA':
                    if usuario in usuarios_en_acceso:
                        del usuarios_en_acceso[usuario]
                    else:
                        self.errores.append(f"[WARNING] Usuario {usuario} hace SALIDA sin ACCESO previo (línea {evento['linea']})")
            return len([e for e in self.errores if 'CRITICAL' in e]) == 0
        finally:
            self.mutex.release()
    
    def verificar_secuencia_eventos(self):
        estado_usuario = defaultdict(list)
        self.mutex.acquire()
        try:
            for evento in self.eventos:
                usuario = evento['usuario']
                accion = evento['accion']
                estados_previos = estado_usuario[usuario]
                estado_actual = estados_previos[-1] if estados_previos else ''
                
                if accion == 'INTENTO' and estado_actual not in ['', 'INTENTO', 'SALIDA']:
                    self.errores.append(f"[WARNING] {usuario} INTENTO cuando estado es {estado_actual} (línea {evento['linea']})")
                elif accion == 'ACCESO' and estado_actual != 'INTENTO':
                    self.errores.append(f"[WARNING] {usuario} ACCESO cuando estado es {estado_actual} (línea {evento['linea']}). Esperado INTENTO.")
                elif accion == 'SALIDA' and estado_actual != 'ACCESO':
                    self.errores.append(f"[WARNING] {usuario} SALIDA cuando estado es {estado_actual} (línea {evento['linea']}). Esperado ACCESO.")
                
                estado_usuario[usuario].append(accion)
        finally:
            self.mutex.release()
    
    def contar_estadisticas(self):
        self.mutex.acquire()
        try:
            return {
                'total_eventos': len(self.eventos),
                'usuarios_unicos': len(set(e['usuario'] for e in self.eventos)),
                'intentos': sum(1 for e in self.eventos if e['accion'] == 'INTENTO'),
                'accesos': sum(1 for e in self.eventos if e['accion'] == 'ACCESO'),
                'salidas': sum(1 for e in self.eventos if e['accion'] == 'SALIDA'),
                'accesos_max_simultaneos': self._calcular_max_simultaneos_interno()
            }
        finally:
            self.mutex.release()
    
    def _calcular_max_simultaneos_interno(self):
        usuarios_activos = set()
        max_simultaneos = 0
        for evento in self.eventos:
            if evento['accion'] == 'ACCESO':
                usuarios_activos.add(evento['usuario'])
                max_simultaneos = max(max_simultaneos, len(usuarios_activos))
            elif evento['accion'] == 'SALIDA':
                usuarios_activos.discard(evento['usuario'])
        return max_simultaneos
    
    def analizar(self, capacidad_maxima):
        print("=" * 70)
        print("ANALIZADOR DE BITÁCORA - EXCLUSIÓN MUTUA")
        print(f"(Verificando para una capacidad máxima de {capacidad_maxima} nodos)")
        print("=" * 70)
        
        print("\n[1] Leyendo bitácora...")
        if not self.leer_log():
            print("[ERROR] No se pudieron leer eventos del log.")
            return False
        
        print(f"✓ Se leyeron {len(self.eventos)} eventos")
        
        print("\n[2] Verificando exclusión mutua...")
        es_valido = self.verificar_exclusion_mutua(capacidad_maxima)
        if es_valido:
            print("✓ Exclusión mutua verificada: No hay violaciones")
        else:
            print("✗ ADVERTENCIA: Se detectaron violaciones")
        
        print("\n[3] Verificando secuencia de eventos...")
        eventos_previos = len(self.errores)
        self.verificar_secuencia_eventos()
        if len(self.errores) == eventos_previos:
            print("✓ Secuencia de eventos válida: INTENTO -> ACCESO -> SALIDA")
        else:
            print("✗ Se detectaron anomalías en la secuencia")
        
        print("\n[4] Estadísticas de ejecución:")
        stats = self.contar_estadisticas()
        for clave, valor in stats.items():
            print(f"   {clave}: {valor}")
        
        print("\n[5] Errores y Advertencias:")
        self.mutex.acquire()
        try:
            if self.errores:
                for error in self.errores:
                    print(f"   {error}")
            else:
                print("✓ Sin errores o advertencias")
        finally:
            self.mutex.release()
        
        print("\n" + "=" * 70)
        if es_valido and len(self.errores) == 0:
            print("✓✓✓ CONCLUSIÓN: Sistema sincronizado correctamente ✓✓✓")
            print("\nEvidencia de exclusión mutua:")
            print(f"- Máximo usuarios simultáneos: {stats['accesos_max_simultaneos']}")
            print(f"- Total de ACCESO completados: {stats['accesos']}")
            print(f"- Ninguna violación de capacidad detectada")
            return True
        else:
            print("✗ CONCLUSIÓN: Se detectaron problemas de sincronización")
            return False
    
    def mostrar_timeline(self, max_eventos=20):
        print("\n" + "=" * 70)
        print("TIMELINE DE EVENTOS (primeros " + str(max_eventos) + ")")
        print("=" * 70)
        self.mutex.acquire()
        try:
            for evento in self.eventos[:max_eventos]:
                timestamp = evento['timestamp']
                usuario = evento['usuario']
                accion = evento['accion']
                if accion == 'INTENTO': simbolo = '→'
                elif accion == 'ACCESO': simbolo = '✓'
                else: simbolo = '←'
                print(f"{timestamp} {simbolo:2s} {usuario:8s} {accion}")
        finally:
            self.mutex.release()

def main():
    capacidad = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    analizador = AnalizadorBitacora('bitacora.log')
    resultado = analizador.analizar(capacidad)
    analizador.mostrar_timeline(max_eventos=30)
    return 0 if resultado else 1

if __name__ == '__main__':
    exit(main())