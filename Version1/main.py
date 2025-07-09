# main.py
# Responsabilidad: Punto de entrada y bucle principal

import cv2
from ultralytics import YOLO
from config import CAM_WIDTH, CAM_HEIGHT, line_x, class_names, total_counter, waste_categories
from tracker import ObjectTracker
from detection import get_center
from categories import get_item_category, get_category_color
from visualization import draw_category_stats, draw_detection, draw_trajectory


def main():
    # Cargar modelo
    model = YOLO("../best.pt")

    # Inicializar cámara
    cap = cv2.VideoCapture(0)       #CAMBIAMOS ESTO POR:  cap = cv2.VideoCapture("http://192.168.0.4:8080/video")

    #cap = cv2.VideoCapture("http://10.42.0.104:8080/video")
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

    # Inicializar tracker y contadores
    tracker = ObjectTracker()
    total = total_counter

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (CAM_WIDTH, CAM_HEIGHT))

        # Inferencia
        results = model(frame, imgsz=640, conf=0.5)

        # Línea de conteo
        cv2.line(frame, (line_x, 0), (line_x, CAM_HEIGHT), (0, 255, 255), 3)
        cv2.putText(frame, "Linea de conteo", (line_x + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Extracción de detecciones
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
                detections.append({'center': center, 'class_name': class_name})
                infos.append({'xyxy': xyxy, 'cls_id': cls_id, 'conf': conf, 'center': center, 'class_name': class_name, 'category': category})

        # Actualizar tracker y contadores por cruce de línea
        tracker.update(detections)
        new_crossings = tracker.check_line_crossing(line_x)
        for cat, cnt in new_crossings.items():
            if cat in waste_categories:
                waste_categories[cat]['count'] += cnt
            total += cnt

        # Dibujar detecciones y trayectorias
        for info in infos:
            label = f"{info['class_name']} ({info['category']}): {info['conf']:.2f}"
            draw_detection(frame, info['xyxy'], label, get_category_color(info['category']))
        for obj in tracker.objects.values():
            draw_trajectory(frame, obj['positions'], obj['category'])

        # Estadísticas y leyendas
        draw_category_stats(frame)
        cv2.putText(frame, f"Total: {total}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Tracking: {len(tracker.objects)}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        legend_y = CAM_HEIGHT - 100
        cv2.putText(frame, "LEYENDA:", (CAM_WIDTH - 200, legend_y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        for i, (cat, data) in enumerate(waste_categories.items()):
            y = legend_y + i * 25
            cv2.rectangle(frame, (CAM_WIDTH - 200, y - 10), (CAM_WIDTH - 180, y + 5), data['color'], -1)
            cv2.putText(frame, cat, (CAM_WIDTH - 175, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Mostrar frame
        cv2.imshow("Contador de basura por categorias", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Limpiar y mostrar resumen
    cap.release()
    cv2.destroyAllWindows()

    print("\n=== RESUMEN FINAL ===")
    print(f"Total de objetos contados: {total}")
    for cat, data in waste_categories.items():
        print(f"{cat}: {data['count']} objetos")
    print("====================\n")


if __name__ == "__main__":
    main()
