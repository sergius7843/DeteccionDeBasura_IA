# main.py
# Responsabilidad: Punto de entrada con sistema robusto anti-falsos positivos

import cv2
from ultralytics import YOLO
from config import CAM_WIDTH, CAM_HEIGHT, class_names, waste_categories, MQTT_BROKER_HOST, MQTT_BROKER_PORT
from tracker import ObjectTracker
from detection import get_center
from categories import get_item_category, get_category_color
from visualization import draw_category_stats, draw_detection, draw_trajectory, draw_mqtt_status, draw_detection_stats
from mqtt_client import MQTTPublisher

def main():
    # Cargar modelo
    model = YOLO("../best110.pt")

    # Inicializar cámara
    
    cap = cv2.VideoCapture(0)  # Cámara local
    
    #cap = cv2.VideoCapture("http://10.42.0.104:8080/video")  # Cámara IP
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

    # Inicializar tracker y cliente MQTT
    tracker = ObjectTracker()
    mqtt_client = MQTTPublisher(MQTT_BROKER_HOST, MQTT_BROKER_PORT)

    print("=== SISTEMA DE DETECCIÓN ROBUSTO CON MQTT ===")
    print("Filtros anti-falsos positivos activados")
    print("Presiona 'q' para salir")
    print("=============================================")

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error leyendo frame de la cámara")
            break
        
        frame = cv2.resize(frame, (CAM_WIDTH, CAM_HEIGHT))
        frame_count += 1

        # Inferencia
        results = model(frame, imgsz=640, conf=0.4)  # Confianza más baja para capturar más detecciones

        # Extracción de detecciones con información de confianza
        detections = []
        infos = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
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

        # Actualizar tracker con filtros robustos
        tracker.update(detections)
        
        # Obtener objetos confirmados para reportar por MQTT
        confirmed_objects = tracker.get_confirmed_objects_for_report()
        for category, items in confirmed_objects.items():
            # Actualizar contador local
            if category in waste_categories:
                waste_categories[category]['count'] += len(items)
            
            # Publicar por MQTT
            mqtt_client.publish_detection(category, items)
            print(f"📤 Reportado: {len(items)} objeto(s) de categoría {category}")

        # Dibujar detecciones con indicadores de estado
        for info in infos:
            confidence_indicator = "✓" if info['conf'] >= 0.7 else "?"
            label = f"{info['class_name']} {confidence_indicator}: {info['conf']:.2f}"
            draw_detection(frame, info['xyxy'], label, get_category_color(info['category']))
        
        # Dibujar trayectorias solo para objetos confirmados
        for obj_id, obj in tracker.objects.items():
            if obj['confirmed']:
                draw_trajectory(frame, obj['positions'], obj['category'], confirmed=True)
            else:
                draw_trajectory(frame, obj['positions'], obj['category'], confirmed=False)

        # Estadísticas y estado
        draw_category_stats(frame)
        draw_mqtt_status(frame, mqtt_client.connected)
        draw_detection_stats(frame, tracker.get_detection_stats())
        
        total_detected = sum(data['count'] for data in waste_categories.values())
        cv2.putText(frame, f"Confirmados: {total_detected}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Leyenda
        legend_y = CAM_HEIGHT - 120
        cv2.putText(frame, "LEYENDA:", (CAM_WIDTH - 250, legend_y - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, "✓ = Alta confianza", (CAM_WIDTH - 250, legend_y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(frame, "? = Baja confianza", (CAM_WIDTH - 250, legend_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        for i, (cat, data) in enumerate(waste_categories.items()):
            y = legend_y + 20 + i * 25
            cv2.rectangle(frame, (CAM_WIDTH - 250, y - 10), (CAM_WIDTH - 230, y + 5), data['color'], -1)
            cv2.putText(frame, cat, (CAM_WIDTH - 225, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Mostrar frame
        cv2.imshow("Detector Robusto de Residuos", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Limpiar recursos
    cap.release()
    cv2.destroyAllWindows()
    mqtt_client.disconnect()

    # Mostrar resumen final
    print("\n=== RESUMEN FINAL ===")
    total_detected = sum(data['count'] for data in waste_categories.values())
    print(f"Total de objetos confirmados: {total_detected}")
    for cat, data in waste_categories.items():
        print(f"{cat}: {data['count']} objetos")
    
    stats = tracker.get_detection_stats()
    print(f"\nEstadísticas de tracking:")
    print(f"- Objetos confirmados: {stats['confirmed']}")
    print(f"- Pendientes de confirmación: {stats['pending_confirmation']}")
    print("====================\n")

if __name__ == "__main__":
    main()