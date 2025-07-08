from flask import Flask, render_template
from config import config_by_name
from database import init_db
from routes.asistencia_bp import asistencia_bp
from routes.alumnos_bp import alumnos_bp

app = Flask(__name__)
app.config.from_object(config_by_name["development"])  # Aseguramos el entorno correcto

# Inicializa la base de datos
init_db(app)

# Registra los Blueprints
app.register_blueprint(asistencia_bp, url_prefix="/asistencia")
app.register_blueprint(alumnos_bp, url_prefix="/alumnos")

# Ruta principal
@app.route('/')
def home():
    try:
        return render_template("index.html")
    except Exception as e:
        return f"Error cargando la página de inicio: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
    