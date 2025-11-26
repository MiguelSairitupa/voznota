# VozNota API - Backend de Transcripción de Voz

Backend serverless para la aplicación **VozNota**, que transcribe audio a texto usando **IBM Watson Speech to Text** y almacena las transcripciones en **IBM Cloudant**.

## 🏗️ Arquitectura

```
Flutter App (Frontend) 
    ↓ (HTTP POST con audio)
FastAPI Backend (Python)
    ↓ (Transcripción)
IBM Watson STT (IA)
    ↓ (Guardar texto)
IBM Cloudant (Base de Datos NoSQL)
```

## 🚀 Características

- ✅ API REST con FastAPI
- ✅ Transcripción de audio con IBM Watson Speech to Text
- ✅ Almacenamiento en IBM Cloudant
- ✅ Generación automática de títulos
- ✅ Documentación interactiva (Swagger UI)
- ✅ Preparado para IBM Cloud Code Engine
- ✅ CORS configurado para Flutter
- ✅ Manejo robusto de errores
- ✅ Logging detallado

## 📋 Requisitos Previos

1. **Python 3.9+** instalado
2. **Cuenta de IBM Cloud** con servicios:
   - IBM Watson Speech to Text
   - IBM Cloudant
3. **Git** (opcional)

## 🔧 Instalación

### 1. Clonar o descargar el proyecto

```powershell
cd d:\voznota
```

### 2. Crear entorno virtual de Python

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y edítalo con tus credenciales:

```powershell
Copy-Item .env.example .env
notepad .env
```

**Configura las siguientes variables en `.env`:**

#### Watson Speech to Text:
```env
WATSON_STT_API_KEY=tu-api-key-aqui
WATSON_STT_URL=https://api.us-south.speech-to-text.watson.cloud.ibm.com
WATSON_STT_MODEL=es-ES_BroadbandModel
```

#### IBM Cloudant:
**⚠️ IMPORTANTE:** El formato debe ser exacto:
```env
CLOUDANT_URL=https://apikey:TU_API_KEY@tu-host.cloudantnosqldb.appdomain.cloud
CLOUDANT_DB_NAME=voznota_transcriptions
```

**NO uses** estos formatos incorrectos:
```env
# ❌ INCORRECTO - Solo la URL sin credenciales
CLOUDANT_URL=https://mi-servicio.cloudantnosqldb.appdomain.cloud

# ❌ INCORRECTO - Username en lugar de "apikey"
CLOUDANT_URL=https://usuario:password@mi-servicio.cloudantnosqldb.appdomain.cloud
```

**✅ CORRECTO:**
```env
# El formato debe incluir "apikey" literal, seguido de tu IAM API Key
CLOUDANT_URL=https://apikey:xyz789ABC123def456...@mi-servicio-123.cloudantnosqldb.appdomain.cloud
```

### 5. Obtener Credenciales de IBM Cloud

