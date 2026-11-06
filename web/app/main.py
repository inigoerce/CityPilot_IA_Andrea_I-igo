"""Rutas del servicio Flask."""
from flask import Flask, jsonify, render_template, request, send_file
from app.db import ping_db


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def inicio():
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
        from app.orchestrator import procesar_solicitud

        try:
            ciudad = request.form.get("ciudad", "")
            tipo_turismo = request.form.get("tipo_turismo", "")
            duracion_horas = int(request.form.get("duracion_horas", 0))
            preferencias = request.form.get("preferencias", "")

            resultado = procesar_solicitud(
                ciudad,
                tipo_turismo,
                duracion_horas,
                preferencias
            )

            return render_template("resultado.html", resultado=resultado)

        except ValueError as error:
            return render_template("resultado.html", error=str(error)), 400
        except Exception:
            return render_template(
                "resultado.html",
                error="No se ha podido generar el itinerario. Inténtalo de nuevo."
            ), 500

    @app.post("/api/planificar")

    def planificar_api():
        from app.orchestrator import procesar_solicitud

        datos = request.get_json(silent=True) or {}

        try:
            resultado = procesar_solicitud(
                datos.get("ciudad", ""),
                datos.get("tipo_turismo", ""),
                int(datos.get("duracion_horas", 0)),
                datos.get("preferencias", "")
            )
            return jsonify(resultado)

        except ValueError as error:
            return jsonify(error=str(error)), 400
        except Exception:
            return jsonify(
                error="No se ha podido generar el itinerario."
            ), 500

    @app.get("/analitica")
    def analitica():
        from app.db import obtener_estadisticas, obtener_ultimas_solicitudes

        try:
            totales = obtener_estadisticas()
            ultimas = obtener_ultimas_solicitudes(8)

            return render_template(
                "analitica.html",
                totales=totales,
                top_ciudades=totales.get("top_ciudades", []),
                ultimas=ultimas
            )
        except Exception:
            return render_template(
                "analitica.html",
                totales=None,
                top_ciudades=[],
                ultimas=[],
                error="No se han podido cargar las estadísticas."
            ), 500

    @app.get("/analitica/grafico.png")
    def grafico():
        from io import BytesIO
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from app.db import obtener_estadisticas

        estadisticas = obtener_estadisticas()
        ciudades = estadisticas.get("top_ciudades", [])

        nombres = [item["ciudad"] for item in ciudades]
        cantidades = [item["total"] for item in ciudades]

        figura, eje = plt.subplots()
        eje.bar(nombres, cantidades)
        eje.set_title("Solicitudes por ciudad")
        eje.set_xlabel("Ciudad")
        eje.set_ylabel("Número de solicitudes")
        figura.tight_layout()

        imagen = BytesIO()
        figura.savefig(imagen, format="png")
        imagen.seek(0)
        plt.close(figura)

        return send_file(imagen, mimetype="image/png")

    @app.get("/api/estadisticas")
    def estadisticas_api():
        from app.db import obtener_estadisticas

        try:
            estadisticas = obtener_estadisticas()
            return jsonify(estadisticas)
        except Exception:
            return jsonify(
                error="No se han podido obtener las estadísticas."
            ), 500

    return app


app = create_app()
