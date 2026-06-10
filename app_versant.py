import streamlit as st
import os
import tempfile
import math
import struct
from docx import Document
from pypdf import PdfReader
from gtts import gTTS

st.set_page_config(page_title="OACI Versant Simulator MP3", page_icon="✈️", layout="centered")

st.title("✈️ OACI VERSANT - AUDIO GENERATOR")
st.subheader("Creador de Simulaciones Reales en MP3 🚶‍♂️")

st.markdown("""
    Este sistema genera un archivo de audio con **pitidos reales de examen y 10 segundos de silencio** después de cada frase. Descárgalo y utilízalo en tu reproductor de música favorito para entrenar manos libres.
    """)

# Función interna para generar Beeps reales matemáticos sin depender de APIs externas
def crear_wave_beep(frecuencia, duracion_ms, archivo_path, sample_rate=24000):
    num_muestras = int(sample_rate * (duracion_ms / 1000.0))
    with open(archivo_path, "wb") as f:
        f.write(b'RIFF' + struct.pack('<I', 36 + num_muestras * 2) + b'WAVEfmt ' +
                struct.pack('<IHHIIHH', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16) +
                b'data' + struct.pack('<I', num_muestras * 2))
        for i in range(num_muestras):
            valor = int(32767.0 * math.sin(2.0 * math.pi * frecuencia * i / sample_rate))
            f.write(struct.pack('<h', valor))

# Función interna para crear bloques de silencio absoluto
def crear_wave_silencio(duracion_s, archivo_path, sample_rate=24000):
    num_muestras = int(sample_rate * duracion_s)
    with open(archivo_path, "wb") as f:
        f.write(b'RIFF' + struct.pack('<I', 36 + num_muestras * 2) + b'WAVEfmt ' +
                struct.pack('<IHHIIHH', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16) +
                b'data' + struct.pack('<I', num_muestras * 2))
        f.write(b'\x00' * (num_muestras * 2))

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
        
        lineas_finales = [l.strip() for l in lineas_extraidas if len(l.strip()) > 2]
        total_frases = len(lineas_finales)
        
        if total_frases > 0:
            st.success(f"✅ ¡Se detectaron {total_frases} frases listas para la simulación!")
            
            # --- PASO 2: PROCESAMIENTO ---
            st.markdown("### ⚙️ 2. Construir simulación estructurada")
            if st.button("🔊 GENERAR SIMULADOR COMPLETO CON PITIDOS", use_container_width=True):
                with st.spinner("Fusionando audios, beeps y silencios reglamentarios... Espera un momento."):
                    
                    path_salida_final = os.path.join(tempfile.gettempdir(), "simulacion_oaci_real.mp3")
                    fragmentos = []
                    
                    # 1. Generar componentes fijos de control
                    tmp_pre_pausa = os.path.join(tempfile.gettempdir(), "pre_pausa.wav")
                    crear_wave_silencio(1.0, tmp_pre_pausa) # 1 segundo de espera inicial
                    
                    tmp_beep_in = os.path.join(tempfile.gettempdir(), "beep_in.wav")
                    crear_wave_beep(880, 300, tmp_beep_in) # Tono agudo (880Hz) de 300ms
                    
                    tmp_silencio_resp = os.path.join(tempfile.gettempdir(), "silencio_resp.wav")
                    crear_wave_silencio(10.0, tmp_silencio_resp) # 🛑 ¡AHORA SON 10 SEGUNDOS DE SILENCIO REAL!
                    
                    tmp_beep_out = os.path.join(tempfile.gettempdir(), "beep_out.wav")
                    crear_wave_beep(440, 250, tmp_beep_out) # Tono grave (440Hz) de 250ms
                    
                    progreso_barra = st.progress(0, text="Procesando...")
                    
                    # 2. Bucle de procesamiento estructurado
                    for i, frase in enumerate(lineas_finales):
                        progreso_barra.progress((i + 1) / total_frases, text=f"Estructurando frase {i+1} de {total_frases}...")
                        
                        frase_limpia = "".join(c for c in frase if c.isalnum() or c.isspace() or c in [".", ",", "?", "!"])
                        if len(frase_limpia.strip()) < 2:
                            continue
                            
                        # Generar frase en formato temporal
                        tmp_frase_mp3 = os.path.join(tempfile.gettempdir(), f"frase_{i}.mp3")
                        
                        try:
                            tts = gTTS(text=frase_limpia, lang="en", tld="com")
                            tts.save(tmp_frase_mp3)
                            
                            # Agregamos la secuencia en orden exacto de examen
                            fragmentos.append(tmp_frase_mp3)    # Dice la frase en inglés
                            fragmentos.append(tmp_pre_pausa)     # Pausa corta
                            fragmentos.append(tmp_beep_in)       # ¡BEEP AGUDO! (Empieza a hablar)
                            fragmentos.append(tmp_silencio_resp) # 10 segundos de silencio para responder
                            fragmentos.append(tmp_beep_out)      # ¡BEEP GRAVE! (Fin de la frase)
                        except:
                            continue
                    
                    # 3. Fusión total en la pista maestra
                    if fragmentos:
                        with open(path_salida_final, "wb") as archivo_destino:
                            for f_path in fragmentos:
                                with open(f_path, "rb") as f_origen:
                                    archivo_destino.write(f_origen.read())
                        
                        # Limpieza profunda de archivos residuales
                        for f_path in fragmentos:
                            try:
                                if "frase_" in f_path: os.remove(f_path)
                            except: pass
                        try:
                            os.remove(tmp_pre_pausa)
                            os.remove(tmp_beep_in)
                            os.remove(tmp_silencio_resp)
                            os.remove(tmp_beep_out)
                        except: pass
                        
                        st.success("🚀 ¡Simulación estructurada creada con éxito!")
                        
                        # --- PASO 3: DESCARGA ---
                        with open(path_salida_final, "rb") as f_mp3:
                            st.download_button(
                                label="📥 DESCARGAR AUDIO DE ENTRENAMIENTO (.MP3)",
                                data=f_mp3.read(),
                                file_name="Simulador_Versant_10Segundos.mp3",
                                mime="audio/mp3",
                                use_container_width=True
                            )
                    else:
                        st.error("Error al estructurar las pistas de audio.")
        else:
            st.error("El archivo cargado no contiene texto válido o está vacío.")
    except Exception as e:
        st.error(f"Error general en el sistema: {e}")
