from flask import Blueprint, request, jsonify, render_template
from models import db, Asistencia, Alumno
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

asistencia_bp = Blueprint("asistencia_bp", __name__)

@asistencia_bp.route('/')
def mostrar_asistencia():
    return render_template("asistencia.html")

@asistencia_bp.route('/reportes')
def ver_reportes():
    return render_template("reportes.html")

@asistencia_bp.route('/registrar', methods=['POST'])
def registrar_asistencia():
    data = request.json

    alumno = Alumno.query.filter_by(codigo_barras=data.get('codigo_barras')).first()
    if not alumno:
        return jsonify({"error": "Alumno no encontrado"}), 404

    asistencia_hoy = Asistencia.query.filter_by(alumno_id=alumno.id).filter(
        Asistencia.hora_entrada.like(f"{datetime.today().date()}%")).first()
    
    try:
        if asistencia_hoy and asistencia_hoy.hora_salida is None:
            asistencia_hoy.hora_salida = datetime.now()
            mensaje = "Salida registrada."
        else:
            nueva_asistencia = Asistencia(alumno_id=alumno.id, hora_entrada=datetime.now())
            db.session.add(nueva_asistencia)
            mensaje = "Entrada registrada."

        db.session.commit()
        return jsonify({"mensaje": mensaje})

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500

