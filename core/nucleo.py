"""
Fase 2 - Funciones núcleo. Todo el cálculo real vive aquí, con lógica
100% determinística: aritmética, Haversine y Dijkstra (vía networkx, que
es un algoritmo clásico de teoría de grafos, no IA).
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
    """
    Suma de tramos entre dos paradas SI están en la misma ruta Y en el
    sentido real del recorrido (nombre_a debe aparecer ANTES que nombre_b
    en esa ruta). Un Pumabús no se regresa, así que "de B a A" cuando el
    camión va de A a B no es un viaje real: se regresa (None, None) igual
    que haría mejor_ruta() en ese caso, para que ambas funciones sean
    consistentes entre sí.
    Regresa (minutos, ruta_id) o (None, None) si no comparten ruta, alguna
    no existe, o el sentido pedido es el inverso al de la ruta.
    """
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
    """
    Regresa (Parada, distancia_m) de la parada física más cercana a
    (lat, lon), comparando contra todas las paradas que SÍ tienen
    coordenadas cargadas (las que aún no se han geolocalizado se ignoran).
    Regresa (None, None) si ninguna parada tiene coordenadas todavía.
    """
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
    """
    Construye un grafo dirigido donde los nodos son nombres canónicos de
    parada y las aristas son los tramos de cada ruta, con peso = minutos.
    Si dos rutas comparten una parada con el mismo nombre, esa parada actúa
    como nodo de transbordo entre rutas.
    """
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
            # conserva la de menor peso (por si dos rutas comparten tramo)
            if G.has_edge(u, v):
                if peso < G[u][v]["weight"]:
                    G[u][v]["weight"] = peso
                    G[u][v]["ruta_id"] = ruta.id
            else:
                G.add_edge(u, v, weight=peso, ruta_id=ruta.id)
    return G


def mejor_ruta(bd, origen, destino):
    """
    Encuentra el trayecto de menor tiempo entre dos paradas por nombre.
    - Si comparten una ruta directa, ese es el camino más simple (Dijkstra
      lo encuentra igual, ya que en ese caso es el camino más corto).
    - Si no, arma un grafo con todas las rutas y usa Dijkstra (peso=tiempo)
      para encontrar la combinación de rutas más rápida, incluyendo posibles
      transbordos en paradas compartidas.
    Regresa un dict con: paradas (lista de nombres), tiempo_total_min,
    tramos (lista de dicts con de/a/minutos/ruta_id); o None si no hay camino.
    """
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
