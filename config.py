"""
Configuración de la aplicación VozNota
Gestiona las variables de entorno y configuraciones del sistema
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Settings:
    """Configuración centralizada de la aplicación"""
    
    # Configuración del servidor
    APP_NAME: str = "VozNota API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "API de transcripción de voz con IBM Watson y Cloudant"
    
    # Watson Speech to Text
    WATSON_STT_API_KEY: str = os.getenv("WATSON_STT_API_KEY", "")
    WATSON_STT_URL: str = os.getenv("WATSON_STT_URL", "")
    WATSON_STT_MODEL: str = os.getenv("WATSON_STT_MODEL", "es-ES_BroadbandModel")
    
    # IBM Cloudant
    CLOUDANT_URL: str = os.getenv("CLOUDANT_URL", "")
    CLOUDANT_DB_NAME: str = os.getenv("CLOUDANT_DB_NAME", "voznota_transcriptions")
    USERS_DB_NAME: str = os.getenv("USERS_DB_NAME", "voznota_users")
    
    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-please")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))  # 30 días
    
    # Configuración de archivos
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_AUDIO_FORMATS: list = [
        "audio/wav", "audio/mpeg", "audio/mp3", "audio/x-wav", 
        "application/octet-stream", "audio/wave", "audio/webm",
        "audio/ogg", "audio/mp4", "audio/x-m4a"
    ]
    ALLOWED_EXTENSIONS: list = [".wav", ".mp3", ".webm", ".ogg", ".m4a"]
    
    # CORS
    CORS_ORIGINS: list = ["*"]  # En producción, especificar dominios permitidos
    
    # Puerto del servidor
    PORT: int = int(os.getenv("PORT", "8080"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    
    def validate(self) -> bool:
        """Valida que las credenciales necesarias estén configuradas"""
        if not self.WATSON_STT_API_KEY:
            raise ValueError("WATSON_STT_API_KEY no está configurada")
        if not self.WATSON_STT_URL:
            raise ValueError("WATSON_STT_URL no está configurada")
        if not self.CLOUDANT_URL:
            raise ValueError("CLOUDANT_URL no está configurada")
        return True

# Instancia global de configuración
settings = Settings()
