# main.py
# Responsabilidad: Sistema principal para robot recolector

import cv2
from ultralytics import YOLO
from config import CAM_WIDTH, CAM_HEIGHT, class_names, waste_categories, MQTT_BROKER_HOST, MQTT_BROKER_PORT
from tracker import ObjectTracker
from detection import get_center
from categories import get_item_category, get_category_color
from visualization import (draw_modern_header, draw_status_panel, draw_category_dashboard, 
                          draw_modern_detection, draw_modern_trajectory, draw_footer_info)
from mqtt_client import MQTTPublisher

def main():
    # Cargar modelo
    model = YOLO("../best110.pt")

    # Inicializar cámara
    
    
    cap = cv2.VideoCapture(0)  # Camara de laptop para pruebas
    
    #cap = cv2.VideoCapture("http://192.168.31.51:8080/video")  # Cámara IP para el celular
    
    #cap = cv2.VideoCapture("http://192.168.31.61/640x480.mjpeg") # Camara IP del ESP32 

    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

    # Inicializar tracker y cliente MQTT
    tracker = ObjectTracker()
    mqtt_client = MQTTPublisher(MQTT_BROKER_HOST, MQTT_BROKER_PORT)

    print("=== ROBOT RECOLECTOR AUTONOMO ===")
    print("Sistema de detección optimizado para recolección móvil")
    print("Categorías: METAL, PLÁSTICO, BOLSAS, PAPEL, OTROS")
    print("Presiona 'q' para salir")
    print("=================================")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error leyendo frame de la cámara")
            break
        
        frame = cv2.resize(frame, (CAM_WIDTH, CAM_HEIGHT))

        # Inferencia con las clases específicas
        results = model(frame, imgsz=640, conf=0.4)

        # Extracción de detecciones
        detections = []
        infos = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                if cls_id >= len(class_names):  # Filtrar clases no deseadas
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
        tracker.update(detections)
        
        # Obtener objetos confirmados para reportar
        confirmed_objects = tracker.get_confirmed_objects_for_report()
        for category, items in confirmed_objects.items():
            if category in waste_categories:
                waste_categories[category]['count'] += len(items)
            
            # Publicar por MQTT con nuevo sistema de topics
            mqtt_client.publish_detection(category, items)
            print(f"🤖 Robot detectó: {len(items)} objeto(s) de {category}")

        # Crear interfaz moderna
        draw_modern_header(frame)
        draw_status_panel(frame, mqtt_client.connected, tracker.get_detection_stats())
        draw_category_dashboard(frame)
        draw_footer_info(frame)

        # Dibujar detecciones con estilo moderno
        for info in infos:
            draw_modern_detection(frame, info['xyxy'], info['class_name'], 
                                info['category'], info['conf'])
        
        # Dibujar trayectorias modernas
        for obj_id, obj in tracker.objects.items():
            draw_modern_trajectory(frame, obj['positions'], obj['category'], obj['confirmed'])

        # Mostrar frame
        cv2.imshow("Robot Recolector - Sistema de Deteccion", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Limpiar recursos
    cap.release()
    cv2.destroyAllWindows()
    mqtt_client.disconnect()

    # Resumen final
    print("\n=== RESUMEN DE RECOLECCION ===")
    total_detected = sum(data['count'] for data in waste_categories.values())
    print(f"Total de objetos detectados: {total_detected}")
    for cat, data in waste_categories.items():
        print(f"{cat} [{data['priority']}]: {data['count']} objetos")
    print("==============================\n")

if __name__ == "__main__":
    main()