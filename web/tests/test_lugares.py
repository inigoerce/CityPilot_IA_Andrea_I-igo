import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import api_clients


class FakeResp:
    def __init__(self, data): self.data = data
    def raise_for_status(self): pass
    def json(self): return self.data


def test_normaliza_y_descarta_sin_nombre(monkeypatch):
    falso = {"elements": [
        {"type": "node", "lat": 39.47, "lon": -0.37, "tags": {"name": "Museo A", "tourism": "museum"}},
        {"type": "way", "center": {"lat": 39.48, "lon": -0.36}, "tags": {"name": "Castillo B", "historic": "castle"}},
        {"type": "node", "lat": 39.4, "lon": -0.3, "tags": {"tourism": "museum"}},
    ]}
    monkeypatch.setattr(api_clients.requests, "post", lambda *a, **k: FakeResp(falso))
    lugares = api_clients.obtener_lugares(39.47, -0.38, "cultural")
    assert [l["nombre"] for l in lugares] == ["Museo A", "Castillo B"]
    assert all(l["fuente"] == "OpenStreetMap" and l["demo"] is False for l in lugares)


def test_tipo_invalido():
    with pytest.raises(ValueError):
        api_clients.obtener_lugares(39.47, -0.38, "espacial")