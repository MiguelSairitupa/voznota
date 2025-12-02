"""
VozNota API - Backend de Transcripción de Voz
FastAPI application para transcribir audio usando IBM Watson STT y guardar en Cloudant
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
import uvicorn

from config import settings
from models import (
    TranscriptionResponse, ErrorResponse, HealthResponse,
    UserRegister, UserLogin, UserResponse, Token
)
from services.watson_service import watson_service
from services.cloudant_service import cloudant_service
from services.user_service import user_service
from services.auth_service import auth_service, get_current_active_user

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    logger.info("="*50)
    logger.info(f"Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("="*50)
    try:
        settings.validate()
        logger.info("✓ Validación de configuración exitosa")
    except Exception as e:
        logger.error(f"✗ Error en configuración: {str(e)}")
        raise

@app.get("/", tags=["Info"])
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Endpoint de verificación de salud del servicio
    """
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.now().isoformat()
    )

# ============================================================================
# Endpoints de Autenticación
# ============================================================================

@app.post(
    "/api/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Email ya registrado o datos inválidos"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    tags=["Authentication"]
)
async def register_user(user_data: UserRegister):
    """
    Registra un nuevo usuario
    
    **Parámetros:**
    - email: Email único del usuario
    - password: Contraseña (mínimo 6 caracteres)
    
    **Retorna:**
    - Usuario creado sin contraseña
    """
    try:
        logger.info(f"Intento de registro: {user_data.email}")
        
        # Crear usuario
        user = user_service.create_user(
            email=user_data.email,
            password=user_data.password
        )
        
        logger.info(f"Usuario registrado exitosamente: {user_data.email}")
        
        return UserResponse(
            id=user["_id"],
            email=user["email"],
            created_at=user["created_at"],
            is_active=user["is_active"]
        )
    
    except ValueError as e:
        # Email ya existe
        logger.warning(f"Error de validación en registro: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error al registrar usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar usuario: {str(e)}"
        )

