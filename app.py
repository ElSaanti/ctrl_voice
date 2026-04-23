import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import time
import paho.mqtt.client as paho
import json

# ---------------- MQTT ----------------
def on_publish(client, userdata, result):
    print("el dato ha sido publicado")

def on_message(client, userdata, message):
    msg = str(message.payload.decode("utf-8"))
    st.write("Respuesta desde Wokwi:", msg)

broker = "broker.mqttdashboard.com"
port = 1883
topic = "voice_ctrl"

client1 = paho.Client("GIT-HUBC")
client1.on_message = on_message
client1.connect(broker, port)
client1.subscribe(topic)

# ---------------- UI ----------------
st.title("INTERFACES MULTIMODALES")
st.subheader("CONTROL POR VOZ + SERVO (WOKWI)")

image = Image.open('voice_ctrl.jpg')

col1, col2 = st.columns(2)

with col1:
    st.image(image, width=200)

with col2:
    st.markdown("### Control por voz en tiempo real")

# Estado del servo
if "angulo" not in st.session_state:
    st.session_state.angulo = 0

st.markdown("### Estado del servo")

st.progress(st.session_state.angulo / 100)
st.metric("Ángulo del servo", f"{st.session_state.angulo}°")

st.write("Toca el botón y habla")

# ---------------- BOTÓN VOZ ----------------
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

# ---------------- PROCESAMIENTO ----------------
if result and "GET_TEXT" in result:
    texto = result.get("GET_TEXT").strip().lower()
    st.write("Comando:", texto)

    client1.on_publish = on_publish

    if "abrir" in texto:
        mensaje = "0"
        st.session_state.angulo = 0

    elif "cerrar" in texto:
        mensaje = "90"
        st.session_state.angulo = 90

    elif "medio" in texto:
        mensaje = "45"
        st.session_state.angulo = 45

    else:
        mensaje = "0"

    payload = json.dumps({"cmd": mensaje})
    client1.publish(topic, payload)

# ---------------- INSTRUCCIONES ----------------
st.markdown("## Cómo funciona con Wokwi")

st.markdown("""
1. Presionas el botón y hablas  
2. El sistema interpreta el comando  
3. Se envía un ángulo por MQTT  
4. El ESP32 en Wokwi mueve el servo  
""")
