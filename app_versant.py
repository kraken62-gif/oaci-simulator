import streamlit as st
import os
import tempfile
from docx import Document
from pypdf import PdfReader
from gtts import gTTS

# Configuración de página móvil limpia
st.set_page_config(page_title="OACI Versant Audio Generator", page_icon="✈️", layout="centered")

st.title("✈️ OACI VERSANT - AUDIO GENERATOR")
st.subheader("Creador de Podcast de Entrenamiento Manos Libres 🚶‍♂️")

st.markdown("""
    Este sistema soluciona el bloqueo de los celulares generando **un único archivo de audio completo (MP3)** con todas tus frases, pitidos y pausas de respuesta integrados. 
    Descárgalo en tu dispositivo, dale Play en tu reproductor de música y entrena sin tocar la pantalla.
    """)

# --- PASO 1: CARGA DE ARCHIVOS ---
st.markdown("### 📂 1. Sube tu material de estudio")
archivo_subido = st.file_uploader("Soporta formatos .txt, .docx y .pdf", type=["txt", "docx", "pdf"])

if archivo_subido is not None:
    lineas_extraidas = []
    ext = archivo_subido.name.split(".")[-1].lower()
    
    try:
        if ext == "txt":
            lineas_extraidas = archivo_subido.read().decode("utf-8").splitlines()
        elif ext == "docx":
            doc = Document(archivo_subido)
            lineas_extraidas = [p.text for p in doc.paragraphs]
        elif ext == "pdf":
            reader = PdfReader(archivo_subido)
            for pagina in reader.pages:
                t_pag = pagina.extract_text()
                if t_pag: lineas_extraidas.extend(t_pag.splitlines())
        
        # FILTRO DE SEGURIDAD: Solo dejamos líneas que tengan texto real (así eliminamos espacios vacíos dañinos)
        lineas_finales = [l.strip() for l in lineas_extraidas if l.strip()]
        total_frases = len(lineas_finales)
        
        if total_frases > 0:
            st.success(f"✅ ¡Se detectaron {total_frases} frases listas para procesar!")
            
            # --- PASO 2: BOTÓN DE PROCESAMIENTO ---
            st.markdown("### ⚙️ 2. Generar pista de vuelo")
            if st.button("🔊 CREAR ARCHIVO COMPLETO DE AUDIO (MP3)", use_container_width=True):
                with st.spinner("Construyendo tu pista de entrenamiento... Esto puede tardar un momento dependiendo del tamaño del archivo."):
                    
                    # Creamos un archivo temporal para ir uniendo todo el audio en formato MP3 limpio
                    path_salida_final = os.path.join(tempfile.gettempdir(), "entrenamiento_oaci_completo.mp3")
                    
                    # Lista temporal para guardar las rutas de los fragmentos de audio
                    fragmentos = []
                    
                    # Generamos un archivo de silencio corto usando una técnica limpia de gTTS leyendo puntuación
                    tmp_silencio = os.path.join(tempfile.gettempdir(), "silencio_5s.mp3")
                    tts_silencio = gTTS(text="...", lang="en") 
                    tts_silencio.save(tmp_silencio)
                    
                    # Generamos las alertas de voz claras para tus audífonos ("Now" para hablar / "Change" para parar)
                    tmp_beep_inicio = os.path.join(tempfile.gettempdir(), "beep_inicio.mp3")
                    gTTS(text="Now.", lang="en", tld="com").save(tmp_beep_inicio)
                    
                    tmp_beep_fin = os.path.join(tempfile.gettempdir(), "beep_fin.mp3")
                    gTTS(text="Change.", lang="en", tld="com").save(tmp_beep_fin)
                    
                    # Procesamos cada una de las frases filtradas del documento
                    for i, frase in enumerate(lineas_finales):
                        # Control extra: si por alguna razón la frase está vacía aquí, la saltamos
                        if not frase:
                            continue
                            
                        tmp_frase = os.path.join(tempfile.gettempdir(), f"frase_{i}.mp3")
                        try:
                            gTTS(text=frase, lang="en", tld="com").save(tmp_frase)
                            fragmentos.append(tmp_frase)
                            
                            # Agregamos las alertas y el espacio para responder
                            fragmentos.append(tmp_beep_inicio)
                            fragmentos.append(tmp_silencio)
                            fragmentos.append(tmp_beep_fin)
                        except Exception as e:
                            # Si una frase específica falla, el programa continúa con las demás sin colgarse
                            continue
                    
                    # Fusión binaria directa de los fragmentos generados
                    if fragmentos:
                        with open(path_salida_final, "wb") as archivo_destino:
                            for f_path in fragmentos:
                                with open(f_path, "rb") as f_origen:
                                    archivo_destino.write(f_origen.read())
                        
                        # Limpieza de archivos individuales intermedios
                        for f_path in fragmentos:
                            try:
                                if "frase_" in f_path: # Solo borramos las frases temporales
                                    os.remove(f_path)
                            except: pass
                        try:
                            os.remove(tmp_silencio)
                            os.remove(tmp_beep_inicio)
                            os.remove(tmp_beep_fin)
                        except: pass
                        
                        st.success("🚀 ¡Tu pista de audio manos libres ha sido generada con éxito!")
                        
                        # --- PASO 3: BOTÓN DE DESCARGA DIRECTA ---
                        with open(path_salida_final, "rb") as f_mp3:
                            st.download_button(
                                label="📥 DESCARGAR AUDIO DE ENTRENAMIENTO (.MP3)",
                                data=f_mp3.read(),
                                file_name="Entrenamiento_OACI_Versant.mp3",
                                mime="audio/mp3",
                                use_container_width=True
                            )
                    else:
                        st.error("No se pudo procesar ninguna frase del archivo.")
        else:
            st.error("El archivo cargado no contiene texto válido o está vacío.")
    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
