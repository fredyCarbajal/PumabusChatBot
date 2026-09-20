# Chatbot de rutas Pumabús — Práctica 1

**Lugar y fecha:** Ciudad Universitaria, UNAM — septiembre de 2026
**Materia:** Agentes Conversacionales basados en reglas
**Integrantes del equipo:** _(completar)_

## Descripción

Chatbot de línea de comandos, basado 100% en reglas clásicas (regex, listas
de alias, if/else y el algoritmo de grafos Dijkstra vía `networkx`), que
responde preguntas sobre las rutas de Pumabús en CU:

- Por dónde pasa una ruta y sus paradas (`ruta_de_X`).
- Cuánto tarda un trayecto entre dos paradas (`tiempo_entre_A_y_B`).
- Cómo llegar a un destino (`como_llegar_a_X`).
- Cuál es la parada más cercana a una coordenada (Haversine).

No usa ningún modelo de lenguaje ni servicio de IA generativa.

## Requisitos

- Python 3.10+
- Dependencias en `requirements.txt` (solo `networkx`)

## Instalación

```bash
python -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

```bash
python chat/main.py
```

Ejemplos de preguntas:

```
¿Cómo llego a Ingeniería?
¿Cuánto tarda de Rectoría a Metro Universidad?
¿Por dónde pasa la ruta 1?
19.3302,-99.1836        (para buscar la parada más cercana a esas coordenadas)
salir
```

## Estructura del proyecto

```
datos/       -> rutas.json: base de conocimiento (rutas, paradas, alias, tiempos, coordenadas)
core/        -> cargar_datos.py (Fase 1), nucleo.py (Fase 2: Haversine, Dijkstra)
nlu/         -> interpretador.py (Fase 3: detección de intención por regex)
chat/        -> main.py (Fase 4: bucle de conversación por CLI)
```

## Estado de los datos

`datos/rutas.json` actualmente contiene **datos de ejemplo/placeholder**
(2 de las 13 rutas, con nombres reales de paradas pero coordenadas y
tiempos estimados). Falta:

1. Completar las 13 rutas con el orden real de paradas.
2. Verificar/corregir coordenadas (lat/lon) de cada parada.
3. Verificar tiempos reales entre paradas consecutivas.

Fuente oficial: mapas por ruta (R1–R13) en
https://www.dgsgm.unam.mx/pumabus.html
