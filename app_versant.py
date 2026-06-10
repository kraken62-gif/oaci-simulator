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
            # MÉTODO ULTRA SEGURO: Extraemos el texto binario crudo del documento
            doc = Document(archivo_subido)
            for p in doc.paragraphs:
                # Limpiamos espacios en blanco, tabulaciones y caracteres extraños
                texto_limpio = p.text.strip()
                if texto_limpio:
                    lineas_extraidas.append(texto_limpio)
        elif ext == "pdf":
            reader = PdfReader(archivo_subido)
            for pagina in reader.pages:
                t_pag = pagina.extract_text()
                if t_pag: lineas_extraidas.extend(t_pag.splitlines())
        
        # Filtro final estricto: Eliminamos cualquier residuo vacío o menor a 2 caracteres
        lineas_finales = [l for l in lineas_extraidas if len(l.strip()) > 2]
        total_frases = len(lineas_finales)
        
        if total_frases > 0:
            st.success(f"✅ ¡Se detectaron {total_frases} frases listas para procesar!")
            
            # --- PASO 2: BOTÓN DE PROCESAMIENTO ---
            st.markdown("### ⚙️ 2. Generar pista de vuelo")
            if st.button("🔊 CREAR ARCHIVO COMPLETO DE AUDIO (MP3)", use_container_width=True):
                with st.spinner("Construyendo tu pista de entrenamiento... Esto puede tardar un momento dependiendo del tamaño del archivo."):
                    
                    path_salida_final = os.path.join(tempfile.gettempdir(), "entrenamiento_oaci_completo.mp3")
                    fragmentos = []
                    
                    # Generamos los componentes fijos de audio de forma segura
                    tmp_silencio = os.path.join(tempfile.gettempdir(), "silencio_5s.mp3")
                    gTTS(text="...", lang="en").save(tmp_silencio)
                    
                    tmp_beep_inicio = os.path.join(tempfile.gettempdir(), "beep_inicio.mp3")
                    gTTS(text="Now.", lang="en", tld="com").save(tmp_beep_inicio)
                    
                    tmp_beep_fin = os.path.join(tempfile.gettempdir(), "beep_fin.mp3")
                    gTTS(text="Change.", lang="en", tld="com").save(tmp_beep_fin)
                    
                    # Procesamos únicamente las frases válidas que superaron el filtro
                    for i, frase in enumerate(lineas_finales):
                        # Doble verificación por si acaso
                        if not frase or len(frase.strip()) <= 2:
                            continue
                            
                        tmp_frase = os.path.join(tempfile.gettempdir(), f"frase_{i}.mp3")
                        try:
                            # Forzamos a gTTS a ignorar cualquier símbolo raro limpiando la cadena
                            frase_filtrada = "".join(c for c in frase if c.isalnum() or c.isspace() or c in [',', '.', '?', '!'])
                            
                            if len(frase_filtrada.strip()) > 2:
                                gTTS(text=frase_filtrada, lang="en", tld="com").save(tmp_frase)
                                fragmentos.append(tmp_frase)
                                fragmentos.append(tmp_beep_inicio)
                                fragmentos.append(tmp_silencio)
                                fragmentos.append(tmp_beep_fin)
                        except:
                            continue
                    
                    # Fusión de los archivos generados
                    if fragmentos:
                        with open(path_salida_final, "wb") as archivo_destino:
                            for f_path in fragmentos:
                                with open(f_path, "rb") as f_origen:
                                    archivo_destino.write(f_origen.read())
                        
                        # Limpieza
                        for f_path in fragmentos:
                            try:
                                if "frase_" in f_path:
                                    os.remove(f_path)
                            except: pass
                        try:
                            os.remove(tmp_silencio)
                            os.remove(tmp_beep_inicio)
                            os.remove(tmp_beep_fin)
                        except: pass
                        
                        st.success("🚀 ¡Tu pista de audio manos libres ha sido generada con éxito!")
                        
                        # --- PASO 3: BOTÓN DE DESCARGA ---
                        with open(path_salida_final, "rb") as f_mp3:
                            st.download_button(
                                label="📥 DESCARGAR AUDIO DE ENTRENAMIENTO (.MP3)",
                                data=f_mp3.read(),
                                file_name="Entrenamiento_OACI_Versant.mp3",
                                mime="audio/mp3",
                                use_container_width=True
                            )
                    else:
                        st.error("No se pudo procesar ninguna frase del archivo debido al formato del texto.")
        else:
            st.error("El archivo cargado no contiene texto válido o está vacío.")
    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
