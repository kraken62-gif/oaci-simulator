import streamlit as st
import os
import io
import math
import struct
from docx import Document
from pypdf import PdfReader
from gtts import gTTS

st.set_page_config(page_title="OACI Versant MP3 Generator", page_icon="✈️", layout="centered")

st.title("✈️ OACI VERSANT - AUDIO GENERATOR")
st.subheader("Creador de Simulaciones Reales en MP3 (Optimizado) 🚶‍♂️")

st.markdown("""
    Genera tu archivo de audio con **pitidos de examen y 10 segundos de silencio** por frase. 
    Esta versión está optimizada para archivos grandes (como tus listas de más de 180 frases), asegurando una descarga rápida y sin bloqueos.
    """)

# Generador matemático de Beeps nativos
def generar_bytes_beep(frecuencia, duracion_ms, sample_rate=24000):
    num_muestras = int(sample_rate * (duracion_ms / 1000.0))
    contenido = bytearray()
    # Cabecera WAV estándar
    contenido.extend(b'RIFF' + struct.pack('<I', 36 + num_muestras * 2) + b'WAVEfmt ' +
                     struct.pack('<IHHIIHH', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16) +
                     b'data' + struct.pack('<I', num_muestras * 2))
    for i in range(num_muestras):
        valor = int(32767.0 * math.sin(2.0 * math.pi * frecuencia * i / sample_rate))
        contenido.extend(struct.pack('<h', valor))
    return bytes(contenido)

# Generador matemático de Silencio puro
def generar_bytes_silencio(duracion_s, sample_rate=24000):
    num_muestras = int(sample_rate * duracion_s)
    contenido = bytearray()
    contenido.extend(b'RIFF' + struct.pack('<I', 36 + num_muestras * 2) + b'WAVEfmt ' +
                     struct.pack('<IHHIIHH', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16) +
                     b'data' + struct.pack('<I', num_muestras * 2))
    contenido.extend(b'\x00' * (num_muestras * 2))
    return bytes(contenido)

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
            
            # --- PASO 2: PROCESAMIENTO EN MEMORIA EN VIVO ---
            st.markdown("### ⚙️ 2. Construir simulación estructurada")
            if st.button("🔊 GENERAR SIMULADOR COMPLETO CON PITIDOS", use_container_width=True):
                
                # Usamos un buffer de memoria RAM en lugar de escribir archivos temporales en el disco duro lento
                buffer_maestro = io.BytesIO()
                
                with st.spinner("Ensamblando la pista en alta velocidad... Espera un momento."):
                    
                    # Pre-generar componentes fijos en bytes
                    bytes_pre_pausa = generar_bytes_silencio(1.0)      # 1 segundo espera post-frase
                    bytes_beep_in = generar_bytes_beep(880, 300)       # Pitido agudo iniciar
                    bytes_silencio_resp = generar_bytes_silencio(10.0)  # 10 SEGUNDOS REALES PARA QUE MILTON HABLE
                    bytes_beep_out = generar_bytes_beep(440, 250)      # Pitido grave terminar
                    
                    progreso_barra = st.progress(0, text="Procesando...")
                    
                    # Procesamiento estructurado secuencial
                    for i, frase in enumerate(lineas_finales):
                        progreso_barra.progress((i + 1) / total_frases, text=f"Estructurando frase {i+1} de {total_frases}...")
                        
                        frase_limpia = "".join(c for c in frase if c.isalnum() or c.isspace() or c in [".", ",", "?", "!"])
                        if len(frase_limpia.strip()) < 2:
                            continue
                        
                        try:
                            # Generar el audio de la frase directo a memoria
                            tts = gTTS(text=frase_limpia, lang="en", tld="com")
                            fp_temp = io.BytesIO()
                            tts.write_to_fp(fp_temp)
                            bytes_frase = fp_temp.getvalue()
                            
                            # Inyectar la secuencia exacta de examen de forma directa al flujo maestro
                            buffer_maestro.write(bytes_frase)
                            buffer_maestro.write(bytes_pre_pausa)
                            buffer_maestro.write(bytes_beep_in)
                            buffer_maestro.write(bytes_silencio_resp)
                            buffer_maestro.write(bytes_beep_out)
                        except:
                            continue
                    
                    # Obtener los datos binarios finales listos para enviar
                    pista_completa_bytes = buffer_maestro.getvalue()
                    
                    if len(pista_completa_bytes) > 0:
                        st.success("🚀 ¡Simulación estructurada creada y lista en caché!")
                        
                        # --- PASO 3: DESCARGA ULTRA-RÁPIDA ---
                        st.download_button(
                            label="📥 DESCARGAR AUDIO DE ENTRENAMIENTO (.MP3)",
                            data=pista_completa_bytes,
                            file_name="Simulador_Versant_10s.mp3",
                            mime="audio/mp3",
                            use_container_width=True
                        )
                    else:
                        st.error("Error al estructurar el flujo de datos de audio.")
        else:
            st.error("El archivo cargado no contiene texto válido o está vacío.")
    except Exception as e:
        st.error(f"Error general en el sistema: {e}")
