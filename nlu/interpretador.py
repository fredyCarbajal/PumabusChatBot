"""
Fase 3 - Interpretación de preguntas mediante reglas.
Solo expresiones regulares y listas de alias
(estas últimas ya cargadas en la BaseDeConocimiento desde datos/rutas.json).
"""

import re

_EMOJI_PATRON = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002B00-\U00002BFF"
    "]+",
    flags=re.UNICODE,
)

PATRONES_SALUDO = [
    r"^\s*hola\b",
    r"^\s*hey\b",
    r"^\s*buenos\s+(?:dias|noches|tardes)\b",
    r"^\s*que\s+onda\b",
    r"^\s*holi\b",
    r"^\s*buenas\b",
    r"^\s*hi\b",
    r"^\s*ola\b",
    r"^\s*saludos\b",
]

# Charla casual 
PATRONES_SMALLTALK = [
    r"como\s+(?:estas|andas|te va|vas|te encuentras)\b",
    r"que\s+tal\b",
    r"todo\s+bien\b",
    r"como\s+te\s+llamas\b",
    r"cual\s+es\s+tu\s+nombre\b",
    r"quien\s+eres\b",
    r"que\s+(?:eres|haces)\b",
    r"eres\s+(?:un\s+)?(?:bot|robot|ia|chatbot)\b",
    r"jaja+\b",
    r"jeje+\b",
    r"^\s*ok(?:ay)?\s*$",
    r"^\s*(?:va|vale)\s*$",
    r"que\s+puedes\s+hacer\b",
    r"(?:me\s+)?(?:puedes|podrias)\s+ayudar\b",
    r"^\s*(?:si|no)\s*$",
    r"no\s+entiendo\b",
    r"no\s+se\b",
]

PATRONES_TIEMPO_ENTRE = [
    r"cuanto (?:tiempo )?(?:se )?tarda(?:n)? (?:de|desde) (?P<a>.+?) (?:a|hasta|hacia) (?P<b>.+)",
    r"cuanto (?:tiempo )?(?:se )?tardo (?:de|desde) (?P<a>.+?) (?:a|hasta|hacia) (?P<b>.+)",
    r"cuanto (?:me )?(?:hago|tardo|demoro|me tardo) (?:de|desde) (?P<a>.+?) (?:a|hasta|hacia) (?P<b>.+)",
    r"cual es el (?:tiempo|tiepo) (?:de|entre|desde) (?P<a>.+?) (?:a|hasta|hacia) (?P<b>.+)",
    r"(?:de|desde) (?P<a>.+?) (?:a|hasta|hacia) (?P<b>.+?)\s*,?\s*cuanto",
    r"tiempo (?:de|entre) (?P<a>.+?) (?:a|y|hasta) (?P<b>.+)",
    r"en cuanto (?:tiempo )?llego (?:de|desde) (?P<a>.+?) (?:a|hasta|hacia) (?P<b>.+)",
    r"que tan lejos (?:esta|queda) (?P<b>.+?) (?:de|desde) (?P<a>.+)",
    r"que tan retirado (?:esta|queda) (?P<b>.+?) (?:de|desde) (?P<a>.+)",
    r"que tan cerca (?:esta|queda) (?P<b>.+?) (?:de|desde) (?P<a>.+)",
]


PATRONES_COMO_LLEGAR_CON_ORIGEN = [
    # ORDEN INVERTIDO
    r"como (?:llego|voy|puedo (?:ir|llegar)) a (?P<destino>.+?) (?:si )?estoy en (?P<origen>.+)",
    r"como (?:llego|voy|puedo ir) a (?P<destino>.+?) (?:desde|de) (?P<origen>.+)",
    r"(?:para|a|hacia) (?P<destino>.+?) (?:saliendo|partiendo) de (?P<origen>.+)",
    r"(?:estoy|ando|me encuentro) en (?P<origen>.+?),?\s*(?:como|ando)\s+(?:llego|voy|me voy|le hago(?: para llegar)?) a (?P<destino>.+)",
    r"(?:estoy|ando|me encuentro) en (?P<origen>.+?),\s*(?:necesito|quiero|debo|tengo que) (?:ir|llegar) a (?P<destino>.+)",
    r"(?:estoy|ando) en (?P<origen>.+?)\s+(?:y\s+)?(?:necesito|quiero|debo|tengo que|como)\s+(?:ir|llegar)?\s*a (?P<destino>.+)",
    # ORDEN NORMAL
    r"como (?:le )?(?:hago )?(?:llego|voy|puedo ir) de (?P<origen>.+?) a (?P<destino>.+)",
    r"como (?:se )?llega de (?P<origen>.+?) a (?P<destino>.+)",
    r"que ruta (?:tomo|uso|agarro) (?:de|desde) (?P<origen>.+?) (?:para|a|hacia) (?P<destino>.+)",
    r"quiero (?:ir|llegar) de (?P<origen>.+?) a (?P<destino>.+)",
    r"voy de (?P<origen>.+?) a (?P<destino>.+)",
    r"como puedo llegar de (?P<origen>.+?) a (?P<destino>.+)",
    r"(?:estoy|ando) en (?P<origen>.+?)\s+como (?:llego|voy) a (?P<destino>.+)",
    r"(?:necesito|debo) (?:ir|llegar) de (?P<origen>.+?) a (?P<destino>.+)",
    r"cual es la ruta mas rapida de (?P<origen>.+?) a (?P<destino>.+)",
    r"que (?:camion|combi) (?:tomo|agarro) de (?P<origen>.+?) a (?P<destino>.+)",
    # Cambio de opinión: "no, mejor de X a Y"
    r"no,? mejor de (?P<origen>.+?) a (?P<destino>.+)",
    r"^de (?P<origen>.+?) a (?P<destino>.+)$",
]

