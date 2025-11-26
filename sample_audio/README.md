# Archivos de Audio de Prueba

Esta carpeta contiene archivos de audio para probar la API de VozNota.

## 📁 Instrucciones

Coloca aquí tus archivos de audio de prueba en formato:
- **MP3** (audio/mpeg)
- **WAV** (audio/wav)

## 🎤 Archivos Recomendados

Puedes crear archivos de prueba con nombres como:
- `test.mp3`
- `test.wav`
- `sample.mp3`
- `sample.wav`

## 🔊 Crear Audio de Prueba

### Opción 1: Grabar con tu micrófono
Usa la grabadora de voz de Windows o cualquier app de grabación.

### Opción 2: Texto a Voz Online
Puedes usar servicios gratuitos como:
- https://ttsmp3.com/
- https://www.naturalreaders.com/online/

Genera un audio en español diciendo algo como:
> "Esta es una prueba de transcripción de voz para la aplicación VozNota. El sistema utiliza IBM Watson Speech to Text para convertir audio en texto."

### Opción 3: Descargar Audio de Prueba
Puedes usar archivos de audio libre de derechos desde:
- https://freesound.org/

## 📏 Limitaciones

- Tamaño máximo: **10 MB**
- Formatos permitidos: **MP3, WAV**
- Idioma recomendado: **Español**

## 🧪 Uso en Pruebas

El script `test_audio.py` buscará automáticamente archivos en esta carpeta con los nombres mencionados arriba.

```powershell
# Probar con archivo automático
python test_audio.py

# Probar con archivo específico
python test_audio.py sample_audio/mi_audio.mp3
```
