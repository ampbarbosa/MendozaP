from flask import Blueprint, redirect, url_for, flash, render_template
from datetime import datetime
from models import db, Alumno, RegistroBaño

registro_bp = Blueprint('registro_bp', __name__)

# Ruta 1: Mostrar formulario HTML para ingresar código manualmente
@registro_bp.route('/formulario', methods=['GET'])
def mostrar_formulario_registro():
    return render_template('registro_banio.html')


# Ruta 2: Registrar salida o regreso al baño según escaneo del código
@registro_bp.route('/registro_banio/<codigo>', methods=['GET'])
def registrar_salida_banio(codigo):
    alumno = Alumno.query.filter_by(codigo_barras=codigo).first()
    if not alumno:
        flash("Código de barras no encontrado", "danger")
        return redirect(url_for('registro_bp.mostrar_formulario_registro'))

    hoy = datetime.now().date()
    ahora = datetime.now().time()

    # Buscar el último registro del día para este alumno
    registro = (
        RegistroBaño.query
        .filter_by(matricula=alumno.matricula, fecha=hoy)
        .order_by(RegistroBaño.id.desc())
        .first()
    )

    if not registro or (registro.hora_salida and registro.hora_regreso):
        # Nuevo registro (salida)
        nuevo = RegistroBaño(
            alumno_id=alumno.id,
            nombre=alumno.nombre,
            apellido=alumno.apellido,
            matricula=alumno.matricula,
            fecha=hoy,
            hora_salida=ahora
        )
        db.session.add(nuevo)
        db.session.commit()
        flash(f"{alumno.nombre} salió al baño a las {ahora.strftime('%H:%M:%S')}.", "info")
    elif not registro.hora_regreso:
        # Actualizar hora_regreso del último registro incompleto
        registro.hora_regreso = ahora
        db.session.commit()
        flash(f"{alumno.nombre} regresó del baño a las {ahora.strftime('%H:%M:%S')}.", "success")

    return redirect(url_for('registro_bp.mostrar_formulario_registro'))

@registro_bp.route('/registros', methods=['GET'])
def ver_registros_banio():
    registros = RegistroBaño.query.order_by(RegistroBaño.fecha.desc(), RegistroBaño.hora_salida.desc()).all()
    return render_template('registros_banio.html', registros=registros)