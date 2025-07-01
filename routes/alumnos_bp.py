from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from models import db, Alumno
from sqlalchemy.exc import SQLAlchemyError
import io
import barcode
from barcode.writer import ImageWriter

alumnos_bp = Blueprint("alumnos_bp", __name__)


# 1) Mostrar formulario de alta
@alumnos_bp.route('/', methods=['GET'])
def mostrar_alumnos():
    return render_template("alumnos.html")


# 2) Procesar alta de alumno
@alumnos_bp.route('/agregar', methods=['POST'])
def agregar_alumno():
    nombre        = request.form.get('nombre')
    apellido      = request.form.get('apellido')
    matricula     = request.form.get('matricula')
    codigo_barras = request.form.get('codigo_barras')

    if not all([nombre, apellido, matricula, codigo_barras]):
        flash("Todos los campos son obligatorios.", "warning")
        return redirect(url_for('alumnos_bp.mostrar_alumnos'))

    try:
        nuevo = Alumno(
            nombre=nombre,
            apellido=apellido,
            matricula=matricula,
            codigo_barras=codigo_barras
        )
        db.session.add(nuevo)
        db.session.commit()
        flash("Alumno agregado correctamente.", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Error en la base de datos: {e}", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Error inesperado: {e}", "danger")

    return redirect(url_for('alumnos_bp.ver_alumnos'))


# 3) Mostrar lista de alumnos
@alumnos_bp.route('/ver', methods=['GET'])
def ver_alumnos():
    try:
        alumnos = Alumno.query.order_by(Alumno.apellido).all()
        return render_template("lista_alumnos.html", alumnos=alumnos)
    except Exception as e:
        import traceback; traceback.print_exc()
        return render_template("error.html",
                               mensaje="No se pudo cargar la lista de alumnos"), 500


# 4) Mostrar formulario de edición
@alumnos_bp.route('/editar/<int:id>', methods=['GET'])
def mostrar_editar_alumno(id):
    alumno = Alumno.query.get_or_404(id)
    return render_template("editar_alumno.html", alumno=alumno)


# 5) Procesar edición de alumno
@alumnos_bp.route('/editar/<int:id>', methods=['POST'])
def editar_alumno(id):
    alumno = Alumno.query.get_or_404(id)
    alumno.nombre        = request.form.get('nombre')
    alumno.apellido      = request.form.get('apellido')
    alumno.matricula     = request.form.get('matricula')
    alumno.codigo_barras = request.form.get('codigo_barras')

    if not all([alumno.nombre, alumno.apellido, alumno.matricula, alumno.codigo_barras]):
        flash("Todos los campos son obligatorios.", "warning")
        return redirect(url_for('alumnos_bp.mostrar_editar_alumno', id=id))

    try:
        db.session.commit()
        flash("Alumno actualizado correctamente.", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Error en la base de datos: {e}", "danger")

    return redirect(url_for('alumnos_bp.ver_alumnos'))


# 6) Eliminar alumno
@alumnos_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_alumno(id):
    alumno = Alumno.query.get_or_404(id)
    try:
        db.session.delete(alumno)
        db.session.commit()
        flash("Alumno eliminado.", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"No se pudo eliminar: {e}", "danger")
    return redirect(url_for('alumnos_bp.ver_alumnos'))


# 7) Generar imagen de código de barras (Code128)
@alumnos_bp.route('/codigo/<valor>')
def generar_codigo_imagen(valor):
    buffer = io.BytesIO()
    codigo = barcode.get('code128', valor, writer=ImageWriter())
    codigo.write(buffer)
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png')


# 8) Mostrar credenciales con códigos de barras
@alumnos_bp.route('/credenciales', methods=['GET'])
def mostrar_credenciales():
    alumnos = Alumno.query.order_by(Alumno.apellido).all()
    return render_template('credenciales.html', alumnos=alumnos)