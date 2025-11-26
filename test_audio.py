"""
Script de Prueba para VozNota API
Simula el envío de un archivo de audio desde el cliente Flutter
"""
import requests
import os
import sys
from pathlib import Path

# URL del servidor (cambiar si se despliega en otro lugar)
API_URL = "http://localhost:8080"

def test_health():
    """Prueba el endpoint de salud"""
    print("🔍 Probando endpoint de salud...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Servidor saludable")
            print(f"   Versión: {data.get('version')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Timestamp: {data.get('timestamp')}")
            return True
        else:
            print(f"❌ Error en health check: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ No se pudo conectar al servidor en {API_URL}")
        print(f"   Asegúrate de que el servidor está corriendo con: python main.py")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def test_transcription(audio_file_path: str):
    """
    Prueba el endpoint de transcripción
    
    Args:
        audio_file_path: Ruta al archivo de audio de prueba
    """
    print(f"\n🎤 Probando transcripción de audio...")
    print(f"   Archivo: {audio_file_path}")
    
    # Verificar que el archivo existe
    if not os.path.exists(audio_file_path):
        print(f"❌ El archivo no existe: {audio_file_path}")
        return False
    
    # Obtener información del archivo
    file_size = os.path.getsize(audio_file_path)
    file_ext = Path(audio_file_path).suffix.lower()
    
    print(f"   Tamaño: {file_size / 1024:.2f} KB")
    print(f"   Formato: {file_ext}")
    
    # Determinar content type
    content_type = "audio/mpeg" if file_ext == ".mp3" else "audio/wav"
    
    try:
        # Leer el archivo
        with open(audio_file_path, 'rb') as audio_file:
            files = {
                'audio': (os.path.basename(audio_file_path), audio_file, content_type)
            }
            
            print(f"\n📤 Enviando audio al servidor...")
            response = requests.post(
                f"{API_URL}/api/transcribe",
                files=files,
                timeout=60  # Timeout de 60 segundos
            )
        
        # Procesar respuesta
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Transcripción exitosa!")
            print(f"{'='*60}")
            print(f"📌 Título: {data.get('titulo')}")
            print(f"{'='*60}")
            print(f"📝 Texto completo:")
            print(f"   {data.get('texto')}")
            print(f"{'='*60}")
            print(f"🆔 ID Documento: {data.get('id_documento')}")
            print(f"📅 Fecha: {data.get('fecha')}")
            print(f"{'='*60}")
            return True
        else:
            print(f"\n❌ Error en la transcripción")
            print(f"   Código: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Error desconocido')}")
            except:
                print(f"   Respuesta: {response.text}")
            return False
    
    except requests.exceptions.Timeout:
        print(f"❌ Timeout: El servidor tardó demasiado en responder")
        print(f"   Esto puede ocurrir con archivos de audio muy largos")
        return False
    except Exception as e:
        print(f"❌ Error al enviar la solicitud: {str(e)}")
        return False

def find_audio_file():
    """Busca un archivo de audio de prueba"""
    sample_dir = Path(__file__).parent / "sample_audio"
    
    # Archivos de prueba comunes
    test_files = [
        sample_dir / "test.mp3",
        sample_dir / "test.wav",
        sample_dir / "sample.mp3",
        sample_dir / "sample.wav",
    ]
    
    # Buscar el primer archivo que existe
    for file_path in test_files:
        if file_path.exists():
            return str(file_path)
    
    # Si no encuentra ninguno, buscar cualquier archivo de audio en la carpeta
    if sample_dir.exists():
        for ext in ["*.mp3", "*.wav"]:
            files = list(sample_dir.glob(ext))
            if files:
                return str(files[0])
    
    return None

def main():
    """Función principal"""
    print("="*60)
    print("🎵 VozNota API - Script de Prueba")
    print("="*60)
    
    # 1. Probar salud del servidor
    if not test_health():
        print("\n⚠️  El servidor no está disponible. Inicialo con:")
        print("   python main.py")
        sys.exit(1)
    
    # 2. Buscar archivo de audio
    audio_file = None
    
    # Si se pasó un archivo como argumento
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
    else:
        # Buscar archivo automáticamente
        audio_file = find_audio_file()
    
    if not audio_file:
        print("\n⚠️  No se encontró ningún archivo de audio de prueba")
        print("\n📋 Opciones:")
        print("   1. Coloca un archivo test.mp3 o test.wav en sample_audio/")
        print("   2. Ejecuta: python test_audio.py ruta/a/tu/archivo.mp3")
        sys.exit(1)
    
    # 3. Probar transcripción
    success = test_transcription(audio_file)
    
    if success:
        print("\n✅ Todas las pruebas pasaron exitosamente!")
        print("\n💡 Próximos pasos:")
        print("   - Revisa la documentación en: http://localhost:8080/docs")
        print("   - Conecta tu app Flutter al endpoint: http://localhost:8080/api/transcribe")
    else:
        print("\n❌ Las pruebas fallaron")
        print("\n💡 Verifica:")
        print("   - Que las credenciales en .env sean correctas")
        print("   - Que el archivo de audio sea válido")
        print("   - Los logs del servidor para más detalles")
        sys.exit(1)

if __name__ == "__main__":
    main()
