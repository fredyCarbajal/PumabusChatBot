"""
Fase 3 - Interpretación de preguntas mediante reglas (estilo ELIZA).
Sin NLU basado en modelos: solo expresiones regulares y listas de alias
(estas últimas ya cargadas en la BaseDeConocimiento desde datos/rutas.json).
"""

import re

PATRONES_SALUDO = [
    r"^\s*hola\b",
    r"^\s*hey\b",
    r"^\s*buenos\s+(?:dias|noches|tardes)\b",
    r"^\s*que\s+onda\b",
    r"^\s*holi\b",
]

PATRONES_TIEMPO_ENTRE = [
    r"cuanto (?:tiempo )?(?:se )?tarda(?:n)? (?:de|desde) (?P<a>.+?) (?:a|hasta|hacia) (?P<b>.+)",
    r"cuanto (?:tiempo )?(?:se )?tardo (?:de|desde) (?P<a>.+?) (?:a|hasta|hacia) (?P<b>.+)",
    r"cuanto (?:me )?(?:hago|tardo|demoro|me tardo) (?:de|desde) (?P<a>.+?) (?:a|hasta|hacia) (?P<b>.+)",
    r"cual es el (?:tiempo|tiepo) (?:de|entre|desde) (?P<a>.+?) (?:a|hasta|hacia) (?P<b>.+)",
    r"(?:de|desde) (?P<a>.+?) (?:a|hasta|hacia) (?P<b>.+?)\s*,?\s*cuanto",
    r"tiempo (?:de|entre) (?P<a>.+?) (?:a|y|hasta) (?P<b>.+)",
]


PATRONES_COMO_LLEGAR_CON_ORIGEN = [
    # ORDEN INVERTIDO (van primero, más específicos)
    r"como (?:llego|voy|puedo (?:ir|llegar)) a (?P<destino>.+?) (?:si )?estoy en (?P<origen>.+)",
    r"como (?:llego|voy|puedo ir) a (?P<destino>.+?) (?:desde|de) (?P<origen>.+)",
    r"(?:para|a|hacia) (?P<destino>.+?) (?:saliendo|partiendo) de (?P<origen>.+)",
    r"estoy en (?P<origen>.+?),\s*(?:como|ando)\s+(?:llego|voy|me voy) a (?P<destino>.+)",
    # ORDEN NORMAL
    r"como (?:le )?(?:hago )?(?:llego|voy|puedo ir) de (?P<origen>.+?) a (?P<destino>.+)",
    r"como (?:se )?llega de (?P<origen>.+?) a (?P<destino>.+)",
    r"que ruta (?:tomo|uso|agarro) (?:de|desde) (?P<origen>.+?) (?:para|a|hacia) (?P<destino>.+)",
    r"quiero (?:ir|llegar) de (?P<origen>.+?) a (?P<destino>.+)",
    r"como puedo llegar de (?P<origen>.+?) a (?P<destino>.+)",
    r"estoy en (?P<origen>.+?)\s+como (?:llego|voy) a (?P<destino>.+)",
    r"(?:necesito|debo) (?:ir|llegar) de (?P<origen>.+?) a (?P<destino>.+)",
    r"^de (?P<origen>.+?) a (?P<destino>.+)$",  
]

# Solo destino (se asume que el bot debe preguntar el origen).
PATRONES_COMO_LLEGAR = [
    # "¿Cómo llego a X?"
    r"como (?:llego|voy|puedo ir|me voy|le hago para llegar) a (?P<destino>.+)",  
    # "¿Qué ruta me lleva a X?"
    r"que ruta (?:me lleva|tomo|uso|agarro) a (?P<destino>.+)",
    # "Necesito/Quiero ir a X"
    r"(?:necesito|quiero|debo|tengo que) (?:ir|llegar) a (?P<destino>.+)",
    # "Por dónde llego a X?"
    r"por donde (?:llego|voy|me voy) a (?P<destino>.+)",
]

PATRONES_RUTA_DE = [
    r"^(?:ruta\s+)?(?P<ruta>\d+)\s*\??$",   # ruta standalone
    r"^(?P<ruta>\d+)\s*\??$",               # número solo
    r"(?:por )?donde pasa (?:la )?(?:ruta )?(?P<ruta>.+)",
    r"que paradas tiene (?:la )?(?:ruta )?(?P<ruta>.+)",
    r"cuales son las paradas de (?:la )?(?:ruta )?(?P<ruta>.+)",
    r"recorrido de (?:la )?(?:ruta )?(?P<ruta>.+)",
    r"cuales (?:son|pasa|tiene) (?:en )?(?:la )?(?:ruta )?(?P<ruta>.+)",
]

