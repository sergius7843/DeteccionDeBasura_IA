# visualization.py
# Responsabilidad: Dibujado mejorado con indicadores de calidad

import cv2
from config import CAM_WIDTH, CAM_HEIGHT
from categories import get_category_color, waste_categories

def draw_category_stats(frame, y_start=100):
    """Dibuja las estadísticas por categoría en el frame"""
    y_offset = y_start
    for category, data in waste_categories.items():
        color = data['color']
        count = data['count']
        # Fondo semi-transparente
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, y_offset - 25), (300, y_offset + 10), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        # Texto de la categoría
        text = f"{category}: {count}"
        cv2.putText(frame, text, (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        y_offset += 40

def draw_detection(frame, xyxy, label, color):
    """Dibuja caja, centro y etiqueta para una detección"""
    x1, y1, x2, y2 = map(int, xyxy)
    # Caja
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    # Centro
    center = ((x1 + x2) // 2, (y1 + y2) // 2)
    cv2.circle(frame, center, 4, color, -1)
    # Fondo de texto
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw, y1), color, -1)
    cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    return center

def draw_trajectory(frame, positions, category, confirmed=False):
    """Dibuja la trayectoria con indicadores de confirmación"""
    color = get_category_color(category)
    
    # Línea sólida para confirmados, punteada para no confirmados
    if confirmed:
        for i in range(1, len(positions)):
            cv2.line(frame, positions[i-1], positions[i], color, 2)
    else:
        # Línea punteada para objetos no confirmados
        for i in range(1, len(positions)):
            if i % 2 == 0:  # Línea punteada simple
                cv2.line(frame, positions[i-1], positions[i], (128, 128, 128), 1)
    
    # Indicador de estado
    if positions:
        last = positions[-1]
        status = "✓" if confirmed else "?"
        status_color = color if confirmed else (128, 128, 128)
        cv2.putText(frame, status, (last[0] + 5, last[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)

def draw_mqtt_status(frame, mqtt_connected):
    """Dibuja el estado de conexión MQTT"""
    status_text = "MQTT: ✓" if mqtt_connected else "MQTT: ✗"
    color = (0, 255, 0) if mqtt_connected else (0, 0, 255)
    cv2.putText(frame, status_text, (CAM_WIDTH - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def draw_detection_stats(frame, stats):
    """Dibuja estadísticas de detección en tiempo real"""
    y_start = 60
    cv2.putText(frame, f"Tracking: {stats['total_tracked']}", (10, y_start), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"Pendientes: {stats['pending_confirmation']}", (10, y_start + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)