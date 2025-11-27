"""
Test directo de Watson STT para diagnosticar el problema
"""
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from dotenv import load_dotenv
import os

load_dotenv()

print("=" * 60)
print("TEST DE WATSON SPEECH TO TEXT")
print("=" * 60)

# Obtener credenciales
api_key = os.getenv("WATSON_STT_API_KEY")
url = os.getenv("WATSON_STT_URL")

print(f"\n📋 Configuración:")
print(f"   API Key: {api_key[:10]}...{api_key[-10:]}")
print(f"   URL: {url}")

try:
    print("\n🔄 Intentando conectar con Watson...")
    
    # Autenticar
    authenticator = IAMAuthenticator(api_key)
    speech_to_text = SpeechToTextV1(authenticator=authenticator)
    speech_to_text.set_service_url(url)
    
    # Listar modelos disponibles (test de conexión)
    print("📡 Obteniendo lista de modelos...")
    response = speech_to_text.list_models().get_result()
    
    print("\n✅ ¡Conexión exitosa!")
    print(f"   Modelos disponibles: {len(response['models'])}")
    
    # Buscar modelos en español
    spanish_models = [m for m in response['models'] if 'es-' in m['name']]
    print(f"\n🇪🇸 Modelos en español disponibles:")
    for model in spanish_models:
        print(f"   • {model['name']} - {model.get('description', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("✅ TEST EXITOSO - Watson está funcionando")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\n🔍 Posibles causas:")
    print("   1. API Key inválida o expirada")
    print("   2. URL incorrecta")
    print("   3. Servicio Watson desactivado en IBM Cloud")
    print("   4. Límite de plan excedido")
    print("\n💡 Solución:")
    print("   Ve a https://cloud.ibm.com/resources")
    print("   Verifica que el servicio Speech to Text esté activo")
    print("   Regenera las credenciales si es necesario")
