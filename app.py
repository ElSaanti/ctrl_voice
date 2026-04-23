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
    global estado_led
    msg = str(message.payload.decode("utf-8"))
    st.write("Respuesta desde Wokwi:", msg)

    if "ON" in msg:
        estado_led = "ENCENDIDO"
    elif "OFF" in msg:
        estado_led = "APAGADO"

broker = "broker.mqttdashboard.com"
port = 1883
topic = "voice_ctrl"

client1 = paho.Client("GIT-HUBC")
client1.on_message = on_message
client1.connect(broker, port)
client1.subscribe(topic)

# ---------------- UI ----------------
st.title("INTERFACES MULTIMODALES")
st.subheader("CONTROL POR VOZ + WOKWI")

image = Image.open('voice_ctrl.jpg')
st.image(image, width=200)

# Estado visual
if "estado_led" not in st.session_state:
    st.session_state.estado_led = "APAGADO"

st.markdown("### Estado del dispositivo")

if st.session_state.estado_led == "ENCENDIDO":
    st.success("LED ENCENDIDO")
else:
    st.error("LED APAGADO")

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

    # Interpretación simple
    if "encender" in texto:
        mensaje = "ON"
        st.session_state.estado_led = "ENCENDIDO"
    elif "apagar" in texto:
        mensaje = "OFF"
        st.session_state.estado_led = "APAGADO"
    else:
        mensaje = texto

    payload = json.dumps({"cmd": mensaje})
    client1.publish(topic, payload)

# ---------------- BOTONES MANUALES ----------------
st.markdown("### Control manual")

col1, col2 = st.columns(2)

if col1.button("Encender"):
    client1.publish(topic, json.dumps({"cmd": "ON"}))
    st.session_state.estado_led = "ENCENDIDO"

if col2.button("Apagar"):
    client1.publish(topic, json.dumps({"cmd": "OFF"}))
    st.session_state.estado_led = "APAGADO"

# ---------------- INSTRUCCIONES ----------------
st.markdown("## Cómo conectarlo con Wokwi")

st.markdown("""
1. Abre Wokwi y crea un proyecto con ESP32  
2. Agrega un LED al pin 2  
3. Usa la librería WiFi y PubSubClient  
4. Conéctate al broker: broker.mqttdashboard.com  
5. Suscríbete al topic: voice_ctrl  
6. Si recibes "ON" → enciende LED  
7. Si recibes "OFF" → apaga LED  
""")
