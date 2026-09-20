"""
Fase 1 - Carga de la base de conocimiento (datos/rutas.json) a estructuras
en memoria. No usa ningún motor de base de datos externo ni IA: es lectura
directa de JSON con json de la librería estándar de Python.
"""

import json
import os
import re

RUTA_JSON_POR_DEFECTO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "datos",
    "rutas.json",
)


class Parada:
    """Una parada dentro de una ruta específica."""

    def __init__(self, id_, nombre, alias, lat, lon, tiempo_al_siguiente_min, ruta_id, orden):
        self.id = id_
        self.nombre = nombre
        self.alias = [a.lower() for a in (alias or [])]
        self.lat = lat
        self.lon = lon
        self.tiempo_al_siguiente_min = tiempo_al_siguiente_min
        self.ruta_id = ruta_id
        self.orden = orden  # posición (0-indexada) dentro de la ruta

    def __repr__(self):
        return f"Parada({self.id!r}, {self.nombre!r}, ruta={self.ruta_id})"


class Ruta:
    """Una ruta de Pumabús con sus paradas en orden."""

    def __init__(self, id_, nombre, paradas):
        self.id = id_
        self.nombre = nombre
        self.paradas = paradas  # lista de Parada, en orden

    def __repr__(self):
        return f"Ruta({self.id!r}, {self.nombre!r}, {len(self.paradas)} paradas)"


class BaseDeConocimiento:
    """
    Estructuras en memoria construidas a partir de datos/rutas.json:
      - self.rutas: dict {ruta_id: Ruta}
      - self.ruta_paradas: dict {ruta_id: [Parada, ...]} (mismo orden que Ruta.paradas)
      - self.paradas_por_nombre: dict {nombre_normalizado: [Parada, ...]}
                                  (una parada física puede aparecer en varias rutas)
      - self.alias_a_nombre: dict {alias_normalizado: nombre_canonico}
    """

    def __init__(self, rutas):
        self.rutas = rutas
        self.ruta_paradas = {ruta_id: ruta.paradas for ruta_id, ruta in rutas.items()}
        self.paradas_por_nombre = {}
        self.alias_a_nombre = {}
        self._indexar()

    def _indexar(self):
        for ruta in self.rutas.values():
            for parada in ruta.paradas:
                clave = _normalizar(parada.nombre)
                self.paradas_por_nombre.setdefault(clave, []).append(parada)
                # el nombre completo también cuenta como "alias" de sí mismo
                self.alias_a_nombre.setdefault(clave, set()).add(parada.nombre)
                for alias in parada.alias:
                    self.alias_a_nombre.setdefault(_normalizar(alias), set()).add(parada.nombre)

    def todas_las_paradas(self):
        vistas = {}
        for lista in self.paradas_por_nombre.values():
            for p in lista:
                vistas[p.id] = p
        return list(vistas.values())

    def resolver_nombre(self, texto):
        """
        Versión simple: regresa el nombre canónico si hay una única mejor
        coincidencia, o None si no hubo match O si hubo ambigüedad (dos
        nombres distintos empatados en especificidad). Para distinguir esos
        dos casos y poder pedirle al usuario que aclare, usar
        resolver_nombre_detallado().
        """
        nombre, _ = self.resolver_nombre_detallado(texto)
        return nombre

    def resolver_nombre_detallado(self, texto):
        """
        Regresa (nombre_canonico, candidatos_ambiguos).
        - Si hay una coincidencia clara: (nombre, [])
        - Si no hay ninguna coincidencia: (None, [])
        - Si dos o más paradas distintas quedan empatadas en especificidad
        (mismo largo de alias/nombre coincidente), elige automáticamente
        el nombre MÁS LARGO (más específico), ej. "Facultad de Filosofía"
        gana sobre "Filosofía".
        """
        candidatos = self._buscar_candidatos(texto)
        if not candidatos:
            return None, []

        mejor_len = max(largo for _, largo in candidatos)
        mejores_nombres = sorted({nombre for nombre, largo in candidatos if largo == mejor_len})

        if len(mejores_nombres) == 1:
            return mejores_nombres[0], []
        
        # Si hay ambigüedad (múltiples nombres con igual especificidad de alias),
        # elegir automáticamente el nombre más LARGO (más específico).
        nombre_mas_largo = max(mejores_nombres, key=len)
        return nombre_mas_largo, []

    def _buscar_candidatos(self, texto):
        """
        Lista de (nombre_canonico, largo_del_alias_que_hizo_match) para todo
        alias/nombre que aparezca como PALABRA COMPLETA (con \\b) dentro del
        texto. Coincidencia de palabra completa, no substring, para evitar
        falsos positivos como el alias corto "fa" (Facultad de Arquitectura)
        apareciendo dentro de la palabra "facultad".
        """
        clave = _normalizar(texto)
        if clave in self.alias_a_nombre:
            return [(nombre, len(clave)) for nombre in self.alias_a_nombre[clave]]

        candidatos = []
        for alias_norm, nombres in self.alias_a_nombre.items():
            patron = r"\b" + re.escape(alias_norm) + r"\b"
            if re.search(patron, clave):
                for nombre_canonico in nombres:
                    candidatos.append((nombre_canonico, len(alias_norm)))
        return candidatos


