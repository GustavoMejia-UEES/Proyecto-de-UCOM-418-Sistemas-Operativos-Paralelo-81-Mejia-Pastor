#!/usr/bin/env python3
"""
Analizador de Bitácora - Verifica Exclusión Mutua

Este script analiza bitacora.log y verifica que:
1. Nunca haya dos eventos ACCESO simultáneos de usuarios diferentes
2. Cada ACCESO esté precedido por un INTENTO
3. Cada SALIDA esté dentro de la sección crítica
"""

import re
from collections import defaultdict
from datetime import datetime

class AnalizadorBitacora:
    def __init__(self, archivo_log='bitacora.log'):
        self.archivo = archivo_log
        self.eventos = []
        self.usuarios_activos = set()
        self.errores = []
        
    def leer_log(self):
        """Lee el archivo de bitácora y parsea eventos."""
        try:
            with open(self.archivo, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
        except FileNotFoundError:
            print(f"[ERROR] Archivo {self.archivo} no encontrado.")
            return False
        
        # Patrón: [TIMESTAMP] - [Usuario X - ACCIÓN - Descripción]
        patron = r'\[(.*?)\] - \[(Usuario \d+) - (\w+) -.*?\]'
        
        for i, linea in enumerate(lineas, 1):
            match = re.match(patron, linea)
            if match:
                timestamp, usuario, accion = match.groups()
                self.eventos.append({
                    'linea': i,
                    'timestamp': timestamp,
                    'usuario': usuario,
                    'accion': accion,
                    'texto_original': linea.strip()
                })
        
        return len(self.eventos) > 0
    
    def verificar_exclusion_mutua(self, capacidad_maxima=3):
        """Verifica que nunca haya más de capacidad_maxima usuarios en ACCESO."""
        usuarios_en_acceso = {}  # usuario -> timestamp_acceso
        
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
                    self.errores.append(
                        f"[WARNING] Usuario {usuario} hace SALIDA sin ACCESO previo (línea {evento['linea']})"
                    )
        
        return len([e for e in self.errores if 'CRITICAL' in e]) == 0
    
    def verificar_secuencia_eventos(self):
        """Verifica que la secuencia de eventos sea válida.
        
        Secuencia válida:
        - INTENTO* -> ACCESO -> SALIDA (usuario obtiene acceso)
        - INTENTO -> INTENTO -> ... (usuario reintenta sin acceso)
        
        Nota: Un usuario puede hacer múltiples INTENTO si no obtiene acceso.
        """
        estado_usuario = defaultdict(list)  # usuario -> lista de estados
        
        for evento in self.eventos:
            usuario = evento['usuario']
            accion = evento['accion']
            
            estados_previos = estado_usuario[usuario]
            
            # Obtener el último estado (o cadena vacía si es la primera vez)
            estado_actual = estados_previos[-1] if estados_previos else ''
            
            # INTENTO: puede ocurrir en estado inicial o después de otro INTENTO (reintento)
            if accion == 'INTENTO':
                if estado_actual not in ['', 'INTENTO', 'SALIDA']:
                    self.errores.append(
                        f"[WARNING] {usuario} INTENTO cuando estado es {estado_actual} (línea {evento['linea']})"
                    )
            
            # ACCESO: debe ocurrir después de INTENTO
            elif accion == 'ACCESO':
                if estado_actual != 'INTENTO':
                    self.errores.append(
                        f"[WARNING] {usuario} ACCESO cuando estado es {estado_actual} (línea {evento['linea']}). Esperado INTENTO."
                    )
            
            # SALIDA: debe ocurrir después de ACCESO
            elif accion == 'SALIDA':
                if estado_actual != 'ACCESO':
                    self.errores.append(
                        f"[WARNING] {usuario} SALIDA cuando estado es {estado_actual} (línea {evento['linea']}). Esperado ACCESO."
                    )
            
            # Agregar el nuevo estado a la lista
            estado_usuario[usuario].append(accion)
    
    def contar_estadisticas(self):
        """Calcula estadísticas de ejecución."""
        estadisticas = {
            'total_eventos': len(self.eventos),
            'usuarios_unicos': len(set(e['usuario'] for e in self.eventos)),
            'intentos': sum(1 for e in self.eventos if e['accion'] == 'INTENTO'),
            'accesos': sum(1 for e in self.eventos if e['accion'] == 'ACCESO'),
            'salidas': sum(1 for e in self.eventos if e['accion'] == 'SALIDA'),
            'accesos_max_simultaneos': self._calcular_max_simultaneos()
        }
        return estadisticas
    
    def _calcular_max_simultaneos(self):
        """Calcula el máximo número de ACCESO simultaneos en cualquier momento."""
        usuarios_activos = set()
        max_simultaneos = 0
        
        for evento in self.eventos:
            usuario = evento['usuario']
            
            if evento['accion'] == 'ACCESO':
                usuarios_activos.add(usuario)
                max_simultaneos = max(max_simultaneos, len(usuarios_activos))
            elif evento['accion'] == 'SALIDA':
                usuarios_activos.discard(usuario)
        
        return max_simultaneos
    
    def analizar(self):
        """Ejecuta el análisis completo."""
        print("=" * 70)
        print("ANALIZADOR DE BITÁCORA - EXCLUSIÓN MUTUA")
        print("=" * 70)
        
        # Paso 1: Leer log
        print("\n[1] Leyendo bitácora...")
        if not self.leer_log():
            print("[ERROR] No se pudieron leer eventos del log.")
            return False
        
        print(f"✓ Se leyeron {len(self.eventos)} eventos")
        
        # Paso 2: Verificar exclusión mutua
        print("\n[2] Verificando exclusión mutua...")
        es_valido = self.verificar_exclusion_mutua()
        if es_valido:
            print("✓ Exclusión mutua verificada: No hay violaciones")
        else:
            print("✗ ADVERTENCIA: Se detectaron violaciones")
        
        # Paso 3: Verificar secuencia de eventos
        print("\n[3] Verificando secuencia de eventos...")
        eventos_previos = len(self.errores)
        self.verificar_secuencia_eventos()
        if len(self.errores) == eventos_previos:
            print("✓ Secuencia de eventos válida: INTENTO -> ACCESO -> SALIDA")
        else:
            print("✗ Se detectaron anomalías en la secuencia")
        
        # Paso 4: Estadísticas
        print("\n[4] Estadísticas de ejecución:")
        stats = self.contar_estadisticas()
        for clave, valor in stats.items():
            print(f"   {clave}: {valor}")
        
        # Paso 5: Mostrar errores/advertencias
        if self.errores:
            print("\n[5] Errores y Advertencias:")
            for error in self.errores:
                print(f"   {error}")
        else:
            print("\n[5] ✓ Sin errores o advertencias")
        
        # Resumen
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
        """Muestra una línea de tiempo de los primeros eventos."""
        print("\n" + "=" * 70)
        print("TIMELINE DE EVENTOS (primeros " + str(max_eventos) + ")")
        print("=" * 70)
        
        for evento in self.eventos[:max_eventos]:
            timestamp = evento['timestamp']
            usuario = evento['usuario']
            accion = evento['accion']
            
            # Codificar color para acción
            if accion == 'INTENTO':
                simbolo = '→'  # Entrada
            elif accion == 'ACCESO':
                simbolo = '✓'  # Acceso
            else:  # SALIDA
                simbolo = '←'  # Salida
            
            print(f"{timestamp} {simbolo:2s} {usuario:8s} {accion}")

def main():
    analizador = AnalizadorBitacora('bitacora.log')
    
    # Ejecutar análisis
    resultado = analizador.analizar()
    
    # Mostrar timeline
    analizador.mostrar_timeline(max_eventos=30)
    
    # Retornar código de salida
    return 0 if resultado else 1

if __name__ == '__main__':
    exit(main())
