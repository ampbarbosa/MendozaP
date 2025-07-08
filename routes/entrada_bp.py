from flask import Blueprint, redirect, url_for, flash, render_template
from datetime import datetime
from models import db, Alumno, RegistroAsistencia

entrada_bp = Blueprint('entrada_bp', __name__)

# Ruta 1: Muestra el formulario HTML para escaneo
@entrada_bp.route('/formulario', methods=['GET'])
def mostrar_formulario_asistencia():
    return render_template('registro_asistencia.html')

# Ruta 2: Detecta entrada o salida según escaneo
@entrada_bp.route('/registro_asistencia/<codigo>', methods=['GET'])
def registrar_asistencia(codigo):
    alumno = Alumno.query.filter_by(codigo_barras=codigo).first()
    if not alumno:
        flash("Código de barras no encontrado", "danger")
        return redirect(url_for('entrada_bp.mostrar_formulario_asistencia'))

    hoy = datetime.now().date()
    ahora = datetime.now().time()

    # Obtener el último registro del día
    registro = (
        RegistroAsistencia.query
        .filter_by(matricula=alumno.matricula, fecha=hoy)
        .order_by(RegistroAsistencia.id.desc())
        .first()
    )

    if not registro or (registro.hora_entrada and registro.hora_salida):
        # Crear nuevo registro con hora_entrada
        nuevo = RegistroAsistencia(
            alumno_id=alumno.id,
            nombre=alumno.nombre,
            apellido=alumno.apellido,
            matricula=alumno.matricula,
            fecha=hoy,
            hora_entrada=ahora
        )
        db.session.add(nuevo)
        db.session.commit()
        flash(f"{alumno.nombre} registró su entrada a las {ahora.strftime('%H:%M:%S')}.", "info")
    elif not registro.hora_salida:
        # Completar registro con hora_salida
        registro.hora_salida = ahora
        db.session.commit()
        flash(f"{alumno.nombre} registró su salida a las {ahora.strftime('%H:%M:%S')}.", "success")

    return redirect(url_for('entrada_bp.mostrar_formulario_asistencia'))

@entrada_bp.route('/registros', methods=['GET'])
def ver_registros_asistencia():
    registros = RegistroAsistencia.query.order_by(RegistroAsistencia.fecha.desc(), RegistroAsistencia.hora_entrada.desc()).all()
    return render_template('registros_asistencia.html', registros=registros)
