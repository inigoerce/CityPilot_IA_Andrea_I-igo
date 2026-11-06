"""Punto ÚNICO de integración para web y API JSON. Pendiente del alumnado."""
import time
from app import api_clients, db, llm

TIPOS_VALIDOS = {"cultural", "gastronomica", "naturaleza", "familiar"}
DURACIONES_VALIDAS = {2, 4, 6}


def procesar_solicitud(ciudad: str, tipo_turismo: str, duracion_horas: int, preferencias: str = "") -> dict:
    """TODO(ALUMNADO): implementar todo el recorrido.

    1) Validación (ciudad no vacía, tipo permitido, duración 2/4/6).
    2) Geocodificar la ciudad y consultar clima actual.
    3) Consultar lugares reales; si falla Overpass, utilizar fixture
       SOLAMENTE para demostrar flujo, marcando 'demo': True.
    4) Preparar el contexto y llamar a llm.generar_itinerario.
    5) Guardar entradas, respuestas, prompt, resultado, éxito/error,
       duración y el modo de datos en PostgreSQL.
    6) Devolver contrato consistente a ambas rutas Flask.

    Salida orientativa:
      {'ciudad': ..., 'tipo_turismo': ..., 'meteorologia': {...},
       'lugares': [...], 'itinerario': ..., 'modo_demo': False,
       'solicitud_id': 1}

    IMPORTANTE: ni el modelo ni los mocks son la fuente de lugares.
    Los datos de interés proceden de Overpass; el modelo los ORGANIZA.
    """
    inicio = time.perf_counter()

    if not ciudad or not ciudad.strip():
        raise ValueError("Debes introducir una ciudad.")

    if tipo_turismo not in TIPOS_VALIDOS:
        raise ValueError("El tipo de turismo no es válido.")

    if duracion_horas not in DURACIONES_VALIDAS:
        raise ValueError("La duración debe ser de 2, 4 o 6 horas.")

    preferencias = preferencias or ""

    ubicacion = api_clients.geocodificar(ciudad.strip())

    meteorologia = api_clients.obtener_meteorologia(
        ubicacion["lat"],
        ubicacion["lon"]
    )

    modo_demo = False

    try:
        lugares = api_clients.obtener_lugares(
            ubicacion["lat"],
            ubicacion["lon"],
            tipo_turismo
        )

        if not lugares:
            raise RuntimeError("No se han encontrado lugares.")

    except Exception:
        lugares = api_clients.cargar_fixture_lugares()
        modo_demo = True

    contexto = {
        "ciudad": ubicacion["ciudad"],
        "tipo_turismo": tipo_turismo,
        "duracion_horas": duracion_horas,
        "preferencias": preferencias,
        "meteorologia": meteorologia,
        "lugares": lugares
    }

    itinerario, prompt_usado = llm.generar_itinerario(contexto)

    duracion_ms = round((time.perf_counter() - inicio) * 1000)

    registro = {
        "ciudad": ubicacion["ciudad"],
        "pais": ubicacion["pais"],
        "tipo_turismo": tipo_turismo,
        "duracion_horas": duracion_horas,
        "preferencias": preferencias,
        "latitud": ubicacion["lat"],
        "longitud": ubicacion["lon"],
        "meteorologia": meteorologia,
        "lugares": lugares,
        "prompt_usado": prompt_usado,
        "itinerario": itinerario,
        "estado": "exito",
        "duracion_ms": duracion_ms,
        "error_resumido": None,
        "modo_demo": modo_demo,
        "modo_modelo": llm.LLM_MODE
    }

    solicitud_id = db.guardar_solicitud(registro)

    return {
        "ciudad": ubicacion["ciudad"],
        "pais": ubicacion["pais"],
        "tipo_turismo": tipo_turismo,
        "duracion_horas": duracion_horas,
        "preferencias": preferencias,
        "meteorologia": meteorologia,
        "lugares": lugares,
        "itinerario": itinerario,
        "modo_demo": modo_demo,
        "modo_modelo": llm.LLM_MODE,
        "solicitud_id": solicitud_id,
        "duracion_ms": duracion_ms
    }