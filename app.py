import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import time
import glob
import paho.mqtt.client as paho
import json
from gtts import gTTS
from googletrans import Translator

# ---------------- MQTT ----------------
def on_publish(client, userdata, result):
    print("el dato ha sido publicado \n")

def on_message(client, userdata, message):
    global message_received
    message_received = str(message.payload.decode("utf-8"))
    st.write("Mensaje recibido:", message_received)

broker = "broker.mqttdashboard.com"
port = 1883
client1 = paho.Client("GIT-HUBC")
client1.on_message = on_message

# ---------------- UI ----------------
st.title("INTERFACES MULTIMODALES")
st.subheader("CONTROL POR VOZ + RESPUESTA")

image = Image.open('voice_ctrl.jpg')
st.image(image, width=200)

st.write("Toca el botón y habla")

# Historial en sesión
if "historial" not in st.session_state:
    st.session_state.historial = []

# Selector de idioma
idioma = st.selectbox("Traducir a:", ["es", "en", "fr", "de"])

stt_button = Button(label="Inicio", width=200)

stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = function (e) {
        var value = e.results[0][0].transcript;
        if (value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    recognition.start();
"""))

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0
)

# ---------------- Lógica principal ----------------
if result and "GET_TEXT" in result:

    texto = result.get("GET_TEXT").strip()
    st.write("Texto detectado:", texto)

    # Guardar historial
    st.session_state.historial.append(texto)

    # Traducción
    translator = Translator()
    traduccion = translator.translate(texto, dest=idioma).text

    st.write("Traducción:", traduccion)

    # Enviar por MQTT
    client1.on_publish = on_publish
    client1.connect(broker, port)
    message = json.dumps({"Act1": texto})
    client1.publish("voice_ctrl", message)

    # Generar audio
    tts = gTTS(traduccion, lang=idioma)
    if not os.path.exists("temp"):
        os.mkdir("temp")

    audio_path = "temp/audio.mp3"
    tts.save(audio_path)

    # Reproducir audio
    audio_file = open(audio_path, 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3')

# ---------------- Historial ----------------
st.subheader("Historial de comandos")
for i, cmd in enumerate(reversed(st.session_state.historial)):
    st.write(f"{i+1}. {cmd}")
