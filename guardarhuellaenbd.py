from machine import UART, Pin
import time
import urequests
import ubinascii
import libreriafingerprint as fingerprint
import network
import random

# Wi-Fi connection details

codigo= 7326457
SSID = 'placa-2'
PASSWORD = '12345678'

# Function to connect to Wi-Fi
def connect_to_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print('Connected to Wi-Fi:', wlan.ifconfig())

# Connect to Wi-Fi
connect_to_wifi(SSID, PASSWORD)
# Configuración del UART y el sensor AS608
uart = UART(2, baudrate=57600, tx=17, rx=16)
time.sleep(1)
sensor = fingerprint.PyFingerprint(uart)


if sensor.verifyPassword():
    print("Sensor initialized and ready.")
    system_params = sensor.getSystemParameters()
else:
    print("Sensor initialization failed.")
    
sensor.setMaxPacketSize(32)  # Start with 32, then try 64 or 128 if issues persist
    

def capturar_y_convertir(char_buffer):
    
    
    print("Por favor, coloca tu dedo en el sensor...")
    while not sensor.readImage():
        time.sleep(2)
        print("Intentando capturar la imagen...")

    if sensor.convertImage(char_buffer):
        print("Imagen capturada y convertida correctamente.")
        time.sleep(2)
        return True
    else:
        print("Error al convertir la imagen.")
        return False
def enviar_huella_a_servidor(template):
    url = "http://192.168.2.193/TESISLAUTAROCOLLINO/TESTINGLOGIN/public/guardarhuella"
    # Reemplaza con la IP de tu PC
    headers = {'Content-Type': 'application/json'}
    data = {'template': template}
    
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print("Error: ESP32 is not connected to Wi-Fi.")
        return
    try:
        response = urequests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print("Huella guardada en la base de datos.")
        else:
            print("Error al guardar la huella:", response.text)
        response.close()
    except Exception as e:
        print("Error de conexión al servidor:", e)
    
def comparar_y_guardar_huella():
    if not capturar_y_convertir(fingerprint.FINGERPRINT_CHARBUFFER1):
        print("Error en la captura de la huella.")
        return

    try:
       
        # Attempt to download characteristics
        characteristics = sensor.downloadCharacteristics(fingerprint.FINGERPRINT_CHARBUFFER1)
        
        # Check if characteristics data was downloaded successfully
        if characteristics:
            print("Characteristics data length:", len(characteristics))
            print("Characteristics data content:", [hex(byte) for byte in characteristics])
            
            try:
                # Attempt to convert characteristics to Base64 format
                template = ubinascii.b2a_base64(bytes(characteristics)).decode('utf-8')
                print("Template created successfully:", template)
                
                # Send the Base64-encoded template to the server
                enviar_huella_a_servidor(template)
                
            except Exception as conversion_error:
                print("Error during Base64 conversion:", conversion_error)
        else:
            print("No se pudieron descargar las características de la huella.")
    except Exception as e:
        print("Error al descargar las características:", e)
# Ejecutar la función para capturar y enviar la huella
comparar_y_guardar_huella()
