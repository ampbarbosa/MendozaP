import logging
from flask_sqlalchemy import SQLAlchemy
from models import db, Alumno, Asistencia

def init_db(app):
    """
    Inicializa la conexión a la base de datos y crea las tablas pendientes.
    Se llama desde app.py en el contexto de la aplicación Flask.
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()      # ← crea alumnos y asistencia si todavía no existen

# ------------------------------------------------------------
# Funciones para gestión de alumnos
# ------------------------------------------------------------
def insertar_alumno(nombre, apellido, matricula, codigo_barras):
    """
    Registra un nuevo alumno en la base de datos.
    """
    nuevo = Alumno(
        nombre=nombre,
        apellido=apellido,
        matricula=matricula,
        codigo_barras=codigo_barras
    )
    db.session.add(nuevo)
    db.session.commit()
    return nuevo

def obtener_alumno_por_codigo(codigo_barras):
    """
    Retorna el objeto Alumno que coincide con el código de barras, o None.
    """
    return Alumno.query.filter_by(codigo_barras=codigo_barras).first()

# ------------------------------------------------------------
# Funciones para registro de asistencia
# ------------------------------------------------------------
def registrar_asistencia(codigo_barras):
    """
    Registra la entrada o salida del alumno según el escaneo del código de barras.
    """
    alumno = obtener_alumno_por_codigo(codigo_barras)
    if not alumno:
        return {"error": "Alumno no encontrado"}, 404

    from datetime import datetime
    hoy = datetime.today().date()
    asistencia_hoy = Asistencia.query \
        .filter_by(alumno_id=alumno.id) \
        .filter(Asistencia.hora_entrada.like(f"{hoy}%")) \
        .first()

    if asistencia_hoy and asistencia_hoy.hora_salida is None:
        asistencia_hoy.hora_salida = datetime.now()
        mensaje = "Salida registrada."
    else:
        nueva = Asistencia(alumno_id=alumno.id, hora_entrada=datetime.now())
        db.session.add(nueva)
        mensaje = "Entrada registrada."

    db.session.commit()
    return {"mensaje": mensaje}