import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main


def test_api_estadisticas_devuelve_json(monkeypatch):
    falso = {"total": 3, "ciudades_distintas": 2, "errores": 1,
             "por_ciudad": [{"ciudad": "Valencia", "peticiones": 2}], "por_tipo": []}
    monkeypatch.setattr(main, "obtener_estadisticas", lambda: falso)
    r = main.create_app().test_client().get("/api/estadisticas")
    assert r.status_code == 200
    assert r.get_json()["total"] == 3


def test_api_estadisticas_error_de_bd_da_503(monkeypatch):
    def falla():
        raise RuntimeError("sin base de datos")
    monkeypatch.setattr(main, "obtener_estadisticas", falla)
    r = main.create_app().test_client().get("/api/estadisticas")
    assert r.status_code == 503


def test_pagina_analitica_muestra_datos(monkeypatch):
    stats = {"total": 1, "ciudades_distintas": 1, "errores": 0,
             "por_ciudad": [{"ciudad": "PruebaDB", "peticiones": 1}],
             "por_tipo": [{"tipo_turismo": "cultural", "peticiones": 1}]}
    ultimas = [{"id": 1, "fecha": "2026-11-06 08:44", "ciudad": "PruebaDB",
                "tipo_turismo": "cultural", "duracion_horas": 4, "estado": "ok",
                "modo_demo": True, "modo_modelo": "mock", "duracion_ms": 10}]
    monkeypatch.setattr(main, "obtener_estadisticas", lambda: stats)
    monkeypatch.setattr(main, "obtener_ultimas_solicitudes", lambda limite=8: ultimas)
    r = main.create_app().test_client().get("/analitica")
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "PruebaDB" in html
    assert "DEMO" in html