# Chatbot de rutas Pumabús — Práctica 1

**Lugar y fecha:** Ciudad de México, UNAM — 21 de septiembre de 2026
**Materia:** Inteligencia Artificial
**Integrantes del equipo:** Quiroz Salazar Sergio

## Descripción

Chatbot de línea de comandos, basado 100% en reglas clásicas — expresiones
regulares, listas de alias, if/else y el algoritmo de grafos de Dijkstra vía
`networkx`, que ayuda a la comunidad de Ciudad Universitaria a planear sus trayectos en el transporte interno
Pumabús. Puede responder, entre otras cosas:

- Cómo llegar de un lugar a otro, con o sin origen indicado (`como_llegar_a_X`, `como_llegar_de_A_a_B`).
- Cuánto tarda un trayecto entre dos paradas (`tiempo_entre_A_y_B`).
- Qué paradas tiene una ruta y dónde empieza/termina (`ruta_de_X`, `extremos_de_ruta_X`).
- Qué rutas pasan por una parada, o por dos paradas a la vez (`que_rutas_por_X`, `misma_ruta_dos_paradas`).
- Cuál es la parada más cercana a unas coordenadas (fórmula de Haversine).
- Si es más rápido llegar por una vía u otra (`comparar_rutas`).
- Si se llega a tiempo saliendo ahora, antes de cierta hora (`llegada_a_tiempo`).
- Preguntas de seguimiento tipo "¿y para X?", reutilizando el origen de la pregunta anterior.

## Requisitos

- Python 3.10+
- Dependencias:
  - `networkx` (obligatoria — cálculo de la ruta más rápida con Dijkstra)
  - `rapidfuzz` (**opcional** — tolerancia a errores de dedo/variantes fonéticas, ej. "polakas" → "polacas". Si no está instalada, el chatbot funciona igual, solo sin esta ayuda extra)

## Instalación

```bash
python -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` debe incluir al menos:

```
networkx
rapidfuzz   # opcional
```

## Uso

```bash
python chat/main.py
```

Ejemplos de preguntas que entiende:

```
¿Cómo llego a Ingeniería?
Estoy en Rectoría
De Derecho a Ciencias
¿Y para Políticas?
¿Cuánto tarda de Metro Universidad a Ingeniería?
¿Qué paradas tiene la ruta 3?
¿Dónde termina la ruta 1?
¿Qué rutas pasan por Ciencias Políticas?
Es más rápido llegar a Rectoría por Derecho o por Odontología
Si salgo ahora de Ingeniería, llego a tiempo a Medicina antes de las 3
19.3302,-99.1836        (parada más cercana a esas coordenadas)
salir
```

Escribe `salir` (o `adiós`, `gracias`, etc.) para terminar la sesión.

## Estructura del proyecto

```
datos/       -> rutas.json: base de conocimiento (13 rutas, paradas, alias, tiempos, coordenadas)
              -> catalogo_paradas.json: catálogo de referencia de nombres/alias de paradas
core/        -> cargar_datos.py (Fase 1: carga y resolución de nombres/alias)
              -> nucleo.py (Fase 2: Haversine, construcción de grafo, Dijkstra)
nlu/         -> interpretador.py (Fase 3: detección de intención por regex — 15+ intenciones, 60+ patrones)
chat/        -> main.py (Fase 4: bucle de conversación por CLI, contexto de sesión)
```

## Estado de los datos

`datos/rutas.json` contiene las **13 rutas completas** de Pumabús, con
paradas en orden y alias/apodos comunes para cada una. Sobre las
coordenadas y tiempos:

- **Coordenadas:** ~48 lugares principales (facultades, institutos, museos,
  etc.) tienen coordenadas reales obtenidas de Google Places. Estacionamientos,
  pistas, accesos y algunos nodos internos sin entrada propia en Google Maps
  quedan sin coordenadas (`null`).
- **Tiempos entre paradas:** se modelaron con distancia Haversine dividida
  entre una velocidad promedio estimada de 12 km/h dentro de CU — **no son
  tiempos medidos en campo**. Donde falta alguna coordenada se usa un
  placeholder de 2 minutos.


Fuente oficial de referencia: mapas por ruta (R1–R13) en
https://www.dgsgm.unam.mx/pumabus.html