# Solo destino
PATRONES_COMO_LLEGAR = [
    # "¿Cómo llego a X?"
    r"como (?:llego|voy|puedo ir|me voy|le hago para llegar) a (?P<destino>.+)",
    # "¿Qué ruta me lleva a X?"
    r"que ruta (?:me lleva|tomo|uso|agarro) a (?P<destino>.+)",
    # "Necesito/Quiero ir a X"
    r"(?:necesito|quiero|debo|tengo que) (?:ir|llegar) a (?P<destino>.+)",
    # "Por dónde llego a X?"
    r"por donde (?:llego|voy|me voy) a (?P<destino>.+)",
    # "¿Qué camión/combi me sirve/lleva a X?"
    r"que (?:camion|combi|pumabus) (?:me lleva|me sirve|tomo|agarro) (?:para (?:ir|llegar) )?a (?P<destino>.+)",
    # "¿Cuál es la ruta más rápida a X?"
    r"cual es la ruta mas rapida a (?P<destino>.+)",
    # "Por dónde me conviene ir a X"
    r"por donde me conviene ir a (?P<destino>.+)",
    # "Ando perdido, cómo llego a X"
    r"ando perdido,? como llego a (?P<destino>.+)",
]

PATRONES_RUTA_DE = [
    r"^(?:ruta\s+)?(?P<ruta>\d+)\s*\??$",   # ruta standalone
    r"^(?P<ruta>\d+)\s*\??$",               # número solo
    r"(?:por )?donde pasa (?:la )?(?:ruta )?(?P<ruta>\d+)",
    r"que paradas tiene (?:la )?(?:ruta )?(?P<ruta>\d+)",
    r"cuales son las paradas de (?:la )?(?:ruta )?(?P<ruta>\d+)",
    # "recorrido de la ruta 1", "recorrido completo/total/detallado de la ruta 1"
    r"recorrido(?:s)? (?:completo |total |detallado )?de (?:la )?(?:ruta )?(?P<ruta>\d+)",
    # variante genérica por si hay más palabras de relleno entre medio
    r"recorrido.*?ruta\s*(?P<ruta>\d+)",
    r"cuales (?:son|pasa|tiene) (?:en )?(?:la )?(?:ruta )?(?P<ruta>\d+)",
    r"informacion (?:de|sobre) (?:la )?ruta (?P<ruta>\d+)",
    r"detalles? de (?:la )?ruta (?P<ruta>\d+)",
    r"dime (?:el recorrido|las paradas) de (?:la )?ruta (?P<ruta>\d+)",
]

# "¿Cuál es la última parada de la ruta X?"
PATRONES_EXTREMOS_RUTA = [
    r"(?:cual es la )?(?:ultima parada|parada final|terminal) de (?:la )?(?:ruta )?(?P<ruta>\d+)",
    r"donde (?:termina|acaba) (?:la )?(?:ruta )?(?P<ruta>\d+)",
    r"cual es (?:el )?(?:punto final|destino final) de (?:la )?(?:ruta )?(?P<ruta>\d+)",
    r"(?:cual es la )?primera parada de (?:la )?(?:ruta )?(?P<ruta>\d+)",
    r"donde (?:empieza|comienza|inicia) (?:la )?(?:ruta )?(?P<ruta>\d+)",
    r"de donde sale (?:la )?(?:ruta )?(?P<ruta>\d+)",
]

