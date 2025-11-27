"""
Servicio de IBM Watson Speech to Text
Maneja la transcripción de audio usando Watson STT
"""
import logging
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.websocket import RecognizeCallback, AudioSource
from config import settings

logger = logging.getLogger(__name__)

class WatsonSTTService:
    """Servicio para transcripción de audio con Watson Speech to Text"""
    
    def __init__(self):
        """Inicializa el cliente de Watson STT"""
        try:
            authenticator = IAMAuthenticator(settings.WATSON_STT_API_KEY)
            self.speech_to_text = SpeechToTextV1(authenticator=authenticator)
            self.speech_to_text.set_service_url(settings.WATSON_STT_URL)
            logger.info("Watson STT Service inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar Watson STT: {str(e)}")
            raise
    
    def transcribe_audio(self, audio_file, content_type: str = "audio/mpeg") -> str:
        """
        Transcribe un archivo de audio a texto
        
        Args:
            audio_file: Archivo de audio (file-like object o bytes)
            content_type: Tipo MIME del audio (audio/mpeg, audio/wav, etc.)
        
        Returns:
            str: Texto transcrito del audio
        
        Raises:
            Exception: Si hay error en la transcripción
        """
        try:
            logger.info(f"Iniciando transcripción de audio (tipo: {content_type})")
            logger.info(f"Tipo de audio_file: {type(audio_file)}")
            
            # Si es bytes, obtener el tamaño
            if isinstance(audio_file, bytes):
                logger.info(f"Tamaño del audio en bytes: {len(audio_file)}")
            
            # Configurar parámetros de reconocimiento
            logger.info(f"Usando modelo: {settings.WATSON_STT_MODEL}")
            logger.info(f"URL de Watson: {settings.WATSON_STT_URL}")
            
            # Lista de content types para intentar (orden de prioridad)
            content_types_to_try = [content_type]
            
            # Si viene como WAV, probar también WebM y Ogg (formatos comunes en navegadores)
            if "wav" in content_type.lower():
                content_types_to_try.extend([
                    "audio/webm",
                    "audio/webm;codecs=opus",
                    "audio/ogg;codecs=opus",
                    "audio/mp4",
                    "audio/mpeg"
                ])
            
            last_error = None
            
            # Intentar con diferentes content types
            for ct in content_types_to_try:
                try:
                    logger.info(f"Intentando transcribir con content_type: {ct}")
                    
                    response = self.speech_to_text.recognize(
                        audio=audio_file,
                        content_type=ct,
                        model=settings.WATSON_STT_MODEL,
                        timestamps=False,
                        word_confidence=False,
                        smart_formatting=True,
                        speaker_labels=False
                    ).get_result()
                    
                    logger.info(f"✓ Respuesta de Watson recibida con {ct}")
                    
                    # Extraer el texto de la respuesta
                    if response and 'results' in response and len(response['results']) > 0:
                        transcripts = []
                        for result in response['results']:
                            if 'alternatives' in result and len(result['alternatives']) > 0:
                                transcript = result['alternatives'][0].get('transcript', '')
                                transcripts.append(transcript)
                        
                        full_text = ' '.join(transcripts).strip()
                        logger.info(f"✓ Transcripción exitosa con {ct}. Longitud: {len(full_text)} caracteres")
                        return full_text
                    else:
                        logger.warning(f"Watson STT no devolvió resultados con {ct}")
                
                except Exception as e:
                    error_msg = str(e)
                    logger.warning(f"✗ Falló con {ct}: {error_msg}")
                    last_error = e
                    # Si el error no es de formato, no intentar otros formatos
                    if "transcode" not in error_msg.lower():
                        raise
                    continue
            
            # Si llegamos aquí, ningún content type funcionó
            if last_error:
                raise last_error
            else:
                return ""
        
        except Exception as e:
            logger.error(f"Error en transcripción de Watson STT: {str(e)}")
            raise Exception(f"Error al transcribir audio: {str(e)}")
    
    def generate_title(self, text: str, max_words: int = 5) -> str:
        """
        Genera un título a partir del texto transcrito
        
        Args:
            text: Texto completo transcrito
            max_words: Número máximo de palabras para el título
        
        Returns:
            str: Título generado
        """
        if not text:
            return "Nota sin título"
        
        words = text.split()
        title_words = words[:max_words]
        title = ' '.join(title_words)
        
        # Si el texto es más largo que el título, agregar puntos suspensivos
        if len(words) > max_words:
            title += "..."
        
        logger.info(f"Título generado: {title}")
        return title

# Instancia global del servicio
watson_service = WatsonSTTService()