#### **Watson Speech to Text:**
1. Ir a [IBM Cloud Console](https://cloud.ibm.com/catalog/services/speech-to-text)
2. Crear instancia de Speech to Text
3. En "Manage" → "Service credentials" → crear credenciales si no existen
4. Copiar `apikey` y `url`

**Ejemplo de credenciales Watson:**
```json
{
  "apikey": "abc123XYZ456...",
  "url": "https://api.us-south.speech-to-text.watson.cloud.ibm.com"
}
```

En tu `.env`:
```env
WATSON_STT_API_KEY=abc123XYZ456...
WATSON_STT_URL=https://api.us-south.speech-to-text.watson.cloud.ibm.com
```

#### **Cloudant:**
1. Ir a [IBM Cloud Console](https://cloud.ibm.com/catalog/services/cloudant)
2. Crear instancia de Cloudant
3. En "Service credentials" → crear credenciales si no existen
4. Copiar `apikey` y `host` del JSON

**Ejemplo de credenciales Cloudant:**
```json
{
  "apikey": "xyz789ABC123...",
  "host": "mi-servicio-123.cloudantnosqldb.appdomain.cloud",
  "url": "https://mi-servicio-123.cloudantnosqldb.appdomain.cloud"
}
```

**⚠️ IMPORTANTE - Formato de CLOUDANT_URL:**

En tu `.env`, debes construir la URL así:
```env
CLOUDANT_URL=https://apikey:TU_IAM_API_KEY@TU_HOST
```

**Ejemplo real:**
```env
CLOUDANT_URL=https://apikey:xyz789ABC123...@mi-servicio-123.cloudantnosqldb.appdomain.cloud
```

Donde:
- `apikey` es **literal** (escríbelo tal cual)
- `xyz789ABC123...` es tu **apikey** del JSON de credenciales
- `mi-servicio-123.cloudantnosqldb.appdomain.cloud` es tu **host** del JSON

## ▶️ Ejecución

### Modo desarrollo:

```powershell
python main.py
```

O usando uvicorn directamente:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

El servidor estará disponible en: `http://localhost:8080`

### Documentación interactiva:

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## 🧪 Pruebas

### 1. Crear archivo de audio de prueba

**Opción A - Grabar con Windows:**
1. Abre **Grabadora de Voz** de Windows (búscala en el menú inicio)
2. Graba algo en español, por ejemplo:
   > "Esta es una prueba de transcripción de voz para la aplicación VozNota. El sistema utiliza IBM Watson Speech to Text."
3. Guarda el archivo como `test.wav` o `test.mp3`
4. Copia el archivo a la carpeta `sample_audio/`

**Opción B - Generar audio con Text-to-Speech online:**
1. Ve a https://ttsmp3.com/
2. Selecciona idioma: **Spanish (Español)**
3. Escribe un texto de prueba:
   > "Reunión con el equipo de desarrollo para discutir las nuevas características del producto y planificar el próximo sprint de trabajo"
4. Click en "Read" o "Descargar"
5. Guarda el archivo como `test.mp3` en la carpeta `sample_audio/`

**Opción C - Usar cualquier archivo MP3/WAV:**
- Copia cualquier archivo de audio en español a `sample_audio/`
- Formatos soportados: `.mp3`, `.wav`
- Tamaño máximo: 10 MB

### 2. Ejecutar script de prueba

Abre **otra terminal** (mantén el servidor corriendo) y ejecuta:

```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Ejecutar pruebas
python test_audio.py
```

El script automáticamente:
1. ✅ Verifica que el servidor esté corriendo
2. ✅ Busca archivos de audio en `sample_audio/`
3. ✅ Envía el audio al endpoint `/api/transcribe`
4. ✅ Muestra el título, texto transcrito e ID del documento

**Ejemplo de salida exitosa:**
```
============================================================
🎵 VozNota API - Script de Prueba
============================================================
🔍 Probando endpoint de salud...
✅ Servidor saludable
   Versión: 1.0.0
   Status: healthy

🎤 Probando transcripción de audio...
   Archivo: D:\voznota\sample_audio\test.mp3
   Tamaño: 42.5 KB
   Formato: .mp3

📤 Enviando audio al servidor...

✅ Transcripción exitosa!
============================================================
📌 Título: Reunión con el equipo de...
============================================================
📝 Texto completo:
   Reunión con el equipo de desarrollo para discutir las nuevas características del producto.
============================================================
🆔 ID Documento: abc123def456
📅 Fecha: 2025-11-25T18:42:00
============================================================
```

### 3. Probar con archivo específico

```powershell
python test_audio.py sample_audio/mi_audio.mp3
```

### 4. Probar manualmente con cURL

```powershell
curl.exe -X POST "http://localhost:8080/api/transcribe" `
  -H "accept: application/json" `
  -H "Content-Type: multipart/form-data" `
  -F "audio=@sample_audio/test.mp3"
```

## 📡 API Endpoints

### `GET /`
Información general de la API

### `GET /health`
Verificación de salud del servicio

**Respuesta:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-25T10:30:00"
}
```

### `POST /api/transcribe`
Transcribe un archivo de audio

**Request:**
- Tipo: `multipart/form-data`
- Campo: `audio` (archivo WAV o MP3, máx. 10 MB)

**Respuesta exitosa (200):**
```json
{
  "titulo": "Reunión con el equipo de...",
  "texto": "Reunión con el equipo de desarrollo para discutir las nuevas características del producto.",
  "id_documento": "abc123def456",
  "fecha": "2025-11-25T10:30:00"
}
```

**Errores:**
- `400`: Formato de audio inválido o archivo muy grande
- `500`: Error en Watson STT o Cloudant

## 📁 Estructura del Proyecto

```
voznota/
├── main.py                      # Aplicación FastAPI principal
├── config.py                    # Configuración y variables de entorno
├── models.py                    # Modelos Pydantic
├── requirements.txt             # Dependencias Python
├── .env.example                 # Plantilla de variables de entorno
├── .env                         # Variables de entorno (NO versionar)
├── README.md                    # Este archivo
├── test_audio.py                # Script de prueba
├── services/
│   ├── watson_service.py        # Servicio de Watson STT
│   └── cloudant_service.py      # Servicio de Cloudant
└── sample_audio/
    └── test.mp3                 # Audio de prueba
```

## 🚢 Despliegue en IBM Cloud Code Engine

### 1. Crear Dockerfile (opcional):

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 2. Desplegar en Code Engine:

```bash
ibmcloud ce application create --name voznota-api \
  --image python:3.9 \
  --build-source . \
  --port 8080 \
  --env WATSON_STT_API_KEY=tu-key \
  --env WATSON_STT_URL=tu-url \
  --env CLOUDANT_URL=tu-cloudant-url
```

## 🔒 Seguridad

- ❌ **NO** versionar el archivo `.env` con credenciales reales
- ✅ Usar variables de entorno en Code Engine
- ✅ Configurar CORS solo para dominios permitidos en producción
- ✅ Limitar tamaño de archivos (10 MB por defecto)

## 🛠️ Tecnologías Utilizadas

- **FastAPI** - Framework web asíncrono de alto rendimiento
- **Uvicorn** - Servidor ASGI para aplicaciones Python asíncronas
- **IBM Watson Speech to Text** - Servicio de IA para transcripción de audio
- **IBM Cloudant** - Base de datos NoSQL basada en CouchDB
- **Pydantic** - Validación de datos con type hints
- **Python-dotenv** - Manejo de variables de entorno

## 📝 Notas Importantes

- El modelo de lenguaje por defecto es español (`es-ES_BroadbandModel`)
- Los títulos se generan automáticamente con las primeras 5 palabras del texto
- La base de datos en Cloudant se crea automáticamente si no existe
- Los archivos permitidos son: **WAV** y **MP3**
- Tamaño máximo de archivo: **10 MB**
- El servidor usa **CORS** configurado para permitir conexiones desde Flutter

## 🐛 Troubleshooting

### Error: "WATSON_STT_API_KEY no está configurada"
**Solución:** Verifica que el archivo `.env` existe y contiene las credenciales correctas de Watson.

### Error: "The username and password shouldn't be None"
**Solución:** La URL de Cloudant no tiene el formato correcto. Debe ser:
```env
CLOUDANT_URL=https://apikey:TU_IAM_API_KEY@tu-host.cloudantnosqldb.appdomain.cloud
```
Ver sección "Obtener Credenciales de IBM Cloud" más arriba.

### Error: "Import could not be resolved"
**Solución:** 
```powershell
# Activa el entorno virtual
.\venv\Scripts\Activate.ps1

# Instala las dependencias
pip install -r requirements.txt
```

### Error: "Connection refused" o "Cannot connect to server"
**Solución:** Verifica que:
1. Las URLs de Watson y Cloudant en `.env` sean correctas
2. Tu conexión a Internet esté funcionando
3. Las credenciales de IBM Cloud sean válidas

### El script de prueba dice "No se encontró archivo de audio"
**Solución:** Coloca un archivo `test.mp3` o `test.wav` en la carpeta `sample_audio/`, o especifica la ruta:
```powershell
python test_audio.py ruta/al/archivo.mp3
```

### Error: "Cannot install requirements.txt - dependency conflict"
**Solución:** El archivo `requirements.txt` ya está actualizado para evitar conflictos. Asegúrate de usar la versión más reciente y ejecuta:
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

## 📞 Soporte

Para problemas o dudas:
- Revisa la documentación de [IBM Watson](https://cloud.ibm.com/docs/speech-to-text)
- Revisa la documentación de [IBM Cloudant](https://cloud.ibm.com/docs/Cloudant)
- Revisa la documentación de [FastAPI](https://fastapi.tiangolo.com/)

---

**VozNota API** - Transcripción de voz inteligente con IBM Watson 🎤→📝
