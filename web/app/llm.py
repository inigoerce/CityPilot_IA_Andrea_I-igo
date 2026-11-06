"""Adaptador Cohere para generar itinerarios."""
import os
import requests

LLM_MODE = os.getenv("LLM_MODE", "mock").lower()
COHERE_MODEL = os.getenv("COHERE_MODEL", "command-r7b-12-2024")
COHERE_URL = "https://api.cohere.com/v2/chat"


def generar_itinerario(contexto: dict) -> tuple[str, str]:
    """Devuelve (texto_itinerario, prompt_usado)."""

    if LLM_MODE == "mock":
        return _simulador(contexto), "[SIMULADOR: sin llamada a modelo]"

    if LLM_MODE != "cohere":
        raise ValueError("LLM_MODE debe ser 'mock' o 'cohere'")

    api_key = os.getenv("COHERE_API_KEY", "")
    if not api_key:
        raise RuntimeError("Falta COHERE_API_KEY (pedirla al docente)")

    prompt = f"""
Eres un asistente especializado en turismo urbano.

Diseña un itinerario turístico en castellano utilizando exclusivamente
los lugares incluidos en los datos proporcionados.

DATOS DE LA SOLICITUD:
Ciudad: {contexto['ciudad']}
Tipo de turismo: {contexto['tipo_turismo']}
Duración: {contexto['duracion_horas']} horas
Preferencias: {contexto.get('preferencias', 'Sin preferencias adicionales')}
Meteorología actual: {contexto['meteorologia']}

LUGARES DISPONIBLES:
{contexto['lugares']}

INSTRUCCIONES:
1. Propón entre 3 y 5 paradas, siempre que haya suficientes lugares.
2. Utiliza exclusivamente los lugares de la lista proporcionada.
3. Adapta el orden y las recomendaciones al tipo de turismo y preferencias.
4. Ten en cuenta la meteorología, especialmente si hay precipitaciones.
5. Explica brevemente por qué recomiendas cada parada.
6. No inventes ubicaciones, horarios, eventos ni datos.
7. No afirmes que los establecimientos están abiertos.
8. Si no hay suficientes lugares, indícalo claramente.
9. Aclara que el orden es una sugerencia y no una ruta GPS verificada.

Presenta el resultado de forma clara y organizada.
""".strip()

    try:
        respuesta = requests.post(
            COHERE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": COHERE_MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
            },
            timeout=30,
        )

        respuesta.raise_for_status()
        datos = respuesta.json()

        contenido = datos["message"]["content"]
        texto = "\n".join(
            bloque["text"]
            for bloque in contenido
            if bloque.get("type") == "text"
        ).strip()

        if not texto:
            raise RuntimeError("Cohere ha devuelto una respuesta vacía")

        return texto, prompt

    except requests.Timeout as error:
        raise RuntimeError("Se agotó el tiempo de espera de Cohere") from error
    except requests.HTTPError as error:
        codigo = error.response.status_code
        if codigo == 401:
            raise RuntimeError("La clave de Cohere no es válida") from error
        if codigo == 429:
            raise RuntimeError("Se ha alcanzado el límite de peticiones de Cohere") from error
        raise RuntimeError(f"Error HTTP de Cohere: {codigo}") from error


def _simulador(contexto: dict) -> str:
    """Salida no generativa para pruebas."""
    lugares = contexto.get("lugares") or []
    ciudad = contexto.get("ciudad", "la ciudad")
    tipo = contexto.get("tipo_turismo", "libre")

    nombres = [x.get("nombre", "Lugar sin nombre") for x in lugares[:4]]
    visitas = "\n".join(
        f"{i}. {nombre}" for i, nombre in enumerate(nombres, 1)
    )

    if not visitas:
        visitas = "No hay lugares verificados disponibles."

    return (
        f"[MODO SIMULACIÓN - NO ES IA]\n"
        f"Plan {tipo} en {ciudad}:\n{visitas}"
    )