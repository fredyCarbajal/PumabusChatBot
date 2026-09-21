"""
Fase 4 - Capa de chat por línea de comandos.
Bucle: lee input -> Fase 3 (interpretar intención) -> Fase 2 (calcular) -> imprime.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cargar_datos import cargar_datos
from core.nucleo import tiempo_entre_paradas, mejor_ruta, parada_mas_cercana, paradas_de_ruta, rutas_por_parada
from nlu.interpretador import interpretar, RESPUESTA_DEFECTO


RESPUESTAS_SMALLTALK = (
    "Jaja, yo solo sé de rutas y paradas del Pumabús en CU 🚌 pero con gusto te ayudo. "
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


def responder(bd, intencion, entidades, contexto):
    """
    contexto: dict compartido entre turnos (ver main()). Por ahora solo
    guarda contexto["destino_pendiente"]: el nombre canónico del destino
    cuando el bot preguntó "¿desde dónde partes?" y todavía no hay
    respuesta. Es memoria de UNA sola pregunta pendiente, no historial
    completo -- suficiente para "como llego a X" -> "desde Y".
    """
    if intencion == "saludo":
        return "¡Hola! 👋 Soy el chatbot de Pumabús. ¿En qué puedo ayudarte? Pregúntame sobre rutas, paradas o tiempos de viaje en CU."

    if intencion == "smalltalk":
        # Sin IA generativa: solo un pool fijo de respuestas amables que
        # redirigen hacia lo que el bot sí sabe hacer.
        import random
        return random.choice(RESPUESTAS_SMALLTALK)

    if intencion == "solo_origen":
        destino_pendiente = contexto.get("destino_pendiente")
        if not destino_pendiente:
            # No hay pregunta pendiente que completar: no adivinamos.
            return RESPUESTA_DEFECTO
        nombre_origen, msg_o = _resolver_o_aclarar(bd, entidades["origen"])
        if msg_o:
            # Seguimos esperando el origen: NO se borra el contexto.
            return msg_o
        contexto["destino_pendiente"] = None
        return _respuesta_como_llegar(bd, nombre_origen, destino_pendiente)

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

    # Contexto de conversación: memoria de UNA sola pregunta pendiente
    # (el destino, cuando el bot preguntó "¿desde dónde partes?"). Vive
    # mientras dure la sesión de chat, se pasa por referencia a responder().
    contexto = {"destino_pendiente": None}

    while True:
        try:
            texto = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nPumabús-bot: ¡Hasta luego!")
            break

        if not texto:
            continue

        # atajo: coordenadas directas para parada más cercana
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

        respuesta = responder(bd, resultado["intencion"], resultado["entidades"], contexto)
        print(f"Pumabús-bot: {respuesta}\n")


def _es_numero(texto):
    try:
        float(texto.strip())
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    main()
