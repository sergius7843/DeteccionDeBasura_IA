# mqtt_client.py
# Responsabilidad: Cliente MQTT para comunicación con ESP32

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

class MQTTPublisher:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client()
        self.connected = False
        
        # Configurar callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        
        # Topics para cada categoría
        self.topics = {
            'RECICLABLE': 'esp32/deteccion/reciclable',
            'NO_RECICLABLE': 'esp32/deteccion/noReciclable',
            'PELIGROSO': 'esp32/deteccion/peligroso'
        }
        
        self.connect()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"✓ Conectado al broker MQTT {self.broker_host}:{self.broker_port}")
        else:
            self.connected = False
            print(f"✗ Error conectando al broker MQTT. Código: {rc}")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        print("✗ Desconectado del broker MQTT")

    def on_publish(self, client, userdata, mid):
        print(f"📤 Mensaje publicado (ID: {mid})")

    def connect(self):
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"✗ Error conectando al broker: {e}")
            self.connected = False

    def publish_detection(self, category, items):
        """Publica detección de una categoría específica"""
        if not self.connected:
            print("✗ No conectado al broker MQTT")
            return False
            
        if category not in self.topics:
            print(f"✗ Categoría desconocida: {category}")
            return False
            
        topic = self.topics[category]
        
        # Crear payload con información de la detección
        payload = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "count": len(items),
            "items": [{"id": item["id"], "class": item["class_name"]} for item in items]
        }
        
        try:
            # Publicar mensaje
            result = self.client.publish(topic, json.dumps(payload), qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 {category}: {len(items)} objeto(s) -> {topic}")
                return True
            else:
                print(f"✗ Error publicando a {topic}")
                return False
        except Exception as e:
            print(f"✗ Error en publish_detection: {e}")
            return False

    def disconnect(self):
        """Desconectar del broker"""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()