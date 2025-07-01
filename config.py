import os
from dotenv import load_dotenv

# ✅ Cargar variables desde .env correctamente
load_dotenv()

class Config:
    """Configuración base del sistema MendozaP."""
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
    DEBUG = False
    TESTING = False

    # ✅ Configuración de la base de datos en Clever Cloud
    DB_HOST = os.getenv("DB_HOST")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    DB_PORT = int(os.getenv("DB_PORT", 3306))  # 🔹 Convertimos a entero para evitar errores

    # ✅ Verificación de carga de variables
    if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME]):
        print("⚠️ Advertencia: Algunas variables de entorno no están cargadas correctamente.")

    # ✅ Corrección en `SQLALCHEMY_DATABASE_URI`
    SQLALCHEMY_DATABASE_URI = os.getenv("DB_URI") or f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB

    # ✅ Prueba de conexión mejorada
    print(f"✅ Conectando a BD: {DB_HOST}, Usuario: {DB_USER}, Base: {DB_NAME}, Puerto: {DB_PORT}")

class DevelopmentConfig(Config):
    """Entorno de desarrollo (modo debug activado)."""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class TestingConfig(Config):
    """Entorno de pruebas (base de datos en memoria)."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

class ProductionConfig(Config):
    """Entorno de producción (modo seguro)."""
    DEBUG = False
    SQLALCHEMY_ECHO = False

# ✅ Diccionario para seleccionar la configuración según el entorno
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}