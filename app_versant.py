import streamlit as st
import os
import tempfile
import time
import numpy as np
from docx import Document
from pypdf import PdfReader
from gtts import gTTS
from scipy.io import wavfile

# Configuración de página móvil
st.set_page_config(page_title="OACI Versant Walk & Train", page_icon="✈️", layout="centered")

st.markdown("""
    <style>
    .big-font { font-size:22px !important; font-weight: bold; color: #2c3e50; text-align: center; }
    .status-font { font-size:26px !important; font-weight: bold; text-align: center; padding: 15px; border-radius: 8px; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# Función técnica para generar tonos puros (Beeps) en formato de audio compatible
def generar_array_beep(frecuencia, duracion_ms, sampl_rate=24000):
    t = np.linspace(0, duracion_ms / 1000, int(sampl_rate * (duracion_ms / 1000)), False)
    audio_beep = np.sin(frecuencia * t * 2 * np.pi)
    audio_int16 = (audio_beep * 32767).astype(np.int16)
    return audio_int16

st.title("✈️ OACI VERSANT - AUDIO TRAINER")
st.subheader("Piloto Automático de Audio Continuo 🚶‍♂️")

if 'lineas' not in st.session_state: st.session_state.lineas = []
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'fase' not in st.session_state: st.session_state.fase = "config"

# --- FASE 1: CARGA DE MATERIAL ---
if st.session_state.fase == "config":
    st.markdown("<p class='big-font'>📂 Carga tus frases de práctica</p>", unsafe_allow_html=True)
    archivo_subido = st.file_uploader("Soporta tus archivos .txt, .docx y .pdf", type=["txt", "docx", "pdf"])
    
    if archivo_subido is not None:
        lineas_extraidas = []
        ext = archivo_subido.name.split(".")[-1].lower()
        
        try:
            if ext == "txt":
                lineas_extraidas = archivo_subido.read().decode("utf-8").splitlines()
            elif ext == "docx":
                doc = Document(archivo_subido)
                lineas_extraidas = [p.text for p in doc.paragraphs if p.text.strip()]
            elif ext == "pdf":
                reader = PdfReader(archivo_subido)
                for pagina in reader.pages:
                    t_pag = pagina.extract_text()
                    if t_pag: lineas_extraidas.extend(t_pag.splitlines())
            
            st.session_state.lineas = [l.strip() for l in lineas_extraidas if l.strip()]
            
            if st.session_state.lineas:
                st.success(f"✅ ¡Se cargaron {len(st.session_state.lineas)} frases con éxito!")
                st.info("💡 Cómo usar en tus caminatas:\n1. Conecta tus audífonos.\n2. Presiona iniciar.\n3. Escucha la frase, espera el pitido agudo, repite en voz alta y el sistema pasará solo.")
                if st.button("🚀 INICIAR ENTRENAMIENTO MANOS LIBRES", use_container_width=True):
                    st.session_state.indice = 0
                    st.session_state.fase = "ejercicio"
                    st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# --- FASE 2: LOOP AUTOMÁTICO DE AUDIO FUSIONADO ---
elif st.session_state.fase == "ejercicio":
    total = len(st.session_state.lineas)
    idx = st.session_state.indice
    
    if idx < total:
        frase_objetivo = st.session_state.lineas[idx]
        
        st.progress((idx) / total, text=f"Progreso de Entrenamiento: Frase {idx + 1} de {total}")
        
        placeholder = st.empty()
        placeholder.markdown("<div class='status-font' style='background-color:#2c3e50; color:white;'>🔊 Generando Pista de Audio...</div>", unsafe_allow_html=True)
        
        # 1. Crear el audio de la frase en inglés (24kHz para consistencia de audio)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
            tts = gTTS(text=frase_objetivo, lang='en', tld='com')
            tts.save(tmp_mp3.name)
            path_mp3 = tmp_mp3.name
            
        # Convertir a formato WAV compatible para fusionar
        path_wav_frase = path_mp3.replace(".mp3", ".wav")
        os.system(f'python -c "from pydub import AudioSegment; AudioSegment.from_mp3(\'{path_mp3}\').set_frame_rate(24000).export(\'{path_wav_frase}\', format=\'wav\')"')
        
        sr_rate = 24000
        # Intentar leer la frase convertida, si falla usamos una aproximación limpia
        try:
            _, data_frase = wavfile.read(path_wav_frase)
            if len(data_frase.shape) > 1: data_frase = data_frase[:, 0]
        except:
            data_frase = np.zeros(int(sr_rate * 3), dtype=np.int16) # Respaldo silencioso
            
        # 2. Generar silencios y pitidos nativos en el mismo archivo
        silencio_corto = np.zeros(int(sr_rate * 1.2), dtype=np.int16)
        beep_inicio = generar_array_beep(frecuencia=900, duracion_ms=350, sampl_rate=sr_rate)
        silencio_grabacion = np.zeros(int(sr_rate * 5.0), dtype=np.int16) # 5 segundos reglamentarios para tu voz
        beep_fin = generar_array_beep(frecuencia=550, duracion_ms=250, sampl_rate=sr_rate)
        
        # 3. FUSIÓN TOTAL DE LA PISTA (Frase + Pausa + Beep Inicio + Tiempo Grabación + Beep Fin)
        pista_completa = np.concatenate([data_frase, silencio_corto, beep_inicio, silencio_grabacion, beep_fin])
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_final:
            wavfile.write(tmp_final.name, sr_rate, pista_completa)
            path_final = tmp_final.name
            
        # Mostrar interfaz limpia en tu caminata
        placeholder.markdown(f"<div class='status-font' style='background-color:#27ae60; color:white;'>🎧 ESCUCHA Y REPITE<br><br><span style='font-size:16px; font-weight:normal;'>\"{frase_objetivo}\"</span></div>", unsafe_allow_html=True)
        
        # Reproducción con autoplay nativo de HTML5
        with open(path_final, "rb") as f_wav:
            st.audio(f_wav.read(), format="audio/wav", autoplay=True)
            
        # Limpieza de temporales
        try:
            os.remove(path_mp3)
            os.remove(path_wav_frase)
            os.remove(path_final)
        except: pass
        
        # El sistema espera exactamente el tiempo que dura el audio completo antes de pasar solo a la siguiente
        duracion_total_segundos = len(pista_completa) / sr_rate
        time.sleep(duracion_total_segundos + 1.0)
        
        st.session_state.indice += 1
        st.rerun()
    else:
        st.session_state.fase = "final"
        st.rerun()

# --- FASE 3: FIN DE SESIÓN ---
elif st.session_state.fase == "final":
    st.balloons()
    st.markdown("<h2 style='text-align:center;'>📊 ¡Sesión Completada!</h2>", unsafe_allow_html=True)
    st.markdown("<div class='status-font' style='background-color:#34495e; color:white;'>Completaste con éxito todas las frases de tu documento de vuelo.</div>", unsafe_allow_html=True)
    
    if st.button("🔄 Cargar otra Lista de Frases", use_container_width=True):
        st.session_state.lineas = []
        st.session_state.indice = 0
        st.session_state.fase = "config"
        st.rerun()
