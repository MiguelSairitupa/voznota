"""
VozNota API - Backend de Transcripción de Voz
FastAPI application para transcribir audio usando IBM Watson STT y guardar en Cloudant
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config import settings
from models import TranscriptionResponse, ErrorResponse, HealthResponse
from services.watson_service import watson_service
from services.cloudant_service import cloudant_service

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

@app.post(
    "/api/transcribe",
    response_model=TranscriptionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    tags=["Transcription"]
)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Archivo de audio (WAV o MP3)")
):
    """
    Transcribe un archivo de audio a texto usando IBM Watson STT
    
    **Flujo de trabajo:**
    1. Recibe el archivo de audio desde el cliente Flutter
    2. Valida el formato y tamaño del archivo
    3. Envía el audio a Watson Speech to Text para transcripción
    4. Genera un título automático (primeras 5 palabras)
    5. Guarda la transcripción en IBM Cloudant
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
        logger.info(f"Nueva solicitud de transcripción. Archivo: {audio.filename}")
        
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
        
        # Preparar respuesta
        response = TranscriptionResponse(
            titulo=titulo,
            texto=texto_transcrito,
            id_documento=doc_id,
            fecha=datetime.now().isoformat()
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
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    tags=["Notes"]
)
async def get_all_notes(limit: int = 100):
    """
    Obtiene todas las notas/transcripciones guardadas en Cloudant
    
    **Parámetros:**
    - limit: Número máximo de notas a devolver (default: 100)
    
    **Retorna:**
    - Lista de notas con sus transcripciones
    """
    try:
        logger.info(f"Obteniendo lista de notas (límite: {limit})")
        
        notes = cloudant_service.list_transcriptions(limit=limit)
        logger.info(f"Se encontraron {len(notes)} notas")
        
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
        404: {"model": ErrorResponse, "description": "Note Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    tags=["Notes"]
)
async def get_note_by_id(note_id: str):
    """
    Obtiene una nota específica por su ID
    
    **Parámetros:**
    - note_id: ID del documento en Cloudant
    
    **Retorna:**
    - Documento completo de la nota
    """
    try:
        logger.info(f"Obteniendo nota con ID: {note_id}")
        
        note = cloudant_service.get_transcription(note_id)
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nota con ID {note_id} no encontrada"
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
        404: {"model": ErrorResponse, "description": "Note Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    tags=["Notes"]
)
async def delete_note(note_id: str):
    """
    Elimina una nota de Cloudant
    
    **Parámetros:**
    - note_id: ID del documento a eliminar
    
    **Retorna:**
    - Confirmación de eliminación exitosa
    """
    try:
        logger.info(f"Eliminando nota con ID: {note_id}")
        
        # Primero obtener el documento para tener el _rev
        note = cloudant_service.get_transcription(note_id)
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nota con ID {note_id} no encontrada"
            )
        
        # Eliminar el documento
        cloudant_service.delete_transcription(note_id, note.get('_rev'))
        
        logger.info(f"Nota {note_id} eliminada exitosamente")
        
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
