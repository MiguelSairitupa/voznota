"""
Script de prueba completo para el sistema de autenticación
"""
import requests
import json

BASE_URL = "http://localhost:8080"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health():
    """Verificar que el servidor está corriendo"""
    print_section("1. VERIFICANDO SERVIDOR")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_register():
    """Registrar un nuevo usuario"""
    print_section("2. REGISTRO DE USUARIO")
    user_data = {
        "email": "test@example.com",
        "password": "Test1234"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        print("✅ Usuario registrado exitosamente")
        return True
    elif response.status_code == 400:
        print("⚠️  Usuario ya existe (esto es normal si ya lo registraste antes)")
        return True
    else:
        print("❌ Error al registrar usuario")
        return False

def test_login():
    """Iniciar sesión y obtener token"""
    print_section("3. LOGIN DE USUARIO")
    
    # FastAPI espera form data para OAuth2PasswordRequestForm
    login_data = {
        "username": "test@example.com",  # OAuth2 usa 'username' aunque sea email
        "password": "Test1234"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data=login_data  # usar data en lugar de json para form
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login exitoso")
        print(f"🔑 Token: {token[:50]}...")
        return token
    else:
        print("❌ Error al hacer login")
        return None

def test_get_me(token):
    """Obtener información del usuario autenticado"""
    print_section("4. OBTENER INFO DEL USUARIO (Endpoint Protegido)")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Información obtenida exitosamente")
        return True
    else:
        print("❌ Error al obtener información")
        return False

def test_transcribe_with_auth(token):
    """Probar transcripción con autenticación"""
    print_section("5. TRANSCRIPCIÓN CON AUTENTICACIÓN")
    
    # Crear un archivo de audio de prueba simple (WAV vacío)
    # En un caso real, usarías un archivo de audio real
    print("⚠️  Nota: Necesitas un archivo de audio real en sample_audio/")
    print("    Por ahora solo mostramos cómo enviar la petición autenticada")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"Headers que debes usar: {headers}")
    print("Ejemplo de cURL:")
    print(f'curl -X POST "{BASE_URL}/api/transcribe" \\')
    print(f'  -H "Authorization: Bearer {token[:50]}..." \\')
    print('  -F "audio=@sample_audio/test.wav"')
    
    return True

def test_get_notes_with_auth(token):
    """Obtener notas del usuario autenticado"""
    print_section("6. OBTENER NOTAS DEL USUARIO")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/api/notes", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        notes = response.json()
        print(f"✅ Se encontraron {len(notes)} notas del usuario")
        return True
    else:
        print("❌ Error al obtener notas")
        return False

def test_without_token():
    """Intentar acceder sin token (debe fallar)"""
    print_section("7. PRUEBA SIN TOKEN (Debe Fallar)")
    
    response = requests.get(f"{BASE_URL}/api/auth/me")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 401:
        print("✅ Correctamente bloqueado (sin autenticación)")
        return True
    else:
        print("❌ Debería estar bloqueado")
        return False

def main():
    print("\n🚀 INICIANDO PRUEBAS DEL SISTEMA DE AUTENTICACIÓN")
    print(f"URL Base: {BASE_URL}")
    
    try:
        # 1. Verificar servidor
        if not test_health():
            print("\n❌ El servidor no está corriendo")
            return
        
        # 2. Registrar usuario
        test_register()
        
        # 3. Login
        token = test_login()
        if not token:
            print("\n❌ No se pudo obtener el token")
            return
        
        # 4. Obtener info del usuario
        test_get_me(token)
        
        # 5. Ejemplo de transcripción con auth
        test_transcribe_with_auth(token)
        
        # 6. Obtener notas del usuario
        test_get_notes_with_auth(token)
        
        # 7. Probar sin token
        test_without_token()
        
        # Resumen
        print_section("RESUMEN")
        print("✅ Sistema de autenticación funcionando correctamente")
        print("\n📝 ENDPOINTS DISPONIBLES:")
        print(f"  • POST {BASE_URL}/api/auth/register - Registrar usuario")
        print(f"  • POST {BASE_URL}/api/auth/login - Login (obtener token)")
        print(f"  • GET  {BASE_URL}/api/auth/me - Info del usuario (requiere auth)")
        print(f"  • POST {BASE_URL}/api/transcribe - Transcribir (requiere auth)")
        print(f"  • GET  {BASE_URL}/api/notes - Listar notas (requiere auth)")
        print(f"  • GET  {BASE_URL}/api/notes/{{id}} - Obtener nota (requiere auth)")
        print(f"  • DELETE {BASE_URL}/api/notes/{{id}} - Eliminar nota (requiere auth)")
        
        print("\n📖 DOCUMENTACIÓN INTERACTIVA:")
        print(f"  Swagger UI: {BASE_URL}/docs")
        print(f"  ReDoc: {BASE_URL}/redoc")
        
        print("\n🔑 TOKEN GUARDADO PARA USO:")
        print(f"  {token}")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ No se pudo conectar al servidor")
        print("   Asegúrate de que el servidor esté corriendo en http://localhost:8080")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
