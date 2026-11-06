"""Rutas del servicio Flask. Esqueleto intencionalmente incompleto."""
import io
import matplotlib
matplotlib.use("Agg")                      # sin ventana: genera imágenes en el servidor
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from flask import Flask, jsonify, render_template, send_file
from app.db import ping_db, obtener_estadisticas, obtener_ultimas_solicitudes


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def inicio():
        # TODO(ALUMNADO): El formulario se desarrolla en templates/index.html.
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        # Punto de salud proporcionado para verificar Compose y PostgreSQL.
        try:
            ping_db()
            return jsonify(servicio="citypilot", estado="ok", db="ok")
        except Exception:
            return jsonify(servicio="citypilot", estado="degradado", db="error"), 503

    @app.post("/planificar")
    def planificar_html():
        # TODO(ALUMNADO): leer y validar request.form; llamar a UN orquestador
        # compartido con /api/planificar; renderizar resultado.html.
        return "Pendiente: formulario -> integración -> resultado", 501

    @app.post("/api/planificar")
    def planificar_api():
        # TODO(ALUMNADO): leer JSON, usar EL MISMO orquestador y devolver JSON.
        # Nunca duplicar la lógica de datos externos en las dos rutas.
        return jsonify(error="Pendiente: API propia"), 501

    @app.get("/analitica")
    def analitica():
        try:
            stats = obtener_estadisticas()
            ultimas = obtener_ultimas_solicitudes(8)
            error = None
        except Exception:
            stats, ultimas = None, []
            error = "No se pudo consultar PostgreSQL."
        return render_template("analitica.html", stats=stats, ultimas=ultimas, error=error)

    @app.get("/analitica/grafico.png")
    def grafico():
        try:
            datos = obtener_estadisticas()["por_ciudad"]
        except Exception:
            return "No se pudo consultar PostgreSQL", 503
        fig, ax = plt.subplots(figsize=(6, 3.5))
        if datos:
            ax.bar([d["ciudad"] for d in datos], [d["peticiones"] for d in datos])
            ax.set_title("Peticiones por ciudad")
            ax.set_ylabel("Peticiones")
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            ax.tick_params(axis="x", rotation=30)
        else:
            ax.text(0.5, 0.5, "Sin datos todavía", ha="center", va="center")
            ax.axis("off")
        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120)
        plt.close(fig)
        buf.seek(0)
        return send_file(buf, mimetype="image/png", max_age=0)

    @app.get("/api/estadisticas")
    def estadisticas_api():
        try:
            return jsonify(obtener_estadisticas())
        except Exception:
            return jsonify(error="No se pudo consultar PostgreSQL"), 503

    return app


app = create_app()
