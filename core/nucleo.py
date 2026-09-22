"""
Fase 2 - Funciones núcleo. Todo el cálculo real vive aquí, con lógica
100% aritmética, Haversine y Dijkstra (vía networkx, que
es un algoritmo clásico de teoría de grafos).
"""

import math

import networkx as nx

from core.cargar_datos import _normalizar


def paradas_de_ruta(bd, ruta_id):
    """Regresa la lista ordenada de Parada de una ruta, o [] si no existe."""
    ruta = bd.rutas.get(ruta_id)
    return ruta.paradas if ruta else []


def rutas_por_parada(bd, nombre):
    """
    Regresa la lista ordenada (por id) de ids de ruta que pasan por la
    parada con ese nombre canónico. [] si el nombre no existe en ninguna
    ruta.
    """
    clave = _normalizar(nombre)
    ids = set()
    for ruta in bd.rutas.values():
        for parada in ruta.paradas:
            if _normalizar(parada.nombre) == clave:
                ids.add(ruta.id)
                break
    return sorted(ids)


def tiempo_entre_paradas(bd, nombre_a, nombre_b):
    for ruta in bd.rutas.values():
        idx_a = _indice_en_ruta(ruta, nombre_a)
        idx_b = _indice_en_ruta(ruta, nombre_b)
        if idx_a is not None and idx_b is not None and idx_a < idx_b:
            minutos = 0
            for parada in ruta.paradas[idx_a:idx_b]:
                if parada.tiempo_al_siguiente_min is None:
                    return None, None  # tramo sin dato, no se puede calcular
                minutos += parada.tiempo_al_siguiente_min
            return minutos, ruta.id
    return None, None


def _indice_en_ruta(ruta, nombre):
    clave = _normalizar(nombre)
    for i, parada in enumerate(ruta.paradas):
        if _normalizar(parada.nombre) == clave:
            return i
    return None


def distancia_haversine_m(lat1, lon1, lat2, lon2):
    """Distancia en metros entre dos coordenadas usando la fórmula de Haversine."""
    R = 6371000  # radio de la Tierra en metros
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def parada_mas_cercana(bd, lat, lon):
    mejor_parada = None
    mejor_dist = float("inf")
    for parada in bd.todas_las_paradas():
        if parada.lat is None or parada.lon is None:
            continue
        d = distancia_haversine_m(lat, lon, parada.lat, parada.lon)
        if d < mejor_dist:
            mejor_dist = d
            mejor_parada = parada
    return mejor_parada, mejor_dist


def _construir_grafo(bd):
    G = nx.DiGraph()
    for ruta in bd.rutas.values():
        for i in range(len(ruta.paradas) - 1):
            actual = ruta.paradas[i]
            siguiente = ruta.paradas[i + 1]
            if actual.tiempo_al_siguiente_min is None:
                continue
            u, v = actual.nombre, siguiente.nombre
            peso = actual.tiempo_al_siguiente_min
            # si ya existe una arista más rápida entre las mismas paradas, se
            # conserva la de menor peso 
            if G.has_edge(u, v):
                if peso < G[u][v]["weight"]:
                    G[u][v]["weight"] = peso
                    G[u][v]["ruta_id"] = ruta.id
            else:
                G.add_edge(u, v, weight=peso, ruta_id=ruta.id)
    return G


def mejor_ruta(bd, origen, destino):
    nombre_origen = bd.resolver_nombre(origen) or origen
    nombre_destino = bd.resolver_nombre(destino) or destino

    G = _construir_grafo(bd)
    if nombre_origen not in G or nombre_destino not in G:
        return None
    try:
        camino = nx.dijkstra_path(G, nombre_origen, nombre_destino, weight="weight")
    except nx.NetworkXNoPath:
        return None

    tramos = []
    tiempo_total = 0
    for i in range(len(camino) - 1):
        u, v = camino[i], camino[i + 1]
        datos_arista = G[u][v]
        tramos.append(
            {
                "de": u,
                "a": v,
                "minutos": datos_arista["weight"],
                "ruta_id": datos_arista["ruta_id"],
            }
        )
        tiempo_total += datos_arista["weight"]

    return {
        "paradas": camino,
        "tiempo_total_min": tiempo_total,
        "tramos": tramos,
    }
