"""
Modelos Pydantic para validación de datos en VozNota
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TranscriptionResponse(BaseModel):
    """Respuesta de la transcripción exitosa"""
    titulo: str = Field(..., description="Título generado automáticamente (primeras 5 palabras)")
    texto: str = Field(..., description="Texto completo transcrito del audio")
    id_documento: str = Field(..., description="ID del documento guardado en Cloudant")
    fecha: str = Field(..., description="Fecha y hora de la transcripción")
    
    class Config:
        json_schema_extra = {
            "example": {
                "titulo": "Reunión con el equipo de",
                "texto": "Reunión con el equipo de desarrollo para discutir las nuevas características del producto.",
                "id_documento": "abc123def456",
                "fecha": "2025-11-25T10:30:00"
            }
        }

class ErrorResponse(BaseModel):
    """Respuesta de error estándar"""
    error: str = Field(..., description="Mensaje de error")
    detalle: Optional[str] = Field(None, description="Detalles adicionales del error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Error al procesar el audio",
                "detalle": "El formato del archivo no es válido"
            }
        }

class HealthResponse(BaseModel):
    """Respuesta del endpoint de salud"""
    status: str = Field(..., description="Estado del servicio")
    version: str = Field(..., description="Versión de la API")
    timestamp: str = Field(..., description="Timestamp actual")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-11-25T10:30:00"
            }
        }

class TranscriptionDocument(BaseModel):
    """Documento que se guarda en Cloudant"""
    titulo: str
    texto: str
    fecha: str
    audio_format: Optional[str] = None
    audio_size: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "titulo": "Nota de voz importante",
                "texto": "Nota de voz importante grabada hoy en la tarde",
                "fecha": "2025-11-25T10:30:00",
                "audio_format": "audio/mpeg",
                "audio_size": 245760
            }
        }
