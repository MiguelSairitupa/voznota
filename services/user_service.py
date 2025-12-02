"""
Servicio de gestión de usuarios
Maneja el registro, autenticación y gestión de usuarios en Cloudant
"""
import logging
from datetime import datetime
from typing import Optional
from passlib.context import CryptContext
from ibmcloudant.cloudant_v1 import CloudantV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
from config import settings

logger = logging.getLogger(__name__)

# Configuración de bcrypt para hash de passwords
# Configuración más robusta que maneja mejor los límites de bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b"
)

class UserService:
    """Servicio para gestión de usuarios en Cloudant"""
    
    def __init__(self):
        """Inicializa el cliente de Cloudant para usuarios"""
        try:
            cloudant_url = settings.CLOUDANT_URL
            
            if not cloudant_url:
                raise ValueError("CLOUDANT_URL no está configurada")
            
            from urllib.parse import urlparse
            parsed = urlparse(cloudant_url)
            
            logger.info(f"Inicializando UserService con Cloudant: {parsed.hostname}")
            
            if parsed.username and parsed.password:
                if parsed.username == 'apikey':
                    authenticator = IAMAuthenticator(parsed.password)
                else:
                    from ibm_cloud_sdk_core.authenticators import BasicAuthenticator
                    authenticator = BasicAuthenticator(parsed.username, parsed.password)
                
                service_url = f"{parsed.scheme}://{parsed.hostname}"
                if parsed.port:
                    service_url += f":{parsed.port}"
            else:
                raise ValueError(
                    "CLOUDANT_URL debe incluir credenciales. "
                    "Formato: https://apikey:TU_API_KEY@tu-instancia.cloudantnosqldb.appdomain.cloud"
                )
            
            self.client = CloudantV1(authenticator=authenticator)
            self.client.set_service_url(service_url)
            self.db_name = settings.USERS_DB_NAME
            
            # Crear la base de datos de usuarios si no existe
            self._ensure_database_exists()
            
            # Crear índice para búsqueda por email
            self._create_email_index()
            
            logger.info(f"UserService inicializado. DB: {self.db_name}")
        except Exception as e:
            logger.error(f"Error al inicializar UserService: {str(e)}")
            raise
    
    def _ensure_database_exists(self):
        """Verifica que la base de datos existe, si no, la crea"""
        try:
            self.client.get_database_information(db=self.db_name).get_result()
            logger.info(f"Base de datos '{self.db_name}' existe")
        except ApiException as e:
            if e.code == 404:
                logger.info(f"Creando base de datos '{self.db_name}'...")
                self.client.put_database(db=self.db_name).get_result()
                logger.info(f"Base de datos '{self.db_name}' creada exitosamente")
            else:
                raise
    
    def _create_email_index(self):
        """Crea un índice para búsqueda eficiente por email"""
        try:
            index = {
                "index": {
                    "fields": ["email"]
                },
                "name": "email-index",
                "type": "json"
            }
            
            self.client.post_index(
                db=self.db_name,
                index=index["index"],
                name=index["name"],
                type=index["type"]
            ).get_result()
            
            logger.info("Índice de email creado exitosamente")
        except ApiException as e:
            # Si el índice ya existe, ignorar el error
            if "already exists" in str(e).lower() or e.code == 409:
                logger.info("Índice de email ya existe")
            else:
                logger.warning(f"No se pudo crear índice de email: {str(e)}")
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Genera hash de la contraseña usando bcrypt"""
        # Bcrypt tiene un límite de 72 bytes, truncar si es necesario
        # Convertir a bytes y truncar ANTES de pasar a bcrypt
        if len(password.encode('utf-8')) > 72:
            password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica si la contraseña coincide con el hash"""
        # Truncar la contraseña de la misma forma que al hashear
        if len(plain_password.encode('utf-8')) > 72:
            plain_password = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_user_by_email(self, email: str) -> Optional[dict]:
        """
        Busca un usuario por email
        
        Args:
            email: Email del usuario
        
        Returns:
            dict: Usuario encontrado o None
        """
        try:
            # Usar find con el índice de email
            selector = {"email": email}
            
            response = self.client.post_find(
                db=self.db_name,
                selector=selector,
                limit=1
            ).get_result()
            
            docs = response.get('docs', [])
            
            if docs:
                return docs[0]
            return None
        
        except Exception as e:
            logger.error(f"Error al buscar usuario por email {email}: {str(e)}")
            raise
    
    def create_user(self, email: str, password: str) -> dict:
        """
        Crea un nuevo usuario
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
        
        Returns:
            dict: Usuario creado (sin password)
        
        Raises:
            ValueError: Si el email ya existe
            Exception: Si hay error al crear
        """
        try:
            # Verificar si el email ya existe
            existing_user = self.get_user_by_email(email)
            if existing_user:
                raise ValueError(f"El email {email} ya está registrado")
            
            # Truncar contraseña ANTES de hashear (límite de bcrypt)
            password_to_hash = password
            if len(password.encode('utf-8')) > 72:
                password_to_hash = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
            
            # Hash de la contraseña
            hashed_password = self.hash_password(password_to_hash)
            
            # Crear documento de usuario
            user_doc = {
                "email": email,
                "hashed_password": hashed_password,
                "created_at": datetime.now().isoformat(),
                "is_active": True
            }
            
            logger.info(f"Creando usuario: {email}")
            
            # Guardar en Cloudant
            response = self.client.post_document(
                db=self.db_name,
                document=user_doc
            ).get_result()
            
            user_id = response.get('id', '')
            
            logger.info(f"Usuario creado exitosamente. ID: {user_id}")
            
            # Retornar usuario sin password
            return {
                "_id": user_id,
                "email": email,
                "created_at": user_doc["created_at"],
                "is_active": user_doc["is_active"]
            }
        
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error al crear usuario: {str(e)}")
            raise Exception(f"Error al crear usuario: {str(e)}")
    
    def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """
        Autentica un usuario verificando email y contraseña
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
        
        Returns:
            dict: Usuario autenticado (sin password) o None si falla
        """
        try:
            user = self.get_user_by_email(email)
            
            if not user:
                logger.warning(f"Usuario no encontrado: {email}")
                return None
            
            # Verificar contraseña
            if not self.verify_password(password, user.get("hashed_password", "")):
                logger.warning(f"Contraseña incorrecta para: {email}")
                return None
            
            # Verificar que el usuario esté activo
            if not user.get("is_active", False):
                logger.warning(f"Usuario inactivo: {email}")
                return None
            
            logger.info(f"Usuario autenticado exitosamente: {email}")
            
            # Retornar usuario sin password
            return {
                "_id": user.get("_id"),
                "email": user.get("email"),
                "created_at": user.get("created_at"),
                "is_active": user.get("is_active")
            }
        
        except Exception as e:
            logger.error(f"Error al autenticar usuario: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """
        Obtiene un usuario por su ID
        
        Args:
            user_id: ID del usuario
        
        Returns:
            dict: Usuario encontrado (sin password) o None
        """
        try:
            user = self.client.get_document(
                db=self.db_name,
                doc_id=user_id
            ).get_result()
            
            # Retornar sin password
            return {
                "_id": user.get("_id"),
                "email": user.get("email"),
                "created_at": user.get("created_at"),
                "is_active": user.get("is_active")
            }
        
        except ApiException as e:
            if e.code == 404:
                return None
            raise
        except Exception as e:
            logger.error(f"Error al obtener usuario {user_id}: {str(e)}")
            raise

# Instancia global del servicio
user_service = UserService()
