"""
Servicio de autenticación JWT
Maneja la creación y validación de tokens JWT
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings
from models import TokenData, UserResponse
from services.user_service import user_service

logger = logging.getLogger(__name__)

# Esquema de seguridad Bearer Token
security = HTTPBearer()

class AuthService:
    """Servicio de autenticación con JWT"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crea un token JWT
        
        Args:
            data: Datos a codificar en el token
            expires_delta: Tiempo de expiración del token
        
        Returns:
            str: Token JWT generado
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> TokenData:
        """
        Verifica y decodifica un token JWT
        
        Args:
            token: Token JWT a verificar
        
        Returns:
            TokenData: Datos decodificados del token
        
        Raises:
            HTTPException: Si el token es inválido
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudieron validar las credenciales",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            
            if user_id is None:
                raise credentials_exception
            
            token_data = TokenData(user_id=user_id, email=email)
            return token_data
        
        except JWTError as e:
            logger.error(f"Error al verificar token JWT: {str(e)}")
            raise credentials_exception
    
    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> UserResponse:
        """
        Obtiene el usuario actual desde el token JWT
        
        Args:
            credentials: Credenciales HTTP Bearer del header Authorization
        
        Returns:
            UserResponse: Usuario actual autenticado
        
        Raises:
            HTTPException: Si el token es inválido o el usuario no existe
        """
        token = credentials.credentials
        
        # Verificar el token
        token_data = auth_service.verify_token(token)
        
        # Obtener usuario desde Cloudant
        user = user_service.get_user_by_id(token_data.user_id)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return UserResponse(
            id=user["_id"],
            email=user["email"],
            created_at=user["created_at"],
            is_active=user["is_active"]
        )
    
    @staticmethod
    async def get_current_active_user(
        current_user: UserResponse = Depends(get_current_user)
    ) -> UserResponse:
        """
        Obtiene el usuario actual y verifica que esté activo
        
        Args:
            current_user: Usuario actual desde get_current_user
        
        Returns:
            UserResponse: Usuario actual activo
        
        Raises:
            HTTPException: Si el usuario está inactivo
        """
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario inactivo"
            )
        return current_user

# Instancia global del servicio
auth_service = AuthService()

# Dependencia para obtener el usuario actual
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserResponse:
    """Dependencia para inyectar en endpoints protegidos"""
    return await AuthService.get_current_user(credentials)

# Dependencia para obtener el usuario actual activo
async def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """Dependencia para endpoints que requieren usuario activo"""
    return await AuthService.get_current_active_user(current_user)
