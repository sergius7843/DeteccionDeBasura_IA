# Responsabilidad: Sistema principal con streaming integrado

import cv2
import threading
import time
from ultralytics import YOLO
from config import CAM_WIDTH, CAM_HEIGHT, class_names, waste_categories, MQTT_BROKER_HOST, MQTT_BROKER_PORT
from tracker import ObjectTracker
from detection import get_center
from categories import get_item_category, get_category_color
from visualization import (draw_modern_header, draw_status_panel, draw_category_dashboard, 
                          draw_modern_detection, draw_modern_trajectory, draw_footer_info)
from mqtt_client import MQTTPublisher
from stream_server import video_streamer, start_flask_server

class RobotCollectorWithStreaming:
    def __init__(self, flask_host='0.0.0.0', flask_port=5000):
        # Componentes principales
        self.model = YOLO("../best110.pt")  #nombre del modelo de deteccion
        self.tracker = ObjectTracker()
        self.mqtt_client = MQTTPublisher(MQTT_BROKER_HOST, MQTT_BROKER_PORT)  ##CONEXION AL BROKER MQTT MOSQUITTO
        
        # Configuración de streaming
        self.flask_host = flask_host
        self.flask_port = flask_port
        self.running = False
        
        # Métricas de rendimiento
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        
        print("🤖 Inicializando Robot Recolector con Streaming...")
        print(f"📡 Servidor web: http://{flask_host}:{flask_port}")
        
    def start_streaming_server(self):
        """Inicia el servidor Flask en un hilo separado"""
        flask_thread = threading.Thread(
            target=start_flask_server, 
            args=(self.flask_host, self.flask_port, False),
            daemon=True
        )
        flask_thread.start()
        print(f"✅ Servidor de streaming iniciado en http://{self.flask_host}:{self.flask_port}")
        
    def calculate_fps(self):
        """Calcula FPS en tiempo real"""
        self.fps_counter += 1
        if self.fps_counter % 30 == 0:  # Actualizar cada 30 frames
            current_time = time.time()
            self.current_fps = 30 / (current_time - self.fps_start_time)
            self.fps_start_time = current_time
            
    def update_streaming_stats(self):
        """Actualiza estadísticas para el streaming"""
        total_detected = sum(data['count'] for data in waste_categories.values())
        categories_stats = {cat: data['count'] for cat, data in waste_categories.items()}
        
        stats = {
            'fps': round(self.current_fps, 1),
            'total_detections': total_detected,
            'categories': categories_stats,
            'robot_status': 'ACTIVE' if self.running else 'INACTIVE',
            'mqtt_connected': self.mqtt_client.connected,
            'tracking_stats': self.tracker.get_detection_stats()
        }
        
        video_streamer.update_stats(stats)
        
    def process_frame(self, frame):
        """Procesa un frame completo con detección y visualización"""
        # Inferencia
        results = self.model(frame, imgsz=640, conf=0.4)
        
        # Extracción de detecciones
        detections = []
        infos = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                if cls_id >= len(class_names):
                    continue
                    
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy()
                center = get_center(xyxy)
                class_name = class_names[cls_id]
                category = get_item_category(class_name)
                
                detections.append({
                    'center': center, 
                    'class_name': class_name, 
                    'confidence': conf
                })
                infos.append({
                    'xyxy': xyxy, 'cls_id': cls_id, 'conf': conf, 
                    'center': center, 'class_name': class_name, 'category': category
                })
        
        # Actualizar tracker
        self.tracker.update(detections)
        
        # Procesar objetos confirmados
        confirmed_objects = self.tracker.get_confirmed_objects_for_report()
        for category, items in confirmed_objects.items():
            if category in waste_categories:
                waste_categories[category]['count'] += len(items)
            
            self.mqtt_client.publish_detection(category, items)
            print(f"🤖 Stream: {len(items)} objeto(s) de {category} detectado(s)")
        
        # Crear visualización
        self.draw_interface(frame, infos)
        
        return frame
        
    def draw_interface(self, frame, infos):
        """Dibuja la interfaz completa en el frame"""
        # Interfaz moderna
        draw_modern_header(frame)
        draw_status_panel(frame, self.mqtt_client.connected, self.tracker.get_detection_stats())
        draw_category_dashboard(frame)
        draw_footer_info(frame)
        
        # Dibujar detecciones
        for info in infos:
            draw_modern_detection(frame, info['xyxy'], info['class_name'], 
                                info['category'], info['conf'])
        
        # Dibujar trayectorias
        for obj_id, obj in self.tracker.objects.items():
            draw_modern_trajectory(frame, obj['positions'], obj['category'], obj['confirmed'])
        
        # Información de streaming
        cv2.putText(frame, f"STREAMING: {self.current_fps:.1f} FPS", 
                   (CAM_WIDTH - 200, CAM_HEIGHT - 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(frame, f"Puerto: {self.flask_port}", 
                   (CAM_WIDTH - 200, CAM_HEIGHT - 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
    
    def run(self, camera_source=0):
        """Ejecuta el sistema completo con streaming"""
        # Inicializar cámara
        cap = cv2.VideoCapture(camera_source)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
        
        if not cap.isOpened():
            print("❌ Error: No se pudo abrir la cámara")
            return
        
        # Iniciar servidor de streaming
        self.start_streaming_server()
        
        self.running = True
        self.fps_start_time = time.time()
        
        print("=== ROBOT RECOLECTOR CON STREAMING ===")
        print(f"📹 Stream disponible en: http://{self.flask_host}:{self.flask_port}")
        print("🔍 Detectando: METAL, PLÁSTICO, BOLSAS, PAPEL, OTROS")
        print("Presiona 'q' para salir")
        print("=====================================")
        
        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Error leyendo frame de la cámara")
                    break
                
                frame = cv2.resize(frame, (CAM_WIDTH, CAM_HEIGHT))
                
                # Procesar frame
                processed_frame = self.process_frame(frame)
                
                # Actualizar streaming
                video_streamer.update_frame(processed_frame)
                
                # Calcular FPS y estadísticas
                self.calculate_fps()
                self.update_streaming_stats()
                
                # Mostrar localmente (opcional)
                cv2.imshow("Robot Recolector - Vista Local", processed_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo sistema...")
        finally:
            self.cleanup(cap)
    
    def cleanup(self, cap):
        """Limpieza de recursos"""
        self.running = False
        cap.release()
        cv2.destroyAllWindows()
        self.mqtt_client.disconnect()
        
        # Resumen final
        print("\n=== RESUMEN DE RECOLECCIÓN ===")
        total_detected = sum(data['count'] for data in waste_categories.values())
        print(f"Total de objetos detectados: {total_detected}")
        for cat, data in waste_categories.items():
            print(f"{cat} [{data['priority']}]: {data['count']} objetos")
        print("==============================\n")

def main():
    # Configuración
    CAMERA_SOURCE = "http://192.168.31.51:8080/video"  # 0 para cámara local, URL para cámara IP
    FLASK_HOST = '0.0.0.0'  # 0.0.0.0 para acceso remoto, localhost solo local
    FLASK_PORT = 5000
    
    # Crear y ejecutar sistema
    robot_system = RobotCollectorWithStreaming(FLASK_HOST, FLASK_PORT)
    robot_system.run(CAMERA_SOURCE)

if __name__ == "__main__":
    main()