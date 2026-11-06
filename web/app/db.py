"""Acceso a PostgreSQL: conexión, guardado de solicitudes y consultas de analítica."""
import os
from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.dialects.postgresql import JSONB

DATABASE_URL = os.environ.get("DATABASE_URL", "")
engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None


def ping_db():
    if engine is None:
        raise RuntimeError("Falta DATABASE_URL")
    with engine.connect() as conn:
        return conn.execute(text("SELECT 1")).scalar_one()


def guardar_solicitud(registro: dict) -> int:
    sql = text("""
        INSERT INTO solicitudes (
            ciudad, pais, tipo_turismo, duracion_horas, preferencias,
            latitud, longitud, meteorologia, lugares, prompt_usado, itinerario,
            modo_demo, modo_modelo, estado, duracion_ms, error_resumido)
        VALUES (
            :ciudad, :pais, :tipo_turismo, :duracion_horas, :preferencias,
            :latitud, :longitud, :meteorologia, :lugares, :prompt_usado, :itinerario,
            :modo_demo, :modo_modelo, :estado, :duracion_ms, :error_resumido)
        RETURNING id
    """).bindparams(bindparam("meteorologia", type_=JSONB),
                    bindparam("lugares", type_=JSONB))
    params = {
        "ciudad": registro["ciudad"],
        "pais": registro.get("pais"),
        "tipo_turismo": registro["tipo_turismo"],
        "duracion_horas": registro["duracion_horas"],
        "preferencias": registro.get("preferencias") or "",
        "latitud": registro.get("latitud"),
        "longitud": registro.get("longitud"),
        "meteorologia": registro.get("meteorologia") or {},
        "lugares": registro.get("lugares") or [],
        "prompt_usado": registro.get("prompt_usado"),
        "itinerario": registro.get("itinerario"),
        "modo_demo": bool(registro.get("modo_demo", False)),
        "modo_modelo": registro.get("modo_modelo"),
        "estado": registro.get("estado", "ok"),
        "duracion_ms": registro.get("duracion_ms"),
        "error_resumido": registro.get("error_resumido"),
    }
    with engine.begin() as conn:
        return conn.execute(sql, params).scalar_one()


def obtener_estadisticas() -> dict:
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM solicitudes")).scalar_one()
        ciudades = conn.execute(
            text("SELECT COUNT(DISTINCT ciudad) FROM solicitudes")).scalar_one()
        errores = conn.execute(
            text("SELECT COUNT(*) FROM solicitudes WHERE estado = 'error'")).scalar_one()
        por_ciudad = [dict(r._mapping) for r in conn.execute(text(
            "SELECT ciudad, COUNT(*) AS peticiones FROM solicitudes "
            "GROUP BY ciudad ORDER BY peticiones DESC, ciudad LIMIT 10"))]
        por_tipo = [dict(r._mapping) for r in conn.execute(text(
            "SELECT tipo_turismo, COUNT(*) AS peticiones FROM solicitudes "
            "GROUP BY tipo_turismo ORDER BY peticiones DESC, tipo_turismo"))]
    return {"total": total, "ciudades_distintas": ciudades, "errores": errores,
            "por_ciudad": por_ciudad, "por_tipo": por_tipo}


def obtener_ultimas_solicitudes(limite: int = 8) -> list[dict]:
    sql = text("""
        SELECT id, fecha, ciudad, tipo_turismo, duracion_horas, estado,
               modo_demo, modo_modelo, duracion_ms
        FROM solicitudes ORDER BY fecha DESC LIMIT :limite
    """)
    with engine.connect() as conn:
        filas = [dict(r._mapping) for r in conn.execute(sql, {"limite": limite})]
    for f in filas:
        f["fecha"] = f["fecha"].strftime("%Y-%m-%d %H:%M")
    return filas