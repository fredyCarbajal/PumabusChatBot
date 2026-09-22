"""
Fase 4 - Capa de chat por línea de comandos.
Bucle: lee input -> Fase 3 (interpretar intención) -> Fase 2 (calcular) -> imprime.
"""

import sys
import os
import re
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cargar_datos import cargar_datos
from core.nucleo import tiempo_entre_paradas, mejor_ruta, parada_mas_cercana, paradas_de_ruta, rutas_por_parada
from nlu.interpretador import interpretar, RESPUESTA_DEFECTO


RESPUESTAS_SMALLTALK = (
    "Jaja, yo solo sé de rutas y paradas del Pumabús en CU pero con gusto te ayudo. "
    "Prueba con algo como '¿cómo llego a Medicina?' o 'estoy en Ingeniería, cómo llego a Rectoría'.",
    "Soy el chatbot de Pumabús, no tengo mucho que contar de mí, pero sí de rutas: "
    "pregúntame por ejemplo '¿qué ruta pasa por Ciencias Políticas?'.",
    "Puedo ayudarte con: cómo llegar de un lugar a otro, cuánto tarda un trayecto, "
    "qué paradas tiene una ruta, o qué ruta pasa por cierta parada. ¿Qué necesitas?",
)


def _respuesta_como_llegar(bd, nombre_origen, nombre_destino):
    """
    Arma la respuesta de trayecto (ruta directa o combinada) entre dos
    nombres YA resueltos (canónicos). Compartida entre "como_llegar_de_A_a_B"
    y "solo_origen" (cuando se completa un destino pendiente del contexto).
    """
    resultado = mejor_ruta(bd, nombre_origen, nombre_destino)
    if not resultado:
        return f"No encontré una forma de ir de {nombre_origen} a {nombre_destino} con los datos actuales."

    rutas_usadas = sorted({t["ruta_id"] for t in resultado["tramos"]})
    if len(rutas_usadas) == 1:
        lineas = [f"Toma la Ruta {rutas_usadas[0]} desde {nombre_origen} hasta {nombre_destino} (~{resultado['tiempo_total_min']} min):"]
        for i, parada in enumerate(resultado['paradas'], 1):
            lineas.append(f"  {i}. {parada}")
        return "\n".join(lineas)

    # Múltiples rutas: mostrar cada tramo con su ruta
    lineas = [f"De {nombre_origen} a {nombre_destino} (~{resultado['tiempo_total_min']} min):"]
    for tramo in resultado["tramos"]:
        lineas.append(f"  • Ruta {tramo['ruta_id']}: {tramo['de']} → {tramo['a']} ({tramo['minutos']} min)")
    return "\n".join(lineas)


def _parsear_hora_objetivo(texto_hora):
    """
    Interpreta un texto de hora tipo "3", "3:00", "15:00", "3 pm" y regresa
    el datetime FUTURO más cercano que corresponde (hoy si aún no pasa, o
    mañana si ya pasó). Si no viene "am"/"pm", se prueban ambas lecturas de
    12 horas y se elige la que quede más cerca en el futuro (ej. a las
    14:00 alguien dice "a las 3" casi seguro quiere decir 3pm, no 3am que
    ya pasó). Regresa None si no se pudo interpretar nada.
    """
    m = re.search(r"(?P<h>\d{1,2})(?::(?P<m>\d{2}))?\s*(?P<ampm>am|pm)?", texto_hora.strip().lower())
    if not m:
        return None
    hora = int(m.group("h"))
    minuto = int(m.group("m")) if m.group("m") else 0
    if hora > 23 or minuto > 59:
        return None
    ampm = m.group("ampm")
    ahora = datetime.datetime.now()

    if ampm == "am":
        candidatas_hora = [hora % 24]
    elif ampm == "pm":
        candidatas_hora = [(hora % 12) + 12]
    else:
        candidatas_hora = sorted({hora % 24, (hora % 12) + 12})

    objetivos = []
    for hh in candidatas_hora:
        objetivo = ahora.replace(hour=hh, minute=minuto, second=0, microsecond=0)
        if objetivo < ahora:
            objetivo += datetime.timedelta(days=1)
        objetivos.append((hh, objetivo))

    if ampm is None and len(objetivos) > 1:
        en_horario_tipico = [(hh, obj) for hh, obj in objetivos if 6 <= hh <= 22]
        if len(en_horario_tipico) == 1:
            return en_horario_tipico[0][1]

    return min((obj for _, obj in objetivos), key=lambda dt: dt - ahora)


def responder(bd, intencion, entidades, contexto, texto_original=None):
    """
    contexto: dict compartido entre turnos (ver main()). Guarda:
      - contexto["destino_pendiente"]: nombre canónico del destino cuando
        el bot preguntó "¿desde dónde partes?" y todavía no hay respuesta.
      - contexto["origen_recordado"]: nombre canónico del último origen
        que SÍ se resolvió con éxito, para poder responder preguntas de
        seguimiento tipo "¿y para X?" sin que el usuario repita de dónde
        parte.
    Es memoria de la última pregunta/origen, no un historial completo,
    pero cubre los encadenamientos más comunes en una conversación.
    """
    if intencion == "saludo":
        return "¡Hola! 👋 Soy el chatbot de Pumabús. ¿En qué puedo ayudarte? Pregúntame sobre rutas, paradas o tiempos de viaje en CU."

    if intencion == "smalltalk":
        import random
        return random.choice(RESPUESTAS_SMALLTALK)

    if intencion == "solo_origen":
        destino_pendiente = contexto.get("destino_pendiente")
        if not destino_pendiente:
            return RESPUESTA_DEFECTO
        nombre_origen, msg_o = _resolver_o_aclarar(bd, entidades["origen"])
        if msg_o:
            return msg_o
        contexto["destino_pendiente"] = None
        contexto["origen_recordado"] = nombre_origen
        return _respuesta_como_llegar(bd, nombre_origen, destino_pendiente)

    if intencion == "y_tambien_a_X":
        origen_recordado = contexto.get("origen_recordado")
        if not origen_recordado:
            return (
                "No tengo un punto de partida guardado todavía. "
                "Dime primero '¿cómo llego a X?' o 'de A a B'."
            )
        nombre_destino, msg_d = _resolver_o_aclarar(bd, entidades["destino"])
        if msg_d:
            return msg_d
        return _respuesta_como_llegar(bd, origen_recordado, nombre_destino)

    if intencion == "tiempo_entre_A_y_B":
        a, b = entidades["a"], entidades["b"]
        nombre_a, msg_a = _resolver_o_aclarar(bd, a)
        if msg_a:
            return msg_a
        nombre_b, msg_b = _resolver_o_aclarar(bd, b)
        if msg_b:
            return msg_b
        minutos, ruta_id = tiempo_entre_paradas(bd, nombre_a, nombre_b)
        if minutos is not None:
            return f"De {nombre_a} a {nombre_b} son aproximadamente {minutos} min por la Ruta {ruta_id}."
        resultado = mejor_ruta(bd, nombre_a, nombre_b)
        if resultado:
            return (
                f"No hay una ruta directa, pero combinando rutas tardarías "
                f"~{resultado['tiempo_total_min']} min: {' -> '.join(resultado['paradas'])}."
            )
        return f"No encontré una forma de ir de {nombre_a} a {nombre_b} con los datos actuales."

    if intencion == "como_llegar_de_A_a_B":
        origen, destino = entidades["origen"], entidades["destino"]
        nombre_origen, msg_o = _resolver_o_aclarar(bd, origen)
        if msg_o:
            return msg_o
        nombre_destino, msg_d = _resolver_o_aclarar(bd, destino)
        if msg_d:
            return msg_d
        contexto["destino_pendiente"] = None
        contexto["origen_recordado"] = nombre_origen
        return _respuesta_como_llegar(bd, nombre_origen, nombre_destino)

    if intencion == "como_llegar_a_X":
        destino = entidades["destino"]
        nombre_destino, msg_d = _resolver_o_aclarar(bd, destino)
        if msg_d:
            return msg_d
        # Se guarda el destino para poder completarlo si el usuario
        # responde solo con "desde X" en el siguiente turno.
        contexto["destino_pendiente"] = nombre_destino
        return (
            f"Para llegar a {nombre_destino} dime desde dónde partes, por ejemplo: "
            f"'desde Metro Universidad'."
        )

    if intencion == "llegada_a_tiempo":
        nombre_origen, msg_o = _resolver_o_aclarar(bd, entidades["origen"])
        if msg_o:
            return msg_o
        nombre_destino, msg_d = _resolver_o_aclarar(bd, entidades["destino"])
        if msg_d:
            return msg_d
        objetivo = _parsear_hora_objetivo(entidades["hora"])
        if objetivo is None:
            return "No entendí la hora. Dime algo como 'a las 3' o 'a las 15:00'."
        resultado = mejor_ruta(bd, nombre_origen, nombre_destino)
        if not resultado:
            return f"No encontré una forma de ir de {nombre_origen} a {nombre_destino} con los datos actuales."
        ahora = datetime.datetime.now()
        llegada_estimada = ahora + datetime.timedelta(minutes=resultado["tiempo_total_min"])
        if llegada_estimada <= objetivo:
            return (
                f"Sí llegas: de {nombre_origen} a {nombre_destino} son ~{resultado['tiempo_total_min']} min, "
                f"llegarías como a las {llegada_estimada:%H:%M}, antes de las {objetivo:%H:%M}."
            )
        return (
            f"No alcanzas: el trayecto tarda ~{resultado['tiempo_total_min']} min y llegarías "
            f"como a las {llegada_estimada:%H:%M} -- después de las {objetivo:%H:%M}. Más vale que salgas antes."
        )

    if intencion == "comparar_rutas":
        nombre_destino, msg_d = _resolver_o_aclarar(bd, entidades["destino"])
        if msg_d:
            return msg_d
        nombre_via1, msg_1 = _resolver_o_aclarar(bd, entidades["via1"])
        if msg_1:
            return msg_1
        nombre_via2, msg_2 = _resolver_o_aclarar(bd, entidades["via2"])
        if msg_2:
            return msg_2
        resultado1 = mejor_ruta(bd, nombre_via1, nombre_destino)
        resultado2 = mejor_ruta(bd, nombre_via2, nombre_destino)
        if not resultado1 and not resultado2:
            return f"No encontré cómo llegar a {nombre_destino} ni por {nombre_via1} ni por {nombre_via2}."
        if not resultado1:
            return f"No encontré ruta por {nombre_via1}, pero por {nombre_via2} tardarías ~{resultado2['tiempo_total_min']} min."
        if not resultado2:
            return f"No encontré ruta por {nombre_via2}, pero por {nombre_via1} tardarías ~{resultado1['tiempo_total_min']} min."
        t1, t2 = resultado1["tiempo_total_min"], resultado2["tiempo_total_min"]
        if t1 == t2:
            return f"Tardan lo mismo: ~{t1} min tanto por {nombre_via1} como por {nombre_via2}."
        mas_rapida, tiempo_rapida = (nombre_via1, t1) if t1 < t2 else (nombre_via2, t2)
        mas_lenta, tiempo_lenta = (nombre_via2, t2) if t1 < t2 else (nombre_via1, t1)
        return (
            f"Es más rápido por {mas_rapida} (~{tiempo_rapida} min) que por {mas_lenta} (~{tiempo_lenta} min) "
            f"para llegar a {nombre_destino}."
        )

    if intencion == "extremos_de_ruta_X":
        texto_ruta = entidades["ruta"]
        ruta_id = _extraer_numero_ruta(texto_ruta)
        if ruta_id is None or ruta_id not in bd.rutas:
            return f"No reconozco la ruta '{texto_ruta}'. Prueba con 'ruta 1', 'ruta 2', etc."
        paradas = paradas_de_ruta(bd, ruta_id)
        if not paradas:
            return f"No tengo paradas cargadas para la Ruta {ruta_id}."
        inicio, fin = paradas[0].nombre, paradas[-1].nombre
        if inicio == fin:
            return f"La Ruta {ruta_id} es un circuito: empieza y termina en {inicio}."
        return f"La Ruta {ruta_id} empieza en {inicio} y termina en {fin}."

    if intencion == "misma_ruta_dos_paradas":
        nombre1, msg1 = _resolver_o_aclarar(bd, entidades["parada1"])
        if msg1:
            return msg1
        nombre2, msg2 = _resolver_o_aclarar(bd, entidades["parada2"])
        if msg2:
            return msg2
        ids1 = set(rutas_por_parada(bd, nombre1))
        ids2 = set(rutas_por_parada(bd, nombre2))
        comunes = sorted(ids1 & ids2)
        if comunes:
            rutas_txt = ", ".join(f"Ruta {r}" for r in comunes)
            return f"Sí: {rutas_txt} pasan tanto por {nombre1} como por {nombre2}."
        return (
            f"No hay ninguna ruta directa que pase por ambas. "
            f"{nombre1} la sirven " + (", ".join(f"Ruta {r}" for r in sorted(ids1)) or "ninguna ruta") + "; "
            f"{nombre2} la sirven " + (", ".join(f"Ruta {r}" for r in sorted(ids2)) or "ninguna ruta") + ". "
            f"Puedes hacer transbordo -- pregúntame '¿cómo llego de {nombre1} a {nombre2}?'"
        )

    if intencion == "ruta_de_X":
        texto_ruta = entidades["ruta"]
        ruta_id = _extraer_numero_ruta(texto_ruta)
        if ruta_id is None or ruta_id not in bd.rutas:
            return f"No reconozco la ruta '{texto_ruta}'. Prueba con 'ruta 1', 'ruta 2', etc."
        paradas = paradas_de_ruta(bd, ruta_id)
        nombres = " -> ".join(p.nombre for p in paradas)
        return f"La Ruta {ruta_id} pasa por: {nombres}."

    if intencion == "que_rutas_por_X":
        texto_parada = entidades["parada"]
        nombre, msg = _resolver_o_aclarar(bd, texto_parada)
        if msg:
            return msg
        ids = rutas_por_parada(bd, nombre)
        if not ids:
            return f"No encontré ninguna ruta que pase por '{nombre}'."
        rutas_txt = ", ".join(f"Ruta {r}" for r in ids)
        return (
            f"Por {nombre} pasan: {rutas_txt}. "
            f"No tengo horarios exactos cronometrados todavía, pero esas son las rutas que puedes esperar ahí."
        )

    if intencion == "parada_mas_cercana":
        coords = entidades.get("coords")
        if coords:
            try:
                lat, lon = map(float, coords.replace(" ", "").split(","))
                parada, dist = parada_mas_cercana(bd, lat, lon)
                if parada is None:
                    return "Todavía no tengo coordenadas cargadas para ninguna parada."
                return f"La parada más cercana es '{parada.nombre}' a ~{dist:.0f} m."
            except (ValueError, IndexError):
                return "No entendí las coordenadas. Usa el formato: 'lat,lon' (ejemplo: 19.3302,-99.1836)"
        return (
            "Para encontrar tu parada más cercana necesito tu latitud y longitud. "
            "Escríbelas así: 'lat,lon' (ejemplo: 19.3302,-99.1836)."
        )

    if intencion == "desconocida" and texto_original:
        nombre, _ = bd.resolver_nombre_detallado(texto_original)
        if nombre:
            contexto["destino_pendiente"] = nombre
            return (
                f"Conozco '{nombre}'. ¿Qué quieres saber? Por ejemplo: "
                f"'¿cómo llego ahí?', 'desde dónde partes' (solo dime 'desde X'), "
                f"o '¿qué rutas pasan por ahí?'."
            )

    return RESPUESTA_DEFECTO


