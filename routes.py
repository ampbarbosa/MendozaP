from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, abort
from flask_login import current_user, login_required
from math import ceil
from functions.auth.register import registrar_alumno as process_registration
from functions.user_management.view_students import get_students
from models import db, Carrera, EstadoAlumno, Alumno, Materia, Coordinadores_Directivos,Cuatrimestre, Docente, PlanEstudios
from functions.academic_progress import get_academic_progress
from services import send_email 
from functions.user_management.update_students_data import actualizar_alumno_y_usuario
from functions.auth.register_user import registrar_coordinador_directivo
from functions.user_management.view_user import get_coordinadores_directivos
from functions.user_management.update_user_data import actualizar_coordinador_directivo
from database import bcrypt, db
from functions.reports.generate_statistical_report import generate_statistical_report
from functions.reports.export_report import generar_pdf_reporte
from functions.user_management.view_docentes import get_docentes
from functions.reports.generate_course_report import generate_course_report
from functions.reports.export_report import generar_pdf_reporte_materia
from functions.reports.generate_student_report import generate_student_report
from functions.reports.export_report import generar_pdf_reporte_alumno
from functions.reports.generate_evaluation_report import generate_evaluation_report
from functions.reports.export_report import generar_pdf_reporte_evaluacion
from functions.reports.generate_group_report import generate_group_report
from functions.reports.export_report import generar_pdf_reporte_grupo
from functions.reports.generate_career_report import generate_career_report
from functions.reports.export_report import generar_pdf_reporte_carrera

academic_bp = Blueprint('academic_bp', __name__)
alumno_progress_bp = Blueprint('alumno_progress', __name__)
reports_bp = Blueprint('reports_bp', __name__)
docentes_bp = Blueprint('docentes_bp', __name__, url_prefix='/docentes')
# Crear el Blueprint
plan_estudios_bp = Blueprint('plan_estudios_bp', __name__)




# ------------------------------------------------------------
# Route del Index
# ------------------------------------------------------------

@academic_bp.route('/', endpoint='index')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return render_template('index.html')

# ------------------------------------------------------------
# Route para el registro de alumnos
# ------------------------------------------------------------

@academic_bp.route('/register', methods=['GET', 'POST'])
@login_required
def registrar_alumno():
    if current_user.rol_id != 2:
        flash("No tienes permisos para registrar alumnos", "index-danger")
        return redirect(url_for('academic_bp.index'))
    return process_registration()

# ------------------------------------------------------------
# Route para Materias
# ------------------------------------------------------------

@academic_bp.route('/materias', methods=['GET'])
@login_required
def listar_materias():
    """
    Muestra todas las materias en una tabla.
    """
    materias = Materia.query.all()
    return render_template('vista_de_materias.html', materias=materias)

# ------------------------------------------------------------
# Route para agregar Materias
# ------------------------------------------------------------

@academic_bp.route('/materias/agregar', methods=['GET', 'POST'])
@login_required
def agregar_materia():
    """
    Permite agregar una nueva materia.
    """
    if request.method == 'POST':
        # Recoger datos del formulario
        nombre = request.form.get('nombre')
        crn = request.form.get('crn')
        codigo = request.form.get('codigo')
        creditos = int(request.form.get('creditos'))
        correlativa_id = request.form.get('correlativa_id')  # Puede ser NULL

        # Crear nueva instancia de Materia
        nueva_materia = Materia(
            nombre=nombre,
            crn=crn,
            codigo=codigo,
            creditos=creditos,
            correlativa_id=correlativa_id if correlativa_id else None
        )
        db.session.add(nueva_materia)
        db.session.commit()
        flash('Materia agregada exitosamente.', 'success')
        return redirect(url_for('academic_bp.listar_materias'))

    # Para el formulario, listar materias existentes para seleccionar correlativas
    materias = Materia.query.all()
    return render_template('agregar_materia.html', materias=materias)

# ------------------------------------------------------------
# Route para editar Materia
# ------------------------------------------------------------

