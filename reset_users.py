"""
Script para limpiar/resetear la base de datos de usuarios
Útil para testing y desarrollo
"""
from services.cloudant_service import CloudantService
from config import settings

def reset_users_database():
    """Elimina y recrea la base de datos de usuarios"""
    print("🔄 Reseteando base de datos de usuarios...")
    
    try:
        # Crear instancia del servicio con la DB de usuarios
        cloudant = CloudantService()
        
        # Nombre de la base de datos de usuarios
        users_db = settings.USERS_DB_NAME
        
        print(f"📊 Base de datos: {users_db}")
        
        # Intentar eliminar la base de datos
        try:
            cloudant.client.delete_database(db=users_db).get_result()
            print(f"✅ Base de datos '{users_db}' eliminada")
        except Exception as e:
            print(f"⚠️  No se pudo eliminar (quizás no existe): {str(e)}")
        
        # Recrear la base de datos
        try:
            cloudant.client.put_database(db=users_db).get_result()
            print(f"✅ Base de datos '{users_db}' creada exitosamente")
        except Exception as e:
            print(f"❌ Error al crear base de datos: {str(e)}")
            return False
        
        print("\n✅ Base de datos de usuarios reseteada exitosamente")
        print("💡 Ahora puedes registrar usuarios nuevamente")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("  RESET DE BASE DE DATOS DE USUARIOS")
    print("="*60)
    print()
    
    confirm = input("⚠️  Esto eliminará TODOS los usuarios. ¿Continuar? (si/no): ")
    
    if confirm.lower() in ['si', 's', 'yes', 'y']:
        reset_users_database()
    else:
        print("❌ Operación cancelada")
