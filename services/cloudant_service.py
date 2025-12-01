"""
Servicio de IBM Cloudant
Maneja la persistencia de transcripciones en la base de datos NoSQL
"""
import logging
from datetime import datetime
from ibmcloudant.cloudant_v1 import CloudantV1, Document
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
from config import settings
from models import TranscriptionDocument

logger = logging.getLogger(__name__)

class CloudantService:
    """Servicio para gestión de documentos en IBM Cloudant"""
    
    def __init__(self):
        """Inicializa el cliente de Cloudant"""
        try:
            cloudant_url = settings.CLOUDANT_URL
            
            # Validar que la URL no esté vacía
            if not cloudant_url:
                raise ValueError("CLOUDANT_URL no está configurada en las variables de entorno")
            
            # Parsear URL de Cloudant para obtener credenciales
            # Formatos soportados:
            # 1. https://apikey:password@hostname
            # 2. https://username:password@hostname
            # 3. URL completa de Cloudant
            from urllib.parse import urlparse
            parsed = urlparse(cloudant_url)
            
            logger.info(f"Conectando a Cloudant: {parsed.hostname}")
            
            # Determinar el tipo de autenticación basado en el formato de la URL
            if parsed.username and parsed.password:
                # Hay credenciales en la URL
                if parsed.username == 'apikey':
                    # Formato: https://apikey:IAM_API_KEY@hostname
                    logger.info("Usando IAM Authentication con API Key")
                    authenticator = IAMAuthenticator(parsed.password)
                else:
                    # Formato legacy: https://username:password@hostname
                    logger.info("Usando Basic Authentication (Legacy)")
                    from ibm_cloud_sdk_core.authenticators import BasicAuthenticator
                    authenticator = BasicAuthenticator(parsed.username, parsed.password)
                
                service_url = f"{parsed.scheme}://{parsed.hostname}"
                if parsed.port:
                    service_url += f":{parsed.port}"
            else:
                # No hay credenciales en la URL, asumir que es una URL con IAM
                raise ValueError(
                    "CLOUDANT_URL debe incluir credenciales. "
                    "Formato esperado: https://apikey:TU_API_KEY@tu-instancia.cloudantnosqldb.appdomain.cloud"
                )
            
            self.client = CloudantV1(authenticator=authenticator)
            self.client.set_service_url(service_url)
            self.db_name = settings.CLOUDANT_DB_NAME
            
            # Crear la base de datos si no existe
            self._ensure_database_exists()
            
            logger.info(f"Cloudant Service inicializado correctamente. DB: {self.db_name}")
        except Exception as e:
            logger.error(f"Error al inicializar Cloudant: {str(e)}")
            raise
    
    def _ensure_database_exists(self):
        """Verifica que la base de datos existe, si no, la crea"""
        try:
            # Intentar obtener información de la base de datos
            self.client.get_database_information(db=self.db_name).get_result()
            logger.info(f"Base de datos '{self.db_name}' existe")
        except ApiException as e:
            if e.code == 404:
                # La base de datos no existe, crearla
                logger.info(f"Creando base de datos '{self.db_name}'...")
                self.client.put_database(db=self.db_name).get_result()
                logger.info(f"Base de datos '{self.db_name}' creada exitosamente")
            else:
                raise
    
    def save_transcription(
        self, 
        titulo: str, 
        texto: str,
        user_id: str,
        audio_format: str = None,
        audio_size: int = None
    ) -> str:
        """
        Guarda una transcripción en Cloudant
        
        Args:
            titulo: Título de la nota
            texto: Texto completo transcrito
            user_id: ID del usuario dueño de la transcripción
            audio_format: Formato del audio original
            audio_size: Tamaño del archivo de audio en bytes
        
        Returns:
            str: ID del documento creado
        
        Raises:
            Exception: Si hay error al guardar
        """
        try:
            # Crear documento con timestamp en hora local
            fecha = datetime.now().isoformat()
            
            document = {
                "user_id": user_id,
                "titulo": titulo,
                "texto": texto,
                "fecha": fecha,
                "audio_format": audio_format,
                "audio_size": audio_size
            }
            
            logger.info(f"Guardando transcripción en Cloudant: {titulo} (usuario: {user_id})")
            
            # Guardar documento
            response = self.client.post_document(
                db=self.db_name,
                document=document
            ).get_result()
            
            doc_id = response.get('id', '')
            logger.info(f"Transcripción guardada exitosamente. ID: {doc_id}")
            
            return doc_id
        
        except Exception as e:
            logger.error(f"Error al guardar en Cloudant: {str(e)}")
            raise Exception(f"Error al guardar transcripción: {str(e)}")
    
    def get_transcription(self, doc_id: str) -> dict:
        """
        Obtiene una transcripción por ID
        
        Args:
            doc_id: ID del documento
        
        Returns:
            dict: Documento completo
        """
        try:
            document = self.client.get_document(
                db=self.db_name,
                doc_id=doc_id
            ).get_result()
            
            return document
        except Exception as e:
            logger.error(f"Error al obtener documento {doc_id}: {str(e)}")
            raise
    
    def list_transcriptions(self, user_id: str = None, limit: int = 100) -> list:
        """
        Lista todas las transcripciones, opcionalmente filtradas por usuario
        
        Args:
            user_id: ID del usuario (opcional, si se proporciona filtra por usuario)
            limit: Número máximo de documentos a devolver
        
        Returns:
            list: Lista de transcripciones
        """
        try:
            if user_id:
                # Filtrar por user_id usando find
                selector = {"user_id": user_id}
                response = self.client.post_find(
                    db=self.db_name,
                    selector=selector,
                    limit=limit
                ).get_result()
                
                documents = response.get('docs', [])
            else:
                # Listar todos los documentos
                response = self.client.post_all_docs(
                    db=self.db_name,
                    include_docs=True,
                    limit=limit
                ).get_result()
                
                documents = [row['doc'] for row in response.get('rows', [])]
            
            return documents
        except Exception as e:
            logger.error(f"Error al listar transcripciones: {str(e)}")
            raise
    
    def delete_transcription(self, doc_id: str, rev: str) -> bool:
        """
        Elimina una transcripción por ID
        
        Args:
            doc_id: ID del documento
            rev: Revisión del documento (_rev)
        
        Returns:
            bool: True si se eliminó exitosamente
        
        Raises:
            Exception: Si hay error al eliminar
        """
        try:
            logger.info(f"Eliminando documento {doc_id} (rev: {rev})")
            
            response = self.client.delete_document(
                db=self.db_name,
                doc_id=doc_id,
                rev=rev
            ).get_result()
            
            if response.get('ok'):
                logger.info(f"Documento {doc_id} eliminado exitosamente")
                return True
            else:
                raise Exception(f"La eliminación no fue exitosa: {response}")
        
        except Exception as e:
            logger.error(f"Error al eliminar documento {doc_id}: {str(e)}")
            raise Exception(f"Error al eliminar transcripción: {str(e)}")

# Instancia global del servicio
cloudant_service = CloudantService()