@academic_bp.route('/materias/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_materia(id):
    """
    Permite editar una materia existente.
    """
    materia = Materia.query.get_or_404(id)

    if request.method == 'POST':
        # Actualizar los datos de la materia
        materia.nombre = request.form.get('nombre')
        materia.crn = request.form.get('crn')
        materia.codigo = request.form.get('codigo')
        materia.creditos = int(request.form.get('creditos'))
        materia.correlativa_id = request.form.get('correlativa_id') if request.form.get('correlativa_id') else None
        db.session.commit()
        flash('Materia actualizada exitosamente.', 'success')
        return redirect(url_for('academic_bp.listar_materias'))

    # Para el formulario, listar materias existentes para seleccionar correlativas
    materias = Materia.query.all()
    return render_template('editar_materia.html', materia=materia, materias=materias)

# ------------------------------------------------------------
# Route para eliminar Materia
# ------------------------------------------------------------

@academic_bp.route('/materias/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_materia(id):
    """
    Permite eliminar una materia.
    """
    materia = Materia.query.get_or_404(id)
    db.session.delete(materia)
    db.session.commit()
    flash('Materia eliminada exitosamente.', 'success')
    return redirect(url_for('academic_bp.listar_materias'))

# ------------------------------------------------------------
# Route para ver alumnos
# ------------------------------------------------------------

@academic_bp.route('/alumnos', methods=['GET'])
@login_required
def alumnos():
    if current_user.rol_id != 2:
        flash("No tienes permisos para acceder a esta sección.", "index-danger")
        return redirect(url_for('academic_bp.index'))

    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    page_size = 10

    # Filtros
    nombre = request.args.get('nombre')
    apellido_paterno = request.args.get('apellido_paterno')
    apellido_materno = request.args.get('apellido_materno')
    matricula = request.args.get('matricula')
    carrera_filtro = request.args.get('carrera')
    estado_filtro = request.args.get('estado')

    query = get_students(
        nombre=nombre,
        apellido_paterno=apellido_paterno,
        apellido_materno=apellido_materno,
        matricula=matricula,
        carrera=carrera_filtro,
        estado=estado_filtro,
        as_query=True
    )

    total = query.count()
    total_pages = ceil(total / page_size)
    skip = (page - 1) * page_size
    students_page = query.offset(skip).limit(page_size).all()

    students_dict = []
    for alumno in students_page:
        student_data = {
            "matricula": alumno.matricula,
            "nombre": alumno.nombre,  # Cambiado: antes era alumno.primer_nombre
            "primer_apellido": alumno.primer_apellido,
            "segundo_apellido": alumno.segundo_apellido,
            "carrera": str(alumno.carrera.nombre) if alumno.carrera else "",
            "estado": str(alumno.estado.nombre_estado) if alumno.estado else ""
        }
        students_dict.append(student_data)

    carreras = Carrera.query.all()
    estados = EstadoAlumno.query.all()

    return render_template(
        'alumnos.html',
        students=students_dict,
        carreras=carreras,
        estados=estados,
        page=page,
        total_pages=total_pages,
        matricula=matricula,
        nombre=nombre,
        apellido_paterno=apellido_paterno,
        apellido_materno=apellido_materno,
        carrera_filtro=carrera_filtro,
        estado_filtro=estado_filtro
    )

# ------------------------------------------------------------
# Route para modificar alumnos
# ------------------------------------------------------------

@academic_bp.route('/modificar_alumno', methods=['GET', 'POST'])
@login_required
def modificar_alumno():
    if current_user.rol_id != 2:
        flash("No tienes permisos para modificar alumnos", "index-danger")
        return redirect(url_for('academic_bp.index'))

    if request.method == "POST":
        # Recoger datos del formulario
        matricula = request.form.get('matricula')
        nombre = request.form.get('nombre')  # Cambio: antes era primer_nombre
        primer_apellido = request.form.get('primer_apellido')
        segundo_apellido = request.form.get('segundo_apellido')
        curp = request.form.get('curp')
        telefono = request.form.get('telefono')
        correo = request.form.get('correo_electronico')
        
        # Datos de domicilio
        pais = request.form.get('pais')
        estado_domicilio = request.form.get('estado_domicilio')
        municipio = request.form.get('municipio')
        colonia = request.form.get('colonia')
        cp = request.form.get('cp')
        calle = request.form.get('calle')
        numero_casa = request.form.get('numero_casa')
        
        # Estado y Carrera
        nuevo_estado = request.form.get('estado_alumno')
        nueva_carrera = request.form.get('carrera_alumno')
        
        # Contraseña y Documentos
        nueva_contrasena = request.form.get('contraseña')
        nuevo_certificado = request.files.get('certificado_preparatoria')
        nuevo_comprobante = request.files.get('comprobante_pago')
        
        try:
            alumno_actualizado = actualizar_alumno_y_usuario(
                matricula,
                nombre,  # Cambio: antes era primer_nombre
                primer_apellido,
                segundo_apellido,
                curp, telefono, correo,
                pais, estado_domicilio, municipio, colonia, cp, calle, numero_casa,
                nuevo_estado, nueva_carrera,
                nueva_contrasena, nuevo_certificado, nuevo_comprobante
            )
            if alumno_actualizado is None:
                flash("No se pudo actualizar el alumno. Revisa los datos ingresados.", "alumno-danger")
                alumno = Alumno.query.filter_by(matricula=matricula).first()
                estados = EstadoAlumno.query.all()
                carreras = Carrera.query.all()
                return render_template("modificar_alumno.html", alumno=alumno, form_data=request.form, estados=estados, carreras=carreras)
        except Exception as e:
            flash(f"Error al actualizar el alumno: {str(e)}", "alumno-danger")
            alumno = Alumno.query.filter_by(matricula=matricula).first()
            estados = EstadoAlumno.query.all()
            carreras = Carrera.query.all()
            return render_template("modificar_alumno.html", alumno=alumno, form_data=request.form, estados=estados, carreras=carreras)
        
        # Construir el mensaje de correo con todos los datos modificados.
        subject = "Actualización de tus datos en SkyCode"
        body = f"Hola {alumno_actualizado.nombre},\n\n"  # Cambio: antes era primer_nombre
        body += "Se han actualizado los siguientes datos en tu cuenta:\n\n"
        # Datos personales
        body += "Datos Personales:\n"
        body += f"  Nombre: {alumno_actualizado.nombre}\n"  # Cambio: antes era primer_nombre + segundo_nombre
        body += f"  Apellidos: {alumno_actualizado.primer_apellido} {alumno_actualizado.segundo_apellido}\n"
        body += f"  CURP: {alumno_actualizado.curp}\n"
        body += f"  Teléfono: {alumno_actualizado.telefono}\n"
        body += f"  Correo Electrónico: {alumno_actualizado.correo_electronico}\n\n"
        
        # Datos de domicilio
        if alumno_actualizado.domicilio:
            body += "Datos de Domicilio:\n"
            body += f"  País: {alumno_actualizado.domicilio.pais}\n"
            body += f"  Estado: {alumno_actualizado.domicilio.estado}\n"
            body += f"  Municipio: {alumno_actualizado.domicilio.municipio}\n"
            body += f"  Colonia: {alumno_actualizado.domicilio.colonia}\n"
            body += f"  Código Postal: {alumno_actualizado.domicilio.cp}\n"
            body += f"  Calle: {alumno_actualizado.domicilio.calle}\n"
            body += f"  Número de Casa: {alumno_actualizado.domicilio.numero_casa}\n\n"
        else:
            body += "No se actualizaron datos de domicilio.\n\n"
        
        # Estado y Carrera
        body += f"Estado del Alumno: {alumno_actualizado.estado.nombre_estado if alumno_actualizado.estado else 'N/A'}\n"
        body += f"Carrera: {alumno_actualizado.carrera.nombre if alumno_actualizado.carrera else 'N/A'}\n\n"
        
        # Incluir la nueva contraseña si se proporcionó
        if nueva_contrasena:
            body += f"Tu nueva contraseña es: {nueva_contrasena}\n\n"
        
        body += "Si tienes alguna duda o necesitas asistencia, por favor contáctanos.\n\n"
        body += "Saludos,\nEquipo SkyCode"

        # Enviar correo al alumno
        send_email(subject, [alumno_actualizado.correo_electronico], body)
        
        flash("Datos del alumno actualizados correctamente.", "alumno-success")
        return redirect(url_for('academic_bp.alumnos'))
    
    else:
        matricula = request.args.get('matricula')
        if not matricula:
            flash("No se especificó la matrícula del alumno.", "alumno-danger")
            return redirect(url_for('academic_bp.alumnos'))
        
        alumno = Alumno.query.filter_by(matricula=matricula).first()
        if not alumno:
            flash("Alumno no encontrado.", "alumno-danger")
            return redirect(url_for('academic_bp.alumnos'))
        
        estados = EstadoAlumno.query.all()
        carreras = Carrera.query.all()
        return render_template("modificar_alumno.html", alumno=alumno, estados=estados, carreras=carreras)

# ------------------------------------------------------------
# Route para descargar Certificado
# ------------------------------------------------------------

@academic_bp.route('/descargar_certificado/<matricula>', methods=['GET'])
@login_required
def descargar_certificado(matricula):
    alumno = Alumno.query.filter_by(matricula=matricula).first()
    if not alumno or not alumno.certificado_preparatoria:
        flash("Certificado no disponible.", "modify-danger")
        return redirect(url_for('academic_bp.modificar_alumno', matricula=matricula))
    from io import BytesIO
    return send_file(
    BytesIO(alumno.certificado_preparatoria),
    download_name="certificado.pdf",
    as_attachment=True
    )

# ------------------------------------------------------------
# Route para descargar Comprobante
# ------------------------------------------------------------

@academic_bp.route('/descargar_comprobante/<matricula>', methods=['GET'])
@login_required
def descargar_comprobante(matricula):
    alumno = Alumno.query.filter_by(matricula=matricula).first()
    if not alumno or not alumno.comprobante_pago:
        flash("Comprobante no disponible.", "modify-danger")
        return redirect(url_for('academic_bp.modificar_alumno', matricula=matricula))
    from io import BytesIO
    return send_file(
    BytesIO(alumno.comprobante_pago),
    download_name="comprobante.pdf",
    as_attachment=True
    )

# ------------------------------------------------------------
# Route para ver Progreso de Alumno
# ------------------------------------------------------------

@alumno_progress_bp.route('/progress')
@login_required
def mostrar_historial_academico():
    if current_user.rol_id != 1:  # Solo los alumnos pueden ver su progreso
        flash("No tienes permisos para ver esta sección.", "danger")
        return redirect(url_for('academic_bp.index'))

    progress_data = get_academic_progress(current_user.alumno_id)

    return render_template(
        'progress.html',
        avance=progress_data["avance"],
        historial=progress_data["historial"],
        pending_courses=progress_data["pending_courses"]
    )

# ------------------------------------------------------------
# Route para el registro de Coordinadores/Directivos
# ------------------------------------------------------------

@academic_bp.route('/register_user', methods=['GET', 'POST'])
@login_required
def register_user_route():
    if current_user.rol_id != 3:
        flash("No tienes permisos para registrar coordinadores/directivos", "index-danger")
        return redirect(url_for('auth.index'))
    return registrar_coordinador_directivo()

# ------------------------------------------------------------
# Route para Ver Coordinadores y Directivos
# ------------------------------------------------------------

@academic_bp.route('/coordinadores_directivos', methods=['GET'])
@login_required
def coordinadores_directivos():
    if current_user.rol_id != 3:
        flash("No tienes permisos para acceder a esta sección.", "index-danger")
        return redirect(url_for('academic_bp.index'))
    
    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    page_size = 10

    # Filtros
    nombre = request.args.get('nombre')
    apellido = request.args.get('apellido')
    matricula = request.args.get('matricula')
    estado_filtro = request.args.get('estado')  # '1' o '0'
    rol_filter = request.args.get('rol', type=int)  # Valor numérico (2: Coordinador, 3: Directivo)

    # Obtiene la query filtrada
    query = get_coordinadores_directivos(
        nombre=nombre,
        apellido=apellido,
        matricula=matricula,
        rol=rol_filter,
        estado=estado_filtro,
        as_query=True
    )
    
    total = query.count()
    total_pages = ceil(total / page_size)
    skip = (page - 1) * page_size
    registros_page = query.offset(skip).limit(page_size).all()
    
    users_dict = []
    for registro in registros_page:
        data = {
            "id": registro.id,
            "matricula": registro.matricula,
            "primer_nombre": registro.primer_nombre,
            "primer_apellido": registro.primer_apellido,
            "estado": "Activo" if registro.usuario and registro.usuario.activo else "Inactivo",
            "rol": "Coordinador" if registro.usuario and registro.usuario.rol_id == 2 
                   else ("Directivo" if registro.usuario and registro.usuario.rol_id == 3 else "Sin definir")
        }
        users_dict.append(data)
    
    return render_template(
        'user.html',
        users=users_dict,
        page=page,
        total_pages=total_pages,
        matricula=matricula,
        nombre=nombre,
        apellido=apellido,
        estado_filtro=estado_filtro,
        rol_filter=rol_filter
    )

# ------------------------------------------------------------
# Route para Modificar Coordinadores y Directivos
# ------------------------------------------------------------

@academic_bp.route('/modificar_coordinador_directivo', methods=['GET', 'POST'])
@login_required
def modificar_coordinador_directivo():
    if current_user.rol_id != 3:
        flash("No tienes permisos para modificar coordinadores/directivos", "coordinador-danger")
        return redirect(url_for('academic_bp.index'))
    
    if request.method == "POST":
        # Recoger datos del formulario
        user_id = request.form.get('user_id')
        primer_nombre = request.form.get('primer_nombre')
        primer_apellido = request.form.get('primer_apellido')
        correo = request.form.get('correo_electronico')
        estado_cuenta = request.form.get('estado_cuenta')  
        nueva_contrasena = request.form.get('contraseña')   
        
        try:
            coordinador_actualizado = actualizar_coordinador_directivo(
                user_id,
                primer_nombre,
                primer_apellido,
                correo,
                "Activo" if estado_cuenta == "1" else "Inactivo"
            )
            if not coordinador_actualizado:
                flash("No se pudo actualizar el Coordinador/Directivo. Revisa los datos ingresados.", "coordinador-danger")
                return redirect(url_for('academic_bp.modificar_coordinador_directivo', user_id=user_id))
        except Exception as e:
            flash(f"Error al actualizar el Coordinador/Directivo: {str(e)}", "coordinador-danger")
            return redirect(url_for('academic_bp.modificar_coordinador_directivo', user_id=user_id))
        
        # Actualizar la contraseña si se proporciona
        if nueva_contrasena:
            usuario = coordinador_actualizado.usuario
            if usuario:
                hashed = bcrypt.generate_password_hash(nueva_contrasena).decode('utf-8')
                usuario.contraseña = hashed

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash("Error al guardar los cambios en la base de datos.", "coordinador-danger")
            return redirect(url_for('academic_bp.modificar_coordinador_directivo', user_id=user_id))
        
        # Construir el mensaje de correo con los datos modificados
        subject = "Actualización de tus datos en SkyCode"
        body = f"Hola {coordinador_actualizado.primer_nombre} {coordinador_actualizado.primer_apellido},\n\n"
        body += "Se han actualizado los siguientes datos en tu cuenta:\n\n"
        body += f"  Nombre: {coordinador_actualizado.primer_nombre}\n"
        body += f"  Apellido: {coordinador_actualizado.primer_apellido}\n"
        body += f"  Correo Electrónico: {coordinador_actualizado.correo_electronico}\n"
        body += f"  Estado de la Cuenta: {'Activo' if coordinador_actualizado.usuario and coordinador_actualizado.usuario.activo else 'Inactivo'}\n"
        if nueva_contrasena:
            body += f"\nTu nueva contraseña es: {nueva_contrasena}\n"
        body += "\nSi tienes alguna duda o necesitas asistencia, por favor contáctanos.\n\n"
        body += "Saludos,\nEquipo SkyCode"
        send_email(subject, [correo], body)
        
        flash("Datos del Coordinador/Directivo actualizados correctamente.", "coordinador-success")
        return redirect(url_for('academic_bp.coordinadores_directivos'))
    
    else:
        user_id = request.args.get('user_id')
        if not user_id:
            flash("No se especificó el ID del Coordinador/Directivo.", "coordinador-danger")
            return redirect(url_for('academic_bp.coordinadores_directivos'))
        
        registro = Coordinadores_Directivos.query.get(user_id)
        if not registro:
            flash("Coordinador/Directivo no encontrado.", "coordinador-danger")
            return redirect(url_for('academic_bp.coordinadores_directivos'))
        
        return render_template("modificar_user.html", registro=registro)

# ------------------------------------------------------------
# Route de Reporte Estadistico
# ------------------------------------------------------------

@reports_bp.route('/reports')
@login_required
def mostrar_reportes():
    if current_user.rol_id != 3:  # Solo los directivos pueden acceder
        flash("No tienes permisos para acceder a esta sección.", "danger")
        return redirect(url_for('academic_bp.index'))

    report_data = generate_statistical_report()  # Obtener datos reales del reporte

    return render_template('reports.html', report_data=report_data)


# ------------------------------------------------------------
# Route para descargar el reporte en PDF
# ------------------------------------------------------------

@reports_bp.route('/reports/download_pdf')
@login_required
def download_report_pdf():
    try:
        datos_reporte = generate_statistical_report()  # Obtiene los datos

        if not datos_reporte:
            flash("No hay datos para generar el reporte.", "danger")
            return redirect(url_for('reports_bp.mostrar_reportes'))

        pdf_path = generar_pdf_reporte(datos_reporte)  # <-- Ahora sí pasamos los datos

        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        flash(f"Error al generar el PDF: {str(e)}", "danger")
        return redirect(url_for('reports_bp.mostrar_reportes'))

@academic_bp.route('/materias/pendientes/<int:alumno_id>', methods=['GET'])
@login_required
def materias_pendientes(alumno_id):
    """
    Muestra las materias pendientes por cursar y sugeridas para el siguiente cuatrimestre.
    """
    # Consultar materias pendientes
    materias_pendientes = db.session.execute("""
        SELECT m.id, m.nombre
        FROM Materias m
        LEFT JOIN Calificaciones c
            ON m.id = c.materia_id AND c.alumno_id = :alumno_id
        WHERE c.calificacion IS NULL OR c.calificacion < 70
    """, {"alumno_id": alumno_id}).fetchall()

    # Consultar materias sugeridas (siguiendo correlativas)
    materias_sugeridas = db.session.execute("""
        SELECT m.id, m.nombre
        FROM Materias m
        LEFT JOIN Calificaciones c
            ON m.id = c.materia_id AND c.alumno_id = :alumno_id
        WHERE (c.calificacion IS NULL OR c.calificacion < 70)
          AND (m.correlativa_id IS NULL 
            OR m.correlativa_id IN (
                SELECT materia_id
                FROM Calificaciones
                WHERE calificacion >= 70 AND alumno_id = :alumno_id
            ))
    """, {"alumno_id": alumno_id}).fetchall()

    return render_template(
        'materias_pendientes.html',
        pendientes=materias_pendientes,
        sugeridas=materias_sugeridas
    )
# ------------------------------------------------------------
# Route para Cuatrimestres 
# ------------------------------------------------------------
@academic_bp.route('/cuatrimestres', methods=['GET'])
@login_required
def listar_cuatrimestres():
    """
    Lista todos los cuatrimestres existentes.
    """
    cuatrimestres = Cuatrimestre.query.all()  # Consulta todos los registros en la tabla Cuatrimestres
    return render_template('listar_cuatrimestres.html', cuatrimestres=cuatrimestres)
@academic_bp.route('/cuatrimestres/agregar', methods=['GET', 'POST'])


@login_required
def agregar_cuatrimestre():
    """
    Permite agregar un nuevo cuatrimestre.
    """
    if request.method == 'POST':
        nocuatrimestre = request.form.get('nocuatrimestre')
        descripcion = request.form.get('descripcion')

        # Crear un nuevo objeto Cuatrimestre y guardarlo en la base de datos
        nuevo_cuatrimestre = Cuatrimestre(nocuatrimestre=nocuatrimestre, descripcion=descripcion)
        db.session.add(nuevo_cuatrimestre)
        db.session.commit()

        flash('Cuatrimestre agregado exitosamente.', 'success')
        return redirect(url_for('academic_bp.listar_cuatrimestres'))
    
    return render_template('agregar_cuatrimestre.html')

@academic_bp.route('/cuatrimestres/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cuatrimestre(id):
    """
    Permite editar un cuatrimestre existente.
    """
    cuatrimestre = Cuatrimestre.query.get_or_404(id)  # Obtiene el registro o lanza un error 404

    if request.method == 'POST':
        # Actualizar los campos
        cuatrimestre.nocuatrimestre = request.form.get('nocuatrimestre')
        cuatrimestre.descripcion = request.form.get('descripcion')
        db.session.commit()

        flash('Cuatrimestre actualizado exitosamente.', 'success')
        return redirect(url_for('academic_bp.listar_cuatrimestres'))
    
    return render_template('editar_cuatrimestre.html', cuatrimestre=cuatrimestre)

@academic_bp.route('/cuatrimestres/eliminar/<int:id>', methods=['POST'])

@login_required
def eliminar_cuatrimestre(id):
    """
    Permite eliminar un cuatrimestre específico.
    """
    cuatrimestre = Cuatrimestre.query.get_or_404(id)  # Obtiene el registro o lanza un error 404

    db.session.delete(cuatrimestre)  # Elimina el registro de la base de datos
    db.session.commit()

    flash('Cuatrimestre eliminado exitosamente.', 'success')
    return redirect(url_for('academic_bp.listar_cuatrimestres'))
    

# ------------------------------------------------------------
# Ruta para listar todos los docentes con filtros y paginación
# ------------------------------------------------------------
@docentes_bp.route('/', methods=['GET'])
def listar_docentes():
    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    page_size = 10

    # Parámetros de filtros
    matricula = request.args.get('matricula')
    nombre = request.args.get('nombre')
    primer_apellido = request.args.get('primer_apellido')
    segundo_apellido = request.args.get('segundo_apellido')

    # Llama a la función de filtrado para obtener la query
    query = get_docentes(
        matricula=matricula,
        nombre=nombre,
        primer_apellido=primer_apellido,
        segundo_apellido=segundo_apellido,
        as_query=True
    )

    # Paginación
    total = query.count()  # Contar el total de resultados
    total_pages = ceil(total / page_size)  # Calcular el total de páginas
    skip = (page - 1) * page_size  # Calcular el desplazamiento
    docentes_page = query.offset(skip).limit(page_size).all()  # Obtener la página actual

    # Transformar los resultados en una lista de diccionarios para la plantilla
    docentes_dict = [
        {
            "matricula": docente.matricula,
            "nombre": docente.nombre,
            "primer_apellido": docente.primer_apellido,
            "segundo_apellido": docente.segundo_apellido,
            "correo_electronico": docente.correo_electronico
        }
        for docente in docentes_page
    ]

    # Renderizar la plantilla con los datos
    return render_template(
        'listar_docentes.html',
        docentes=docentes_dict,
        page=page,
        total_pages=total_pages,
        matricula=matricula,
        nombre=nombre,
        primer_apellido=primer_apellido,
        segundo_apellido=segundo_apellido
    )

# ------------------------------------------------------------
# Ruta para registrar un nuevo docente
# ------------------------------------------------------------
@docentes_bp.route('/nuevo', methods=['GET', 'POST'])
def registrar_docente():
    from functions.auth.validations import generar_matricula_docente  # Importar función de matrícula

    if request.method == 'POST':
        # Recoger datos del formulario
        nombre = request.form.get('nombre')
        primer_apellido = request.form.get('primer_apellido')
        segundo_apellido = request.form.get('segundo_apellido')
        correo_electronico = request.form.get('correo_electronico')

        # Generar la matrícula automáticamente
        matricula = generar_matricula_docente()

        # Crear el nuevo docente con la matrícula
        nuevo_docente = Docente(
            nombre=nombre,
            primer_apellido=primer_apellido,
            segundo_apellido=segundo_apellido,
            correo_electronico=correo_electronico,
            matricula=matricula
        )

        # Guardar en la base de datos
        try:
            db.session.add(nuevo_docente)
            db.session.commit()
            flash('Docente registrado exitosamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar el docente: {str(e)}', 'danger')

        return redirect(url_for('docentes_bp.listar_docentes'))
    
    return render_template('registrar_docente.html')

# ------------------------------------------------------------
# Ruta para editar un docente existente
# ------------------------------------------------------------
@docentes_bp.route('/<string:matricula>/editar', methods=['GET', 'POST'])
def editar_docente(matricula):
    # Buscar el docente por matrícula
    docente = Docente.query.filter_by(matricula=matricula).first()
    if not docente:
        flash("Docente no encontrado", "danger")
        return redirect(url_for('docentes_bp.listar_docentes'))

    if request.method == 'POST':
        # Actualizar datos con lo enviado desde el formulario
        docente.nombre = request.form.get('nombre')
        docente.primer_apellido = request.form.get('primer_apellido')
        docente.segundo_apellido = request.form.get('segundo_apellido')
        docente.correo_electronico = request.form.get('correo_electronico')

        try:
            db.session.commit()
            flash('Docente actualizado exitosamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el docente: {str(e)}', 'danger')

        return redirect(url_for('docentes_bp.listar_docentes'))
    
    return render_template('editar_docente.html', docente=docente)

# ------------------------------------------------------------
# Ruta para eliminar un docente
# ------------------------------------------------------------
@docentes_bp.route('/<int:id>/eliminar', methods=['POST'])
def eliminar_docente(id):
    docente = Docente.query.get_or_404(id)

    try:
        db.session.delete(docente)
        db.session.commit()
        flash('Docente eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el docente: {str(e)}', 'danger')
    return redirect(url_for('docentes_bp.listar_docentes'))

# ------------------------------------------------------------
# Ruta para asignar materias a un docente
# ------------------------------------------------------------
@docentes_bp.route('/<int:docente_id>/asignar_materias', methods=['GET', 'POST'])
@login_required
def asignar_materias(docente_id):
    # Obtén al docente por su ID o muestra un error 404 si no existe
    docente = Docente.query.get_or_404(docente_id)
    
    # Obtén todas las materias disponibles para mostrarlas en el formulario
    materias = Materia.query.all()

    if request.method == 'POST':
        # Obtener los IDs de las materias seleccionadas desde el formulario
        materias_ids = request.form.getlist('materias')

        # Buscar las materias que corresponden a esos IDs
        nuevas_materias = Materia.query.filter(Materia.id.in_(materias_ids)).all()

        # Agregar solo las materias nuevas (que no estén asignadas todavía)
        for nueva_materia in nuevas_materias:
            if nueva_materia not in docente.materias:
                docente.materias.append(nueva_materia)

        # Guardar los cambios
        try:
            db.session.commit()
            flash('Materias asignadas correctamente al docente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al asignar materias: {str(e)}', 'danger')

        # Redirige de nuevo a la lista de docentes
        return redirect(url_for('docentes_bp.ver_docentes_materias'))

    # Renderiza el formulario de asignación con las materias y el docente
    return render_template('asignar_materias_docente.html', docente=docente, materias=materias)

# ------------------------------------------------------------
# Ruta para ver docentes y materias asignadas
# ------------------------------------------------------------
@docentes_bp.route('/ver_docentes_materias', methods=['GET'])
@login_required
def ver_docentes_materias():
    # Recupera todos los docentes junto con sus materias
    docentes = Docente.query.all()
    return render_template('ver_docentes_materias.html', docentes=docentes)

# ------------------------------------------------------------
# Route de Reporte por Materia
# ------------------------------------------------------------


@academic_bp.route('/reportes/materia', methods=['GET'])
@login_required
def reporte_por_materia():
    if current_user.rol_id != 3:
        flash("No tienes permisos para ver esta sección.", "danger")
        return redirect(url_for('academic_bp.index'))

    materias = Materia.query.all()
    materia_id = request.args.get('materia_id', type=int)
    datos_materia = generate_course_report(materia_id) if materia_id else None

    return render_template('reporte_por_materia.html', materias=materias, datos_materia=datos_materia, materia_id=materia_id)

# ------------------------------------------------------------
# Route para descargar el reporte por materia en PDF
# ------------------------------------------------------------

@academic_bp.route('/reporte-materia/pdf/<int:materia>', methods=['GET'])
@login_required
def descargar_reporte_materia_pdf(materia):
    datos = generate_course_report(materia)
    if not datos:
        flash("No hay datos para esta materia.", "warning")
        return redirect(url_for('academic_bp.reporte_por_materia'))

    path_pdf = generar_pdf_reporte_materia(datos)

    return send_file(path_pdf, as_attachment=True)

# ------------------------------------------------------------
# Route de Reporte por Alumno
# ------------------------------------------------------------


@academic_bp.route('/reporte-alumno', methods=['GET'])
@login_required
def reporte_por_alumno():
    if current_user.rol_id != 3:
        flash("No tienes permisos para acceder a esta sección.", "danger")
        return redirect(url_for('academic_bp.index'))

    alumnos = Alumno.query.all()
    return render_template('reporte_por_alumno.html', alumnos=alumnos)


# ------------------------------------------------------------
# Route para descargar el reporte por alumno en PDF
# ------------------------------------------------------------

@academic_bp.route('/reporte-alumno/pdf/<string:matricula>', methods=['GET'])
@login_required
def descargar_reporte_alumno_pdf(matricula):
    datos = generate_student_report(matricula)
    if not datos:
        flash("No se encontraron datos para este alumno.", "warning")
        return redirect(url_for('academic_bp.reporte_por_alumno'))

    pdf_path = generar_pdf_reporte_alumno(datos)
    return send_file(pdf_path, as_attachment=True)

# ------------------------------------------------------------
# Route de Reporte por Evaluacion
# ------------------------------------------------------------

@academic_bp.route('/reporte_evaluacion', methods=['GET'])
@login_required
def reporte_por_evaluacion():
    if current_user.rol_id != 3:
        flash("No tienes permisos para ver esta sección.", "danger")
        return redirect(url_for('academic_bp.index'))

    datos = generate_evaluation_report()
    return render_template("reporte_por_evaluacion.html", datos=datos)

# ------------------------------------------------------------
# Route para descargar el reporte por evaluacion en PDF
# ------------------------------------------------------------

@academic_bp.route('/reporte_evaluacion/pdf', methods=['GET'])
@login_required
def descargar_pdf_evaluacion():
    datos = generate_evaluation_report()
    path_pdf = generar_pdf_reporte_evaluacion(datos)
    return send_file(path_pdf, as_attachment=True)

# ------------------------------------------------------------
# Route de Reporte por Grupo
# ------------------------------------------------------------

@academic_bp.route('/reporte_grupo')
@login_required
def reporte_por_grupo():
    if current_user.rol_id != 3:
        flash("No tienes permisos para ver esta sección.", "danger")
        return redirect(url_for('academic_bp.index'))

    datos = generate_group_report()
    return render_template("reporte_por_grupo.html", datos=datos)

# ------------------------------------------------------------
# Route para descargar el reporte por grupo en PDF
# ------------------------------------------------------------

@academic_bp.route('/reporte_grupo/pdf')
@login_required
def descargar_pdf_grupo():
    datos = generate_group_report()
    pdf_path = generar_pdf_reporte_grupo(datos)
    return send_file(pdf_path, as_attachment=True)

# ------------------------------------------------------------
# Route de Reporte por Carrera
# ------------------------------------------------------------

@academic_bp.route("/reporte_carrera")
@login_required
def reporte_por_carrera():
    if current_user.rol_id != 3:
        flash("No tienes permisos para ver esta sección.", "danger")
        return redirect(url_for('academic_bp.index'))

    datos = generate_career_report()
    return render_template("reporte_por_carrera.html", datos=datos)

# ------------------------------------------------------------
# Route para descargar el reporte por carrera en PDF
# ------------------------------------------------------------

@academic_bp.route("/reporte_carrera/pdf")
@login_required
def descargar_pdf_carrera():
    datos = generate_career_report()
    pdf_path = generar_pdf_reporte_carrera(datos)
    return send_file(pdf_path, as_attachment=True)

# ------------------------------------------------------------
# Route para plan de estudios 
# ------------------------------------------------------------

@plan_estudios_bp.route('/asignar', methods=['GET', 'POST'])
def asignar_plan_estudios():
    if request.method == 'POST':
        # Recoger datos del formulario
        carrera_id = request.form.get('carrera_id')
        materia_id = request.form.get('materia_id')
        cuatrimestre_id = request.form.get('cuatrimestre')

        # Crear un nuevo registro en PlanEstudios
        nuevo_plan_estudio = PlanEstudios(
            carrera_id=carrera_id,
            materia_id=materia_id,
            cuatrimestre=cuatrimestre_id
        )

        # Guardar en la base de datos
        try:
            db.session.add(nuevo_plan_estudio)
            db.session.commit()
            flash('Plan de estudios asignado exitosamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al asignar el plan de estudios: {str(e)}', 'danger')

        return redirect(url_for('plan_estudios_bp.asignar_plan_estudios'))

    # Cargar datos para el formulario
    carreras = Carrera.query.all()
    materias = Materia.query.all()
    cuatrimestres = Cuatrimestre.query.all()

    return render_template(
        'asignar_plan_estudios.html',
        carreras=carreras,
        materias=materias,
        cuatrimestres=cuatrimestres
    )
