import streamlit as st
import os
import tempfile
from docx import Document
from pypdf import PdfReader
from gtts import gTTS

st.set_page_config(page_title="OACI Versant Audio Generator", page_icon="✈️", layout="centered")

st.title("✈️ OACI VERSANT - AUDIO GENERATOR")
st.subheader("Creador de Podcast de Entrenamiento Manos Libres 🚶‍♂️")

st.markdown("""
    Genera **un único archivo de audio completo (MP3)** con todas tus frases y pausas integradas. 
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
            contenido = archivo_subido.read().decode("utf-8", errors="ignore")
            lineas_extraidas = contenido.splitlines()
        elif ext == "docx":
            doc = Document(archivo_subido)
            lineas_extraidas = [p.text for p in doc.paragraphs]
        elif ext == "pdf":
            reader = PdfReader(archivo_subido)
            for pagina in reader.pages:
                t_pag = pagina.extract_text()
                if t_pag: lineas_extraidas.extend(t_pag.splitlines())
        
        # Filtro estricto inicial
        lineas_finales = [l.strip() for l in lineas_extraidas if len(l.strip()) > 1]
        total_frases = len(lineas_finales)
        
        if total_frases > 0:
            st.success(f"✅ ¡Se detectaron {total_frases} frases listas para procesar!")
            
            # --- PASO 2: BOTÓN DE PROCESAMIENTO ---
            st.markdown("### ⚙️ 2. Generar pista de vuelo")
            if st.button("🔊 CREAR ARCHIVO COMPLETO DE AUDIO (MP3)", use_container_width=True):
                with st.spinner("Construyendo tu pista de entrenamiento... Espera un momento."):
                    
                    path_salida_final = os.path.join(tempfile.gettempdir(), "entrenamiento_oaci_completo.mp3")
                    fragmentos = []
                    
                    # Generar la pausa de silencio fija de forma ultra-segura
                    tmp_silencio = os.path.join(tempfile.gettempdir(), "silencia_pausa.mp3")
                    try:
                        tts_silencio = gTTS(text="ah.", lang="en") # Un sonido mínimo para asegurar que gTTS cree el archivo sin error
                        tts_silencio.save(tmp_silencio)
                    except Exception as e:
                        st.error(f"Error crítico al inicializar motor de audio: {e}")
                        st.stop()
                    
                    # Barra de progreso interna para ver en vivo cuál frase se está procesando
                    progreso_barra = st.progress(0, text="Procesando frases...")
                    
                    # Procesamos las frases una por una
                    for i, frase in enumerate(lineas_finales):
                        progreso_barra.progress((i + 1) / total_frases, text=f"Convirtiendo frase {i+1} de {total_frases}...")
                        
                        if not frase:
                            continue
                        
                        # FILTRO EXTREMO: Conservamos SOLO letras, números, espacios, puntos, comas y signos normales
                        frase_filtrada = "".join(
                            c for c in frase 
                            if c.isalnum() or c.isspace() or c in [".", ",", "?", "!", "'", "-"]
                        ).strip()
                        
                        # Si después del filtro la frase quedó vacía o demasiado corta, la ignoramos y seguimos
                        if len(frase_filtrada) < 2:
                            continue
                            
                        tmp_frase = os.path.join(tempfile.gettempdir(), f"f_{i}.mp3")
                        try:
                            # Intentamos generar el audio de la frase en inglés estándar
                            tts_vuelo = gTTS(text=frase_filtrada, lang="en", tld="com")
                            tts_vuelo.save(tmp_frase)
                            
                            # Si se guardó correctamente, la añadimos a la lista junto con su espacio para responder
                            if os.path.exists(tmp_frase) and os.path.getsize(tmp_frase) > 0:
                                fragmentos.append(tmp_frase)
                                fragmentos.append(tmp_silencio)
                        except:
                            # SI UNA FRASE DA ERROR, EL PROGRAMA SIMPLEMENTE LA IGNORA Y SIGUE CON LA SIGUIENTE
                            continue
                    
                    # Fusión de los archivos generados en un solo MP3 masivo
                    if fragmentos:
                        with open(path_salida_final, "wb") as archivo_destino:
                            for f_path in fragmentos:
                                with open(f_path, "rb") as f_origen:
                                    archivo_destino.write(f_origen.read())
                        
                        # Limpieza de archivos temporales individuales
                        for f_path in fragmentos:
                            try:
                                if "f_" in f_path:
                                    os.remove(f_path)
                            except: pass
                        try: os.remove(tmp_silencio)
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
                        st.error("No se pudo procesar ninguna frase del archivo. Verifica que contenga texto en inglés válido.")
        else:
            st.error("El archivo cargado no contiene texto válido o está vacío.")
    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