def _normalizar(texto):
    """
    Minúsculas, sin espacios sobrantes y SIN ACENTOS. Debe ser exactamente
    la misma normalización que usa nlu/interpretador.py, para que comparar
    longitudes de alias/nombres durante la resolución sea justo (si aquí no
    se quitaran acentos, un nombre corto sin acentos podía "ganar" por texto
    a un nombre más largo pero con acentos, aunque el segundo fuera el
    match correcto).
    """
    texto = texto.strip().lower()
    reemplazos = str.maketrans("áéíóúñ", "aeioun")
    return texto.translate(reemplazos)


def cargar_datos(ruta_archivo=None):
    """
    Lee datos/rutas.json y construye una BaseDeConocimiento.
    Lanza FileNotFoundError o json.JSONDecodeError si el archivo no existe
    o está mal formado (se recomienda capturarlos en chat/main.py).
    """
    ruta_archivo = ruta_archivo or RUTA_JSON_POR_DEFECTO
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        datos = json.load(f)

    rutas = {}
    for ruta_raw in datos.get("rutas", []):
        paradas = []
        for orden, parada_raw in enumerate(ruta_raw.get("paradas", [])):
            paradas.append(
                Parada(
                    id_=parada_raw["id"],
                    nombre=parada_raw["nombre"],
                    alias=parada_raw.get("alias", []),
                    lat=parada_raw.get("lat"),
                    lon=parada_raw.get("lon"),
                    tiempo_al_siguiente_min=parada_raw.get("tiempo_al_siguiente_min"),
                    ruta_id=ruta_raw["id"],
                    orden=orden,
                )
            )
        rutas[ruta_raw["id"]] = Ruta(
            id_=ruta_raw["id"], nombre=ruta_raw["nombre"], paradas=paradas
        )

    return BaseDeConocimiento(rutas)


if __name__ == "__main__":
    # Pruebas rápidas en consola (Fase 1, punto 3 del flujo de trabajo)
    bd = cargar_datos()
    print(f"Rutas cargadas: {list(bd.rutas.keys())}")
    for ruta_id, ruta in bd.rutas.items():
        print(f"  {ruta.nombre}: {len(ruta.paradas)} paradas")
        for p in ruta.paradas:
            print(f"    - {p.orden}: {p.nombre} (alias: {p.alias})")
    print("\nPrueba de resolución de alias:")
    for texto in ["ing", "metro u", "rectoria", "algo que no existe"]:
        print(f"  '{texto}' -> {bd.resolver_nombre(texto)}")
