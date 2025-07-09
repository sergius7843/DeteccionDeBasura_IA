
# mqtt_client.py  
# Responsabilidad: Cliente MQTT optimizado para robot móvil

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
        
        # Topics optimizados para robot recolector
        self.topics = {
            'METAL': 'robot/deteccion/metal',
            'PLASTICO': 'robot/deteccion/plastico', 
            'BOLSAS': 'robot/deteccion/bolsas',
            'PAPEL': 'robot/deteccion/papel',
            'OTROS': 'robot/deteccion/otros',
            # Topics de control para el robot
            'STATUS': 'robot/status',
            'LOCATION': 'robot/location',
            'COMMAND': 'robot/command'
        }
        
        self.connect()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"🤖 Robot conectado al broker MQTT {self.broker_host}:{self.broker_port}")
            # Suscribirse a comandos para el robot
            self.client.subscribe(self.topics['COMMAND'])
        else:
            self.connected = False
            print(f"❌ Error conectando al broker MQTT. Código: {rc}")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        print("🔌 Robot desconectado del broker MQTT")

    def on_publish(self, client, userdata, mid):
        print(f"📡 Datos enviados al servidor (ID: {mid})")

    def connect(self):
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"❌ Error conectando al broker: {e}")
            self.connected = False

    def publish_detection(self, category, items):
        """Publica detección con información de ubicación del robot"""
        if not self.connected:
            print("❌ Robot no conectado al broker MQTT")
            return False
            
        if category not in self.topics:
            print(f"❌ Categoría desconocida: {category}")
            return False
            
        topic = self.topics[category]
        
        # Payload optimizado para robot móvil
        payload = {
            "timestamp": datetime.now().isoformat(),
            "robot_id": "COLLECTOR_01",
            "category": category,
            "item_count": len(items),
            "items": [{"id": item["id"], "class": item["class_name"], 
                      "confidence": round(item.get("confidence", 0), 3)} for item in items],
            "priority": self._get_category_priority(category),
            "collection_recommended": self._should_collect(category, items)
        }
        
        try:
            result = self.client.publish(topic, json.dumps(payload), qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "⚪"}.get(
                    self._get_category_priority(category), "⚪")
                print(f"🤖 {priority_emoji} {category}: {len(items)} objeto(s) detectado(s)")
                return True
            else:
                print(f"❌ Error publicando a {topic}")
                return False
        except Exception as e:
            print(f"❌ Error en publish_detection: {e}")
            return False

    def _get_category_priority(self, category):
        """Obtiene prioridad de la categoría"""
        from config import waste_categories
        return waste_categories.get(category, {}).get('priority', 'LOW')

    def _should_collect(self, category, items):
        """Determina si el robot debe recolectar estos objetos"""
        priority = self._get_category_priority(category)
        item_count = len(items)
        
        # Lógica de recolección basada en prioridad y cantidad
        if priority == 'HIGH':
            return item_count >= 1  # Recolectar inmediatamente
        elif priority == 'MEDIUM':
            return item_count >= 2  # Recolectar si hay varios
        else:
            return item_count >= 3  # Recolectar solo si hay muchos

    def publish_robot_status(self, status_data):
        """Publica estado del robot"""
        if self.connected:
            self.client.publish(self.topics['STATUS'], json.dumps(status_data), qos=1)

    def disconnect(self):
        """Desconectar del broker"""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()