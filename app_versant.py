import streamlit as st
import os
import tempfile
import time
from docx import Document
from pypdf import PdfReader
from gtts import gTTS
import streamlit.components.v1 as components

# Configuración de página móvil limpia
st.set_page_config(page_title="OACI Versant Simulator", page_icon="✈️", layout="centered")

st.markdown("""
    <style>
    .big-font { font-size:22px !important; font-weight: bold; color: #2c3e50; text-align: center; }
    .status-font { font-size:26px !important; font-weight: bold; text-align: center; padding: 15px; border-radius: 8px; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

st.title("✈️ OACI VERSANT SIMULATOR")
st.subheader("Piloto Automático por Tiempos 🚶‍♂️")

if 'lineas' not in st.session_state: st.session_state.lineas = []
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'fase' not in st.session_state: st.session_state.fase = "config"

# --- FASE 1: CARGA DE MATERIAL ---
if st.session_state.fase == "config":
    st.markdown("<p class='big-font'>📂 Carga tus frases de práctica (.txt, .docx, .pdf)</p>", unsafe_allow_html=True)
    archivo_subido = st.file_uploader("Sube tu archivo de estudio aquí", type=["txt", "docx", "pdf"])
    
    if archivo_subido is not None:
        lineas_extraidas = []
        ext = archivo_subido.name.split(".")[-1].lower()
        
        try:
            if ext == "txt":
                lineas_extraidas = archivo_subido.read().decode("utf-8", errors="ignore").splitlines()
            elif ext == "docx":
                doc = Document(archivo_subido)
                lineas_extraidas = [p.text for p in doc.paragraphs]
            elif ext == "pdf":
                reader = PdfReader(archivo_subido)
                for pagina in reader.pages:
                    t_pag = pagina.extract_text()
                    if t_pag: lineas_extraidas.extend(t_pag.splitlines())
            
            st.session_state.lineas = [l.strip() for l in lineas_extraidas if len(l.strip()) > 2]
            
            if st.session_state.lineas:
                st.success(f"✅ ¡Se cargaron {len(st.session_state.lineas)} frases con éxito!")
                
                # INYECTOR JAVASCRIPT: Fuerza al navegador móvil a pedir permiso de micrófono e iniciar el contexto de audio
                components.html("""
                    <script>
                    window.parent.document.addEventListener('click', function() {
                        navigator.mediaDevices.getUserMedia({ audio: true })
                        .then(function(stream) { console.log('Microfono desbloqueado'); })
                        .catch(function(err) { console.log('Error o rechazo: ' + err); });
                    }, { once: true });
                    </script>
                """, height=0)
                
                st.info("💡 IMPORTANTE: Al presionar el botón de abajo, tu celular te pedirá permiso para usar el micrófono. Dale a 'PERMITIR' para que los pitidos y el sistema funcionen en segundo plano.")
                
                if st.button("🚀 INICIAR SIMULACIÓN MANOS LIBRES", use_container_width=True):
                    st.session_state.indice = 0
                    st.session_state.fase = "ejercicio"
                    st.rerun()
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

# --- FASE 2: BUCLE AUTOMÁTICO ORIGINAL ---
elif st.session_state.fase == "ejercicio":
    total = len(st.session_state.lineas)
    idx = st.session_state.indice
    
    if idx < total:
        frase_objetivo = st.session_state.lineas[idx]
        
        st.progress((idx) / total, text=f"Frase {idx + 1} de {total}")
        
        # Generar el audio de la frase actual con Google TTS
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
            tts = gTTS(text=frase_objetivo, lang='en', tld='com')
            tts.save(tmp_mp3.name)
            path_mp3 = tmp_mp3.name
            
        st.markdown(f"<div class='status-font' style='background-color:#2c3e50; color:white;'>🔊 ESCUCHA ATENTAMENTE</div>", unsafe_allow_html=True)
        
        # Reproducir la frase con autoplay nativo
        with open(path_mp3, "rb") as f_mp3:
            st.audio(f_mp3.read(), format="audio/mp3", autoplay=True)
            
        try: os.remove(path_mp3)
        except: pass
        
        # Tiempo de espera estimado para que termine de hablar la IA (calculado según el largo del texto)
        tiempo_habla = max(3.0, len(frase_objetivo) * 0.09)
        time.sleep(tiempo_habla)
        
        # PITIDO VIRTUAL DE EXAMEN (Generado por el navegador gracias al permiso desbloqueado)
        components.html("""
            <script>
            // Forzar la creación del pitido electrónico real en el auricular del celular
            var context = new (window.AudioContext || window.webkitAudioContext)();
            var osc = context.createOscillator();
            var gain = context.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(900, context.currentTime); // Tono agudo de examen
            gain.gain.setValueAtTime(0.3, context.currentTime);
            osc.connect(gain);
            gain.connect(context.destination);
            osc.start();
            setTimeout(function() { osc.stop(); context.close(); }, 300); // Duración de 300ms
            </script>
        """, height=0)
        
        st.markdown(f"<div class='status-font' style='background-color:#27ae60; color:white;'>🎙️ RESPONDE AHORA<br><span style='font-size:14px; font-weight:normal;'>(10 segundos libres)</span></div>", unsafe_allow_html=True)
        
        # ⏱️ TUS 10 SEGUNDOS SOLICITADOS PARA RESPONDER
        time.sleep(10.0)
        
        # PITIDO GRAVE DE FIN DE FRASE
        components.html("""
            <script>
            var context = new (window.AudioContext || window.webkitAudioContext)();
            var osc = context.createOscillator();
            var gain = context.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(450, context.currentTime); // Tono grave de cierre
            gain.gain.setValueAtTime(0.2, context.currentTime);
            osc.connect(gain);
            gain.connect(context.destination);
            osc.start();
            setTimeout(function() { osc.stop(); context.close(); }, 200);
            </script>
        """, height=0)
        
        time.sleep(0.5) # Pequeña pausa de transición
        
        # Avanzar automáticamente a la siguiente frase sin intervención
        st.session_state.indice += 1
        st.rerun()
    else:
        st.session_state.fase = "final"
        st.rerun()

# --- FASE 3: FIN DE SESIÓN ---
elif st.session_state.fase == "final":
    st.balloons()
    st.markdown("<h2 style='text-align:center;'>📊 ¡Práctica Concluida!</h2>", unsafe_allow_html=True)
    st.markdown("<div class='status-font' style='background-color:#34495e; color:white;'>Completaste con éxito tu lista de frases manos libres.</div>", unsafe_allow_html=True)
    
    if st.button("🔄 Cargar otra lista", use_container_width=True):
        st.session_state.lineas = []
        st.session_state.indice = 0
        st.session_state.fase = "config"
        st.rerun()
