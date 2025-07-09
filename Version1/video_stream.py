from flask import Flask, Response, stream_with_context
from flask_cors import CORS
import cv2
from ultralytics import YOLO
from config import line_x, class_names, waste_categories
from tracker import ObjectTracker
from detection import get_center
from categories import get_item_category, get_category_color
from visualization import draw_category_stats, draw_detection, draw_trajectory

app = Flask(__name__)
CORS(app)  # habilita CORS para todos los orígenes

# Inicializaciones de cámara y modelo
CAMERA_URL = "http://192.168.0.7:8080/video"
# Forzar uso de FFMPEG backend para menor buffering
cap = cv2.VideoCapture(CAMERA_URL, cv2.CAP_FFMPEG)
model = YOLO("../best110.pt")
tracker = ObjectTracker()


@app.route('/')
def index():
    """Página de prueba con stream procesado únicamente."""
    return """
    <html>
      <head><title>Stream Procesado</title></head>
      <body>
        <h3>Salida Procesada (baja latencia)</h3>
        <img src=\"/stream/processed\" />
      </body>
    </html>
    """

@app.route('/stream/processed')
def stream_processed():
    # Usar stream_with_context para no acumular buffer
    return Response(stream_with_context(gen_processed()),
                    mimetype='multipart/x-mixed-replace; boundary=frame',
                    headers={'Cache-Control': 'no-cache', 'Pragma': 'no-cache'})


def gen_processed():
    """Generador para el flujo procesado (YOLO + drawing) con JPEG calidad ajustable."""
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]  # reducir calidad para mayor velocidad
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        # Redimensionar al tamaño del modelo
        frame = cv2.resize(frame, (640, 640))

        # Inferencia (podrías ajustar imgsz menor si aceptas menor resolución)
        results = model(frame, imgsz=640, conf=0.5)
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
                infos.append({'xyxy': xyxy, 'cls_id': cls_id, 'conf': conf,
                              'center': center, 'class_name': class_name,
                              'category': category})

        # Actualizar tracker y contadores
        tracker.update(detections)
        new_crossings = tracker.check_line_crossing(line_x)
        for cat, cnt in new_crossings.items():
            if cat in waste_categories:
                waste_categories[cat]['count'] += cnt

        # Dibujar detecciones y estadísticas
        for info in infos:
            label = f"{info['class_name']} ({info['category']}): {info['conf']:.2f}"
            draw_detection(frame, info['xyxy'], label, get_category_color(info['category']))
        for obj in tracker.objects.values():
            draw_trajectory(frame, obj['positions'], obj['category'])
        draw_category_stats(frame)
        cv2.line(frame, (line_x, 0), (line_x, 640), (0,255,255), 2)

        # Codificar frame con menor latencia
        ret2, jpg = cv2.imencode('.jpg', frame, encode_param)
        if not ret2:
            continue
        frame_bytes = jpg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

if __name__ == '__main__':
    # Desactivar threaded para evitar reordenamiento de frames
    app.run(host='0.0.0.0', port=5000, threaded=False)
