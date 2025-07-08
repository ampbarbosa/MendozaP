from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from models import db, Alumno, HistorialReportes

reportes_bp = Blueprint('reportes_bp', __name__)

# Vista del formulario de generación de reporte
@reportes_bp.route('/formulario_reporte', methods=['GET', 'POST'])
def formulario_reporte():
    alumno = None
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        alumno = Alumno.query.filter_by(codigo_barras=codigo).first()
        if not alumno:
            flash("Alumno no encontrado con ese código de barras", "danger")
    return render_template('formulario_reporte.html', alumno=alumno, fecha=datetime.now())

# Registro del incidente + incremento de reportes
@reportes_bp.route('/registrar_reporte/<int:alumno_id>', methods=['POST'])
def registrar_reporte(alumno_id):
    alumno = Alumno.query.get_or_404(alumno_id)

    historial = HistorialReportes.query.filter_by(matricula=alumno.matricula).first()

    if historial:
        historial.total_reportes += 1
    else:
        historial = HistorialReportes(
            alumno_id=alumno.id,
            nombre=alumno.nombre,
            apellido=alumno.apellido,
            matricula=alumno.matricula,
            total_reportes=1
        )
        db.session.add(historial)

    db.session.commit()
    flash(f"Reporte registrado para {alumno.nombre}. Total ahora: {historial.total_reportes}", "success")
    return redirect(url_for('reportes_bp.formulario_reporte'))