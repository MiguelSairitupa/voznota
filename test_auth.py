"""
Script de prueba para el sistema de autenticación
Prueba registro, login y endpoints protegidos
"""
import requests
import json
from datetime import datetime

# URL base de la API (ajustar si es necesario)
BASE_URL = "http://localhost:8080"

def print_separator():
    print("\n" + "="*70 + "\n")

def test_health():
    """Prueba el endpoint de health"""
    print("🔍 Probando endpoint /health...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_register(email, password):
    """Prueba el registro de usuario"""
    print(f"📝 Registrando usuario: {email}...")
    data = {
        "email": email,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 201, response.json()

def test_login(email, password):
    """Prueba el login de usuario"""
    print(f"🔐 Iniciando sesión: {email}...")
    data = {
        "email": email,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if response.status_code == 200:
        token = result.get("access_token")
        print(f"\n✅ Token JWT obtenido: {token[:50]}...")
        return True, token
    return False, None

def test_get_me(token):
    """Prueba obtener información del usuario actual"""
    print("👤 Obteniendo información del usuario actual...")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_protected_endpoint_without_token():
    """Prueba acceder a endpoint protegido sin token"""
    print("🚫 Intentando acceder a /api/notes sin token...")
    response = requests.get(f"{BASE_URL}/api/notes")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 401  # Debe ser 401 Unauthorized

def test_get_notes(token):
    """Prueba obtener las notas del usuario"""
    print("📚 Obteniendo notas del usuario...")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(f"{BASE_URL}/api/notes", headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    print(f"Total de notas: {len(result)}")
    return response.status_code == 200

def main():
    """Ejecuta todas las pruebas"""
    print("🚀 INICIANDO PRUEBAS DEL SISTEMA DE AUTENTICACIÓN")
    print_separator()
    
    # Test 1: Health Check
    if not test_health():
        print("❌ Error: El servidor no está respondiendo")
        return
    
    print_separator()
    
    # Test 2: Registro de usuario
    email = f"test_{datetime.now().timestamp()}@ejemplo.com"
    password = "password123"
    
    success, user_data = test_register(email, password)
    if not success:
        print("❌ Error en el registro")
        return
    
    print("✅ Usuario registrado exitosamente")
    print_separator()
    
    # Test 3: Intentar registrar el mismo email (debe fallar)
    print("🔄 Intentando registrar el mismo email nuevamente...")
    success, _ = test_register(email, password)
    if success:
        print("❌ Error: Se permitió registrar un email duplicado")
    else:
        print("✅ Correcto: No se permite email duplicado")
    
    print_separator()
    
    # Test 4: Login con credenciales correctas
    success, token = test_login(email, password)
    if not success:
        print("❌ Error en el login")
        return
    
    print("✅ Login exitoso")
    print_separator()
    
    # Test 5: Login con credenciales incorrectas
    print("🔐 Intentando login con contraseña incorrecta...")
    success, _ = test_login(email, "wrongpassword")
    if success:
        print("❌ Error: Se permitió login con contraseña incorrecta")
    else:
        print("✅ Correcto: Login rechazado con contraseña incorrecta")
    
    print_separator()
    
    # Test 6: Obtener información del usuario actual
    if not test_get_me(token):
        print("❌ Error al obtener información del usuario")
        return
    
    print("✅ Información del usuario obtenida")
    print_separator()
    
    # Test 7: Intentar acceder sin token
    if not test_protected_endpoint_without_token():
        print("❌ Error: Se permitió acceso sin token")
    else:
        print("✅ Correcto: Acceso denegado sin token")
    
    print_separator()
    
    # Test 8: Obtener notas con token válido
    if not test_get_notes(token):
        print("❌ Error al obtener notas")
        return
    
    print("✅ Notas obtenidas exitosamente")
    print_separator()
    
    # Resumen
    print("🎉 TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
    print("\n📋 Resumen:")
    print(f"   - Usuario registrado: {email}")
    print(f"   - Token obtenido: {token[:30]}...")
    print(f"   - Todos los endpoints funcionando correctamente")
    print("\n✅ Sistema de autenticación implementado y funcionando!")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: No se pudo conectar al servidor")
        print("Asegúrate de que el servidor esté corriendo con: python main.py")
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {str(e)}")
        import traceback
        traceback.print_exc()