PATRONES_PARADA_CERCANA = [
    r"parada\s+(?:mas|más)?\s*cercana\s+(?:de|en|a)?\s*(?P<coords>[\d\.\-]+\s*,\s*[\d\.\-]+)",
    r"que parada (?:es )?(?:la )?(?:mas|más) (?:cercana|cerca) (?:a|de|en)?\s*(?P<coords>[\d\.\-]+\s*,\s*[\d\.\-]+)",
    r"cual es la parada (?:mas|más) (?:cercana|cerca)\s+(?:de|en|a)?\s*(?P<coords>[\d\.\-]+\s*,\s*[\d\.\-]+)",
    r"que parada (?:tengo )?cerca (?:de|en|a)?\s*(?P<coords>[\d\.\-]+\s*,\s*[\d\.\-]+)",
    r"dame (?:la )?parada (?:mas|más) (?:cercana|cerca) (?:a|de|en)?\s*(?P<coords>[\d\.\-]+\s*,\s*[\d\.\-]+)",
    r"cual es la parada (?:mas|más) (?:cercana|cerca) a (?:mi )?ubicacion\s*(?P<coords>[\d\.\-]+\s*,\s*[\d\.\-]+)",
    r"parada\s+(?:mas|más)?\s*(?:cercana|cerca)",
    r"que parada me queda cerca",
    r"cual es la parada (?:mas|más) (?:cercana|cerca)",
]

PATRONES_SALIDA = [
    r"^\s*sal(?:ir|te)?\b",
    r"^\s*adios\b",
    r"^\s*chao\b",
    r"^\s*fin\b",
    r"^\s*bye\b",
    r"^\s*gracias\b",
    r"(?:me )?quiero (?:salir|irme)(?!\s+a\s+)",
    r"(?:me )?quiero (?:irme de|salir de) aqui",
    r"(?:ya )?(?:quiero )?terminar",
    r"(?:necesito|debo) (?:irme|salir)",
]

def _normalizar(texto):
    texto = texto.strip().lower()
    reemplazos = str.maketrans("áéíóúñ", "aeioun")
    return texto.translate(reemplazos)


def _primer_match(patrones, texto):
    for patron in patrones:
        m = re.search(patron, texto)
        if m:
            return m
    return None


def interpretar(texto_usuario):
    """
    Clasifica el texto del usuario en una de las intenciones fijas:
      - "salir"
      - "saludo"                   ← AGREGADO
      - "tiempo_entre_A_y_B"      -> entidades: {"a":..., "b":...}
      - "como_llegar_de_A_a_B"    -> entidades: {"origen":..., "destino":...}
      - "como_llegar_a_X"         -> entidades: {"destino":...}
      - "ruta_de_X"               -> entidades: {"ruta":...}
      - "parada_mas_cercana"      -> entidades: {"coords":...}
      - "desconocida"             -> no hubo coincidencia (respuesta tipo ELIZA)
    
    Orden de verificación (prioridad):
    1. Salida (más importante)
    2. Tiempo entre paradas
    3. Cómo llegar con origen
    4. Cómo llegar sin origen
    5. Ruta de X
    6. Parada más cercana
    7. Saludo (simple)
    8. Desconocida 
    
    Regresa un dict: {"intencion": str, "entidades": dict}
    """
    texto = _normalizar(texto_usuario)
    
    if _primer_match(PATRONES_SALIDA, texto):
        return {"intencion": "salir", "entidades": {}}


    m = _primer_match(PATRONES_TIEMPO_ENTRE, texto)
    if m:
        return {
            "intencion": "tiempo_entre_A_y_B",
            "entidades": {"a": m.group("a").strip(), "b": m.group("b").strip()},
        }

    m = _primer_match(PATRONES_COMO_LLEGAR_CON_ORIGEN, texto)
    if m:
        return {
            "intencion": "como_llegar_de_A_a_B",
            "entidades": {
                "origen": m.group("origen").strip(),
                "destino": m.group("destino").strip(),
            },
        }

    m = _primer_match(PATRONES_COMO_LLEGAR, texto)
    if m:
        return {
            "intencion": "como_llegar_a_X",
            "entidades": {"destino": m.group("destino").strip()},
        }

    m = _primer_match(PATRONES_RUTA_DE, texto)
    if m:
        return {
            "intencion": "ruta_de_X",
            "entidades": {"ruta": m.group("ruta").strip()},
        }

    m = _primer_match(PATRONES_PARADA_CERCANA, texto)
    if m:
        coords = m.group("coords") if "coords" in m.groupdict() else None
        return {"intencion": "parada_mas_cercana", "entidades": {"coords": coords} if coords else {}}
    
    if _primer_match(PATRONES_SALUDO, texto):
        return {"intencion": "saludo", "entidades": {}}


    return {"intencion": "desconocida", "entidades": {}}


RESPUESTA_DEFECTO = (
    "No entendí, ¿puedes reformular tu pregunta sobre una ruta o parada? "
    "Por ejemplo: '¿cómo llego a Ingeniería?' o '¿cuánto tarda de Rectoría a Metro Universidad?'"
)