def _resolver_o_aclarar(bd, texto_parada):
    """
    Intenta resolver un nombre de parada. Regresa (nombre_canonico, None) si
    se pudo resolver sin ambigüedad, o (None, mensaje_para_el_usuario) si no
    se reconoció o si el texto es ambiguo entre varias paradas (en cuyo caso
    NO se adivina: se le pide al usuario que sea más específico).
    """
    nombre, candidatos_ambiguos = bd.resolver_nombre_detallado(texto_parada)
    if nombre:
        return nombre, None
    if candidatos_ambiguos:
        opciones = "', '".join(candidatos_ambiguos)
        return None, f"'{texto_parada}' es ambiguo, podría ser: '{opciones}'. ¿Cuál de esas quieres decir?"
    return None, f"No reconozco la parada '{texto_parada}'. ¿Puedes darme el nombre completo?"


def _extraer_numero_ruta(texto):
    digitos = "".join(ch for ch in texto if ch.isdigit())
    return int(digitos) if digitos else None


def main():
    print("=== Chatbot de rutas Pumabús (UNAM CU) ===")
    print("Escribe tu pregunta sobre rutas, paradas o tiempos. Escribe 'salir' para terminar.\n")

    try:
        bd = cargar_datos()
    except FileNotFoundError:
        print("Error: no se encontró datos/rutas.json. Verifica la ruta del archivo.")
        return
    except Exception as e:
        print(f"Error al cargar la base de conocimiento: {e}")
        return

    contexto = {"destino_pendiente": None, "origen_recordado": None}

    while True:
        try:
            texto = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nPumabús-bot: ¡Hasta luego!")
            break

        if not texto:
            continue

        # coordenadas directas para parada más cercana
        if "," in texto and all(_es_numero(p) for p in texto.split(",", 1)):
            lat_str, lon_str = texto.split(",", 1)
            parada, dist = parada_mas_cercana(bd, float(lat_str), float(lon_str))
            if parada is None:
                print("Pumabús-bot: Todavía no tengo coordenadas cargadas para ninguna parada.\n")
            else:
                print(f"Pumabús-bot: La parada más cercana es '{parada.nombre}' a ~{dist:.0f} m.\n")
            continue

        resultado = interpretar(texto)
        if resultado["intencion"] == "salir":
            print("Pumabús-bot: ¡Hasta luego!")
            break

        respuesta = responder(bd, resultado["intencion"], resultado["entidades"], contexto, texto_original=texto)
        print(f"Pumabús-bot: {respuesta}\n")


def _es_numero(texto):
    try:
        float(texto.strip())
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    main()