@app.post(
    "/api/auth/login",
    response_model=Token,
    responses={
        401: {"model": ErrorResponse, "description": "Credenciales incorrectas"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    tags=["Authentication"]
)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Inicia sesión y obtiene un token JWT
    
    **Parámetros:**
    - username: Email del usuario (OAuth2 usa 'username')
    - password: Contraseña
    
    **Retorna:**
    - Token JWT de acceso
    - Información del usuario
    """
    try:
        logger.info(f"Intento de login: {form_data.username}")
        
        # Autenticar usuario (username es el email)
        user = user_service.authenticate_user(
            email=form_data.username,
            password=form_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Crear token JWT
        access_token = auth_service.create_access_token(
            data={"sub": user["_id"], "email": user["email"]}
        )
        
        logger.info(f"Login exitoso: {form_data.username}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user["_id"],
                email=user["email"],
                created_at=user["created_at"],
                is_active=user["is_active"]
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar sesión: {str(e)}"
        )

@app.get(
    "/api/auth/me",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "No autenticado"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    tags=["Authentication"]
)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_active_user)):
    """
    Obtiene la información del usuario actual autenticado
    
    **Requiere:** Token JWT en header Authorization
    
    **Retorna:**
    - Información del usuario actual
    """
    return current_user

# ============================================================================
# Endpoints de Transcripción (Protegidos)
# ============================================================================

@app.post(
    "/api/transcribe",
    response_model=TranscriptionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "No autenticado"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    tags=["Transcription"]
)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Archivo de audio (WAV o MP3)"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Transcribe un archivo de audio a texto usando IBM Watson STT
    
    **Requiere:** Token JWT en header Authorization
    
    **Flujo de trabajo:**
    1. Recibe el archivo de audio desde el cliente Flutter
    2. Valida el formato y tamaño del archivo
    3. Envía el audio a Watson Speech to Text para transcripción
    4. Genera un título automático (primeras 5 palabras)
    5. Guarda la transcripción en IBM Cloudant asociada al usuario
    6. Retorna el título, texto completo y ID del documento
    
    **Parámetros:**
    - audio: Archivo de audio en formato WAV o MP3 (máx. 10 MB)
    
    **Retorna:**
    - titulo: Título generado automáticamente
    - texto: Texto completo transcrito
    - id_documento: ID del documento en Cloudant
    - fecha: Timestamp de la transcripción
    """
    try:
        logger.info(f"Nueva solicitud de transcripción. Archivo: {audio.filename}, Usuario: {current_user.email}")
        
        # Validar tipo de archivo
        if audio.content_type not in settings.ALLOWED_AUDIO_FORMATS:
            logger.warning(f"Formato de audio no válido: {audio.content_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato de audio no válido. Formatos permitidos: {', '.join(settings.ALLOWED_AUDIO_FORMATS)}"
            )
        
        # Leer contenido del archivo
        audio_content = await audio.read()
        audio_size = len(audio_content)
        
        logger.info(f"Audio leído: {audio_size} bytes")
        logger.info(f"Primeros 20 bytes (hex): {audio_content[:20].hex()}")
        
        # Validar tamaño del archivo
        if audio_size > settings.MAX_FILE_SIZE:
            logger.warning(f"Archivo demasiado grande: {audio_size} bytes")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo es demasiado grande. Tamaño máximo: {settings.MAX_FILE_SIZE / (1024*1024)} MB"
            )
        
        logger.info(f"Archivo válido. Tamaño: {audio_size} bytes, Tipo: {audio.content_type}")
        
        # Transcribir audio con Watson STT
        try:
            texto_transcrito = watson_service.transcribe_audio(
                audio_file=audio_content,
                content_type=audio.content_type
            )
            
            if not texto_transcrito:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se pudo transcribir el audio. El audio podría estar vacío o ser inaudible."
                )
            
            logger.info(f"Transcripción exitosa: {len(texto_transcrito)} caracteres")
        
        except Exception as e:
            logger.error(f"Error en Watson STT: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al transcribir el audio: {str(e)}"
            )
        
        # Generar título
        titulo = watson_service.generate_title(texto_transcrito)
        
        # Guardar en Cloudant
        try:
            doc_id = cloudant_service.save_transcription(
                titulo=titulo,
                texto=texto_transcrito,
                user_id=current_user.id,
                audio_format=audio.content_type,
                audio_size=audio_size
            )
            
            logger.info(f"Documento guardado en Cloudant. ID: {doc_id}")
        
        except Exception as e:
            logger.error(f"Error al guardar en Cloudant: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al guardar la transcripción: {str(e)}"
            )
        
        # Preparar respuesta con zona horaria de Perú (UTC-5)
        peru_tz = timezone(timedelta(hours=-5))
        fecha_peru = datetime.now(peru_tz).isoformat()
        
        response = TranscriptionResponse(
            titulo=titulo,
            texto=texto_transcrito,
            id_documento=doc_id,
            fecha=fecha_peru
        )
        
        logger.info(f"Transcripción completada exitosamente. ID: {doc_id}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.get(
    "/api/notes",
    responses={
        401: {"model": ErrorResponse, "description": "No autenticado"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    tags=["Notes"]
)
async def get_all_notes(
    current_user: UserResponse = Depends(get_current_active_user),
    limit: int = 100
):
    """
    Obtiene todas las notas/transcripciones del usuario autenticado
    
    **Requiere:** Token JWT en header Authorization
    
    **Parámetros:**
    - limit: Número máximo de notas a devolver (default: 100)
    
    **Retorna:**
    - Lista de notas del usuario actual
    """
    try:
        logger.info(f"Obteniendo lista de notas para usuario: {current_user.email} (límite: {limit})")
        
        # Listar solo las notas del usuario actual
        notes = cloudant_service.list_transcriptions(user_id=current_user.id, limit=limit)
        logger.info(f"Se encontraron {len(notes)} notas para usuario {current_user.email}")
        
        return notes
    
    except Exception as e:
        logger.error(f"Error al obtener notas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las notas: {str(e)}"
        )

@app.get(
    "/api/notes/{note_id}",
    responses={
        401: {"model": ErrorResponse, "description": "No autenticado"},
        403: {"model": ErrorResponse, "description": "No autorizado"},
        404: {"model": ErrorResponse, "description": "Note Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    tags=["Notes"]
)
async def get_note_by_id(
    note_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Obtiene una nota específica por su ID
    
    **Requiere:** Token JWT en header Authorization
    
    **Parámetros:**
    - note_id: ID del documento en Cloudant
    
    **Retorna:**
    - Documento completo de la nota (solo si pertenece al usuario)
    """
    try:
        logger.info(f"Obteniendo nota con ID: {note_id} para usuario: {current_user.email}")
        
        note = cloudant_service.get_transcription(note_id)
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nota con ID {note_id} no encontrada"
            )
        
        # Verificar que la nota pertenezca al usuario actual
        if note.get("user_id") != current_user.id:
            logger.warning(f"Usuario {current_user.email} intentó acceder a nota de otro usuario")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para acceder a esta nota"
            )
        
        return note
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener nota {note_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la nota: {str(e)}"
        )

@app.delete(
    "/api/notes/{note_id}",
    responses={
        401: {"model": ErrorResponse, "description": "No autenticado"},
        403: {"model": ErrorResponse, "description": "No autorizado"},
        404: {"model": ErrorResponse, "description": "Note Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    tags=["Notes"]
)
async def delete_note(
    note_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Elimina una nota de Cloudant
    
    **Requiere:** Token JWT en header Authorization
    
    **Parámetros:**
    - note_id: ID del documento a eliminar
    
    **Retorna:**
    - Confirmación de eliminación exitosa (solo si la nota pertenece al usuario)
    """
    try:
        logger.info(f"Eliminando nota con ID: {note_id} para usuario: {current_user.email}")
        
        # Primero obtener el documento para tener el _rev y verificar permisos
        note = cloudant_service.get_transcription(note_id)
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nota con ID {note_id} no encontrada"
            )
        
        # Verificar que la nota pertenezca al usuario actual
        if note.get("user_id") != current_user.id:
            logger.warning(f"Usuario {current_user.email} intentó eliminar nota de otro usuario")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar esta nota"
            )
        
        # Eliminar el documento
        cloudant_service.delete_transcription(note_id, note.get('_rev'))
        
        logger.info(f"Nota {note_id} eliminada exitosamente por {current_user.email}")
        
        return {
            "success": True,
            "message": f"Nota {note_id} eliminada exitosamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar nota {note_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la nota: {str(e)}"
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones"""
    logger.error(f"Excepción no manejada: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Error interno del servidor", "detalle": str(exc)}
    )

if __name__ == "__main__":
    logger.info(f"Iniciando servidor en {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info"
    )
