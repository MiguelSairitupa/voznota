"""
Script para generar una clave secreta segura para JWT
"""
import secrets

def generate_secret_key():
    """Genera una clave secreta aleatoria segura"""
    return secrets.token_urlsafe(32)

if __name__ == "__main__":
    secret_key = generate_secret_key()
    print("="*60)
    print("  JWT SECRET KEY GENERADA")
    print("="*60)
    print()
    print("Copia esta clave y agrégala como variable de entorno en Code Engine:")
    print()
    print(f"JWT_SECRET_KEY={secret_key}")
    print()
    print("⚠️  IMPORTANTE: Guarda esta clave en un lugar seguro!")
    print("   No la compartas ni la subas a Git")
    print()