# "¿A qué hora pasa el puma/pumabús de X?", "¿qué ruta pasa por X?"
PATRONES_QUE_RUTA_PASA = [
    r"a que hora (?:pasa|llega|sale) (?:el|la) (?:puma|pumabus|camion|bus|combi)(?:\s+de)? (?P<parada>.+)",
    r"cuando (?:pasa|llega) (?:el|la) (?:puma|pumabus|camion|bus) (?:de|en|por) (?P<parada>.+)",
    r"que (?:puma|pumabus|camion|bus|ruta) pasa (?:por|en) (?P<parada>.+)",
    r"que rutas? (?:pasan|hay|sirven) (?:por|en) (?P<parada>.+)",
    r"(?:el|la) (?:puma|pumabus) (?:de|en) (?P<parada>.+?) a que hora pasa",
    r"a que hora (?:es|hay) (?:el|la|un) (?:puma|pumabus|camion|bus) (?:en|de|por) (?P<parada>.+)",
]

# "¿Pasan por X y por Y la misma ruta?"
PATRONES_MISMA_RUTA = [
    r"(?:pasan|pasa) (?:por )?(?P<parada1>.+?) y (?:por )?(?P<parada2>.+?) (?:por )?la misma ruta",
    r"(?:hay|existe) alguna ruta que pase por (?P<parada1>.+?) y (?:por )?(?P<parada2>.+)",
    r"la (?:misma )?ruta (?:que )?pasa por (?P<parada1>.+?) y (?:por )?(?P<parada2>.+)",
]

# "¿Es más rápido llegar a X por A o por B?" 
PATRONES_COMPARAR_RUTAS = [
    r"es mas rapido (?:llegar a |ir a )?(?P<destino>.+?) por (?P<via1>.+?) o por (?P<via2>.+)",
    r"que es mas rapido,? (?:ir )?por (?P<via1>.+?) o por (?P<via2>.+?) para llegar a (?P<destino>.+)",
    r"conviene mas ir por (?P<via1>.+?) o por (?P<via2>.+?) (?:para llegar )?a (?P<destino>.+)",
]

# "Si salgo ahora de X, ¿llego a tiempo a Y (antes de/para) las 3?"
PATRONES_LLEGADA_A_TIEMPO = [
    r"si salgo(?: ahora| ahorita)? de (?P<origen>.+?),? (?:llego|alcanzo|logro llegar) a tiempo a (?P<destino>.+?) (?:antes de las|para las|a las)\s*(?P<hora>[\d: ]+(?:am|pm)?)",
    r"si salgo(?: ahora| ahorita)? de (?P<origen>.+?),? (?:llego|alcanzo) a (?P<destino>.+?) (?:antes de las|para las|a las)\s*(?P<hora>[\d: ]+(?:am|pm)?)",
    r"si me voy(?: ahora| ahorita)? de (?P<origen>.+?),? (?:llego|alcanzo) a (?P<destino>.+?) (?:antes de las|para las|a las)\s*(?P<hora>[\d: ]+(?:am|pm)?)",
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

# Pregunta de seguimiento tipo "¿y para X?" / "¿y a X?" 
PATRONES_MISMO_ORIGEN_OTRO_DESTINO = [
    r"^y (?:a|para|hacia|hasta) (?P<destino>.+)$",
    r"^y (?:que tal|como llego) (?:a |para )(?P<destino>.+)$",
    r"^oye,? y (?:a|para|hacia) (?P<destino>.+)$",
    r"^tambien (?:quiero|necesito) ir a (?P<destino>.+)$",
    # Cambio de opinión sin repetir el origen: "no, mejor a X"
    r"^no,? mejor (?:a|hacia|para) (?P<destino>.+)$",
    r"^no,? mejor (?:quiero ir|voy) a (?P<destino>.+)$",
]

# Respuesta corta a "¿desde dónde partes?" 
PATRONES_SOLO_ORIGEN = [
    r"^desde (?P<origen>.+)$",
    r"^partiendo de (?P<origen>.+)$",
    r"^saliendo de (?P<origen>.+)$",
    r"^(?:estoy|ando|me encuentro) en (?P<origen>.+)$",
    r"^de (?P<origen>.+)$",
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
    texto = _EMOJI_PATRON.sub(" ", texto)
    texto = texto.strip().lower()
    # quitar signos de interrogación o exclamación, no afectan al sentido
    texto = re.sub(r"[¿?¡!]", "", texto)
    reemplazos = str.maketrans("áéíóúñ", "aeioun")
    texto = texto.translate(reemplazos)
    # colapsar espacios que pudieron quedar dobles tras quitar emojis
    return re.sub(r"\s+", " ", texto).strip()


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
      - "saludo"
      - "smalltalk"                ← charla casual, no pide ruta
      - "tiempo_entre_A_y_B"      -> entidades: {"a":..., "b":...}
      - "como_llegar_de_A_a_B"    -> entidades: {"origen":..., "destino":...}
      - "como_llegar_a_X"         -> entidades: {"destino":...}
      - "ruta_de_X"               -> entidades: {"ruta":...}
      - "que_rutas_por_X"          ← -> entidades: {"parada":...}
      - "parada_mas_cercana"      -> entidades: {"coords":...}
      - "solo_origen"             ← -> entidades: {"origen":...} (respuesta
        corta tipo "desde X"; solo tiene sentido si chat/main.py tenía un
        destino pendiente guardado en su contexto de conversación)
      - "y_tambien_a_X"           ← -> entidades: {"destino":...} (pregunta
        de seguimiento tipo "¿y para X?" o cambio de opinión "no, mejor a
        X"; reutiliza el ORIGEN recordado de la pregunta anterior)
      - "llegada_a_tiempo"        ← -> entidades: {"origen","destino","hora"}
        ("si salgo ahora de X, llego a tiempo a Y antes de las 3?")
      - "comparar_rutas"          ← -> entidades: {"destino","via1","via2"}
        ("¿es más rápido llegar a X por A o por B?")
      - "extremos_de_ruta_X"      ← -> entidades: {"ruta":...} (inicio/fin
        de una ruta: "¿dónde termina la ruta 1?", "primera parada de...")
      - "misma_ruta_dos_paradas"  ← -> entidades: {"parada1","parada2"}
        ("¿pasan por X y por Y la misma ruta?")
      - "desconocida"             -> no hubo coincidencia (respuesta tipo ELIZA)

    Orden de verificación (prioridad):
    1. Salida (más importante)
    2. Tiempo entre paradas
    3. Cómo llegar con origen
    4. Cómo llegar sin origen
    5. Ruta de X
    6. Qué rutas pasan por X / a qué hora pasa
    7. Parada más cercana
    8. Seguimiento ("y para X")
    9. Solo origen ("desde X")
    10. Saludo (simple)
    11. Smalltalk
    12. Desconocida

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

    m = _primer_match(PATRONES_LLEGADA_A_TIEMPO, texto)
    if m:
        return {
            "intencion": "llegada_a_tiempo",
            "entidades": {
                "origen": m.group("origen").strip(),
                "destino": m.group("destino").strip(),
                "hora": m.group("hora").strip(),
            },
        }

    m = _primer_match(PATRONES_COMPARAR_RUTAS, texto)
    if m:
        return {
            "intencion": "comparar_rutas",
            "entidades": {
                "destino": m.group("destino").strip(),
                "via1": m.group("via1").strip(),
                "via2": m.group("via2").strip(),
            },
        }

    m = _primer_match(PATRONES_EXTREMOS_RUTA, texto)
    if m:
        return {
            "intencion": "extremos_de_ruta_X",
            "entidades": {"ruta": m.group("ruta").strip()},
        }

    m = _primer_match(PATRONES_RUTA_DE, texto)
    if m:
        return {
            "intencion": "ruta_de_X",
            "entidades": {"ruta": m.group("ruta").strip()},
        }

    m = _primer_match(PATRONES_MISMA_RUTA, texto)
    if m:
        return {
            "intencion": "misma_ruta_dos_paradas",
            "entidades": {
                "parada1": m.group("parada1").strip(),
                "parada2": m.group("parada2").strip(),
            },
        }

    m = _primer_match(PATRONES_QUE_RUTA_PASA, texto)
    if m:
        return {
            "intencion": "que_rutas_por_X",
            "entidades": {"parada": m.group("parada").strip()},
        }

    m = _primer_match(PATRONES_PARADA_CERCANA, texto)
    if m:
        coords = m.group("coords") if "coords" in m.groupdict() else None
        return {"intencion": "parada_mas_cercana", "entidades": {"coords": coords} if coords else {}}

    m = _primer_match(PATRONES_MISMO_ORIGEN_OTRO_DESTINO, texto)
    if m:
        return {"intencion": "y_tambien_a_X", "entidades": {"destino": m.group("destino").strip()}}

    m = _primer_match(PATRONES_SOLO_ORIGEN, texto)
    if m:
        return {"intencion": "solo_origen", "entidades": {"origen": m.group("origen").strip()}}

    if _primer_match(PATRONES_SALUDO, texto):
        return {"intencion": "saludo", "entidades": {}}

    if _primer_match(PATRONES_SMALLTALK, texto):
        return {"intencion": "smalltalk", "entidades": {}}

    return {"intencion": "desconocida", "entidades": {}}


RESPUESTA_DEFECTO = (
    "No entendí, ¿puedes reformular tu pregunta sobre una ruta o parada? "
    "Por ejemplo: '¿cómo llego a Ingeniería?' o '¿cuánto tarda de Rectoría a Metro Universidad?'"
)
