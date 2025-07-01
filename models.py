from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Alumno(db.Model):
    __tablename__ = "alumnos"  # ✅ Se mantiene en minúsculas, coincidiendo con MySQL
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    matricula = db.Column(db.String(20), unique=True, nullable=False)
    codigo_barras = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"<Alumno {self.nombre} {self.apellido} - {self.matricula}>"

class Asistencia(db.Model):
    __tablename__ = "asistencia"  # ✅ Cambio a minúsculas para coincidir con la base de datos
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alumno_id = db.Column(db.Integer, db.ForeignKey("alumnos.id"), nullable=False)  # ✅ Corrección de clave foránea
    hora_entrada = db.Column(db.DateTime, nullable=False)
    hora_salida = db.Column(db.DateTime, nullable=True)