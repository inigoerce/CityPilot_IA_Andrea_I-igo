"""Clientes HTTP de datos públicos. Se entregan los contratos, NO la solución."""
import json
import os
from pathlib import Path
import requests

GEO_URL = os.getenv("OPEN_METEO_GEO_URL", "https://geocoding-api.open-meteo.com/v1/search")
METEO_URL = os.getenv("OPEN_METEO_WEATHER_URL", "https://api.open-meteo.com/v1/forecast")
OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")


def geocodificar(ciudad: str) -> dict:
    """TODO(ALUMNADO).

    Entrada: 'Valencia'. Salida normalizada: {'ciudad': 'Valencia',
    'pais': 'España', 'lat': 39.47, 'lon': -0.38} (números ilustrativos).
    Usar Open-Meteo Geocoding y controlar búsqueda sin resultados.
    Restricción: peticiones con timeout, filtrando countryCode='ES' si se
    decide limitar a España.
    """
    params = {"name":ciudad,  "countryCode":"ES"}

    respuesta = requests.get(GEO_URL, params=params, timeout=8)
    respuesta.raise_for_status()

    datos = respuesta.json()
    resultados = datos.get("results", [])

    if not resultados:
        raise ValueError("No se ha encontrado la ciudad.")

    resultado = resultados[0]

    return {"ciudad": resultado["name"],
            "pais": resultado["country"],
            "lat": float(resultado["latitude"]),
            "lon":float(resultado["longitude"])}


def obtener_meteorologia(lat: float, lon: float) -> dict:
    """TODO(ALUMNADO).

    Devolver, como mínimo: temperatura_c, precipitacion_mm,
    codigo_tiempo, instante. Seleccionar current=temperature_2m,
    precipitation,weather_code e incluir timezone=auto.
    """
    params = {"latitude":lat,  "longitude":lon, "current":"temperature_2m,precipitation,weather_code", "timezone":"auto"}

    respuesta = requests.get(METEO_URL, params=params, timeout=8)
    respuesta.raise_for_status()

    datos = respuesta.json()
    actual = datos["current"]

    return {"temperatura_c": actual["temperature_2m"],
            "precipitacion_mm": actual["precipitation"],
            "codigo_tiempo": actual["weather_code"],
            "instante":actual["time"]}


FILTROS_POR_TIPO = {
    "cultural": {"tourism": ["museum", "attraction", "gallery"],
                 "historic": ["monument", "castle", "memorial"]},
    "gastronomica": {"amenity": ["restaurant", "cafe", "food_court"]},
    "naturaleza": {"leisure": ["park", "garden"]},
    "familiar": {"tourism": ["attraction", "zoo"],
                 "leisure": ["park", "playground"]},
}


def _construir_consulta(lat: float, lon: float, tipo: str, radio: int = 2500) -> str:
    filtros = FILTROS_POR_TIPO[tipo]
    lat, lon = float(lat), float(lon)   # fuerza números: nada de texto raro en la consulta
    lineas = []
    for clave, valores in filtros.items():
        patron = "|".join(valores)
        lineas.append(f'  nwr["{clave}"~"^({patron})$"]["name"](around:{radio},{lat},{lon});')
    return "[out:json][timeout:25];\n(\n" + "\n".join(lineas) + "\n);\nout center 60;"


def _categoria(tags: dict) -> str:
    for clave in ("tourism", "historic", "amenity", "leisure"):
        if tags.get(clave):
            return tags[clave]
    return "otro"


def obtener_lugares(lat: float, lon: float, tipo: str) -> list[dict]:
    if tipo not in FILTROS_POR_TIPO:
        raise ValueError(f"Tipo de turismo no válido: {tipo}")
    consulta = _construir_consulta(lat, lon, tipo)
    r = requests.post(OVERPASS_URL, data={"data": consulta}, timeout=30,
                      headers={"User-Agent": "CityPilotIA-clase/1.0"})
    r.raise_for_status()
    elementos = r.json().get("elements", [])

    lugares, vistos = [], set()
    for el in elementos:
        tags = el.get("tags", {})
        nombre = tags.get("name")
        if not nombre or nombre in vistos:
            continue
        if el.get("type") == "node":
            plat, plon = el.get("lat"), el.get("lon")
        else:                                   # way / relation: usan el centro
            centro = el.get("center") or {}
            plat, plon = centro.get("lat"), centro.get("lon")
        if plat is None or plon is None:
            continue
        vistos.add(nombre)
        lugares.append({"nombre": nombre, "categoria": _categoria(tags),
                        "lat": float(plat), "lon": float(plon),
                        "fuente": "OpenStreetMap", "demo": False})
        if len(lugares) >= 12:
            break
    return lugares


def cargar_fixture_lugares() -> list[dict]:
    """Utilidad entregada para simular Overpass durante pruebas sin Internet.

    Los lugares son FICTICIOS y deben identificarse como DEMO en la UI.
    """
    file_path = Path("/fixtures/puntos_demo.json")
    if not file_path.exists():
        file_path = Path(__file__).resolve().parents[2] / "fixtures/puntos_demo.json"
    return json.loads(file_path.read_text(encoding="utf-8"))["lugares"]
