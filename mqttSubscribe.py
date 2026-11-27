import matplotlib
matplotlib.use('TkAgg')  # Fuerza ventana externa en VS Code
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
import numpy as np
import json

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USER = "user"
MQTT_PASSWORD = "password"
MQTT_TOPIC = "Lidar/Distance"

# Matriz [theta][phi] para ángulos de 0° a 180° (181 valores)
matriz_distancias = np.zeros((181, 181))
barrido_listo = False

# Función que se ejecuta cuando nos conectamos al broker
def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"Conectado al broker con código: {reason_code}")
    client.subscribe(MQTT_TOPIC)
    print(f"Suscrito a: {MQTT_TOPIC} ... Esperando datos...\n")

# Función que se ejecuta cada vez que llega un mensaje
def on_message(client, userdata, msg):
    global matriz_distancias, barrido_listo
    try:
        # 1. Decodificar el mensaje de bytes a texto (String)
        payload_texto = msg.payload.decode('utf-8')
        
        # 2. Convertir el texto JSON a un diccionario de Python
        datos = json.loads(payload_texto)
        
        # 3. Extraer las variables
        theta = datos.get("theta")
        distances = datos.get("distances", [])
        
        # Validar que theta esté en rango y que lleguen 181 distancias (phi de 0 a 180)
        if theta is not None and 0 <= int(theta) <= 180 and len(distances) == 181:
            theta = int(theta)
            # Guardar en matriz[theta][phi] (convertido a metros dividiendo entre 100; quita '/ 100.0' si lo quieres en cm)
            matriz_distancias[theta] = np.array(distances, dtype=float) / 100.0
            
            print(f"Guardado theta={theta}° | Primeras 5 distancias (m): {np.round(matriz_distancias[theta][:5], 2)}")
            
            # Cuando llega el ángulo final (180), pausamos loop_forever() para poder dibujar
            if theta == 180:
                barrido_listo = True
                client.disconnect()
        else:
            print(f"⚠️ Mensaje ignorado: theta={theta}, cantidad de distancias={len(distances)}")
        
    except json.JSONDecodeError:
        print("Error: El mensaje recibido no es un JSON válido.")
        print("Mensaje bruto:", msg.payload)

def dibujar_plot_3d(matriz):
    # Crear rejilla de ángulos theta y phi (0° a 180°) en radianes
    angulos_rad = np.deg2rad(np.arange(181))
    THETA, PHI = np.meshgrid(angulos_rad, angulos_rad, indexing='ij')

    # Convertir coordenadas esféricas (r, theta, phi) a cartesianas (X, Y, Z)
    X = matriz * np.cos(THETA) * np.cos(PHI)
    Y = matriz * np.cos(THETA) * np.sin(PHI)
    Z = matriz * np.sin(THETA)

    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection='3d')

    sc = ax.scatter(X, Y, Z, c=matriz, cmap='plasma', s=2)
    fig.colorbar(sc, label='Distancia (m)')
    ax.scatter([0], [0], [0], color='red', s=80, label='Sensor Lidar (0,0,0)')

    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.set_title('Nube de Puntos 3D - Lidar')
    ax.legend()
    ax.set_box_aspect([1, 1, 1])

    plt.show()

# --- Configuración del Cliente MQTT ---
cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
cliente.on_connect = on_connect
cliente.on_message = on_message

# Mantener el script corriendo y escuchando indefinidamente
while True:
    try:
        barrido_listo = False
        print(f"Intentando conectar a {MQTT_BROKER}:{MQTT_PORT}...")
        cliente.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Escucha hasta que llega theta == 180 y se llama a client.disconnect()
        cliente.loop_forever()
        
        if barrido_listo:
            print("\nBarrido completo (0° a 180°). Abriendo gráfico 3D...")
            dibujar_plot_3d(matriz_distancias)
            
    except KeyboardInterrupt:
        print("\nDesconectando...")
        cliente.disconnect()
        break