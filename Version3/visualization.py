# visualization.py
# Responsabilidad: UI profesional y minimalista

import cv2
import numpy as np
from config import CAM_WIDTH, CAM_HEIGHT, UI_CONFIG, waste_categories
from categories import get_category_color, get_priority_order

def create_overlay(frame, alpha=0.8):
    """Crea overlay semi-transparente para UI moderna"""
    overlay = frame.copy()
    return overlay, alpha

def draw_rounded_rectangle(img, pt1, pt2, color, thickness=1, radius=10):
    """Dibuja rectángulo con esquinas redondeadas"""
    x1, y1 = pt1
    x2, y2 = pt2
    
    # Rectángulo principal
    cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
    cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, thickness)
    
    # Esquinas redondeadas
    cv2.circle(img, (x1 + radius, y1 + radius), radius, color, thickness)
    cv2.circle(img, (x2 - radius, y1 + radius), radius, color, thickness)
    cv2.circle(img, (x1 + radius, y2 - radius), radius, color, thickness)
    cv2.circle(img, (x2 - radius, y2 - radius), radius, color, thickness)

def draw_modern_header(frame):
    """Dibuja header profesional"""
    # Fondo del header
    cv2.rectangle(frame, (0, 0), (CAM_WIDTH, 60), UI_CONFIG['card_background'], -1)
    cv2.line(frame, (0, 60), (CAM_WIDTH, 60), UI_CONFIG['border_color'], 1)
    
    # Título principal
    cv2.putText(frame, "ROBOT RECOLECTOR", (20, 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, UI_CONFIG['accent_color'], 2)
    cv2.putText(frame, "Sistema de Deteccion Autonoma", (20, 45), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, UI_CONFIG['text_secondary'], 1)

def draw_status_panel(frame, mqtt_connected, stats):
    """Panel de estado superior derecho"""
    panel_width = 200
    panel_height = 100
    x_start = CAM_WIDTH - panel_width - 10
    y_start = 10
    
    # Fondo del panel
    overlay = frame.copy()
    cv2.rectangle(overlay, (x_start, y_start), 
                 (x_start + panel_width, y_start + panel_height), 
                 UI_CONFIG['card_background'], -1)
    cv2.addWeighted(overlay, 0.9, frame, 0.1, 0, frame)
    
    # Borde
    cv2.rectangle(frame, (x_start, y_start), 
                 (x_start + panel_width, y_start + panel_height), 
                 UI_CONFIG['border_color'], 1)
    
    # Status MQTT
    mqtt_color = UI_CONFIG['success_color'] if mqtt_connected else UI_CONFIG['error_color']
    mqtt_status = "CONECTADO" if mqtt_connected else "DESCONECTADO"
    cv2.putText(frame, "MQTT:", (x_start + 10, y_start + 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, UI_CONFIG['text_primary'], 1)
    cv2.putText(frame, mqtt_status, (x_start + 60, y_start + 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, mqtt_color, 1)
    
    # Estadísticas
    cv2.putText(frame, f"Rastreando: {stats['total_tracked']}", 
                (x_start + 10, y_start + 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, UI_CONFIG['text_secondary'], 1)
    cv2.putText(frame, f"Confirmados: {stats['confirmed']}", 
                (x_start + 10, y_start + 70), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, UI_CONFIG['text_secondary'], 1)
    cv2.putText(frame, f"Pendientes: {stats['pending_confirmation']}", 
                (x_start + 10, y_start + 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, UI_CONFIG['text_secondary'], 1)

def draw_category_dashboard(frame):
    """Dashboard principal de categorías con diseño moderno"""
    panel_width = 280
    panel_height = 300
    x_start = 10
    y_start = 70
    
    # Fondo principal
    overlay = frame.copy()
    cv2.rectangle(overlay, (x_start, y_start), 
                 (x_start + panel_width, y_start + panel_height), 
                 UI_CONFIG['card_background'], -1)
    cv2.addWeighted(overlay, 0.9, frame, 0.1, 0, frame)
    
    # Borde del panel
    cv2.rectangle(frame, (x_start, y_start), 
                 (x_start + panel_width, y_start + panel_height), 
                 UI_CONFIG['border_color'], 2)
    
    # Título del dashboard
    cv2.putText(frame, "DETECCIONES POR CATEGORIA", 
                (x_start + 10, y_start + 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, UI_CONFIG['text_primary'], 2)
    
    # Línea separadora
    cv2.line(frame, (x_start + 10, y_start + 35), 
             (x_start + panel_width - 10, y_start + 35), 
             UI_CONFIG['border_color'], 1)
    
    # Categorías ordenadas por prioridad
    y_offset = y_start + 55
    ordered_categories = get_priority_order()
    
    for i, category in enumerate(ordered_categories):
        if category not in waste_categories:
            continue
            
        data = waste_categories[category]
        color = data['color']
        count = data['count']
        priority = data['priority']
        
        # Fondo de cada categoría
        category_bg = (60, 60, 60) if i % 2 == 0 else (50, 50, 50)
        cv2.rectangle(frame, (x_start + 15, y_offset - 15), 
                     (x_start + panel_width - 15, y_offset + 25), 
                     category_bg, -1)
        
        # Indicador de color de categoría
        cv2.circle(frame, (x_start + 30, y_offset + 5), 8, color, -1)
        cv2.circle(frame, (x_start + 30, y_offset + 5), 8, UI_CONFIG['text_primary'], 1)
        
        # Nombre de categoría
        cv2.putText(frame, category, (x_start + 50, y_offset + 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, UI_CONFIG['text_primary'], 2)
        
        # Contador
        cv2.putText(frame, str(count), (x_start + panel_width - 50, y_offset + 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        # Indicador de prioridad
        priority_color = {
            'HIGH': UI_CONFIG['error_color'],
            'MEDIUM': UI_CONFIG['warning_color'], 
            'LOW': UI_CONFIG['text_secondary']
        }.get(priority, UI_CONFIG['text_secondary'])
        
        cv2.putText(frame, f"[{priority}]", (x_start + 150, y_offset + 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, priority_color, 1)
        
        y_offset += 45

def draw_modern_detection(frame, xyxy, label, category, confidence):
    """Dibuja detección con estilo moderno"""
    x1, y1, x2, y2 = map(int, xyxy)
    color = get_category_color(category)
    
    # Caja principal con esquinas redondeadas simuladas
    thickness = 3 if confidence >= 0.8 else 2
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    
    # Esquinas decorativas
    corner_size = 15
    cv2.line(frame, (x1, y1), (x1 + corner_size, y1), color, thickness + 1)
    cv2.line(frame, (x1, y1), (x1, y1 + corner_size), color, thickness + 1)
    cv2.line(frame, (x2, y1), (x2 - corner_size, y1), color, thickness + 1)
    cv2.line(frame, (x2, y1), (x2, y1 + corner_size), color, thickness + 1)
    cv2.line(frame, (x1, y2), (x1 + corner_size, y2), color, thickness + 1)
    cv2.line(frame, (x1, y2), (x1, y2 - corner_size), color, thickness + 1)
    cv2.line(frame, (x2, y2), (x2 - corner_size, y2), color, thickness + 1)
    cv2.line(frame, (x2, y2), (x2, y2 - corner_size), color, thickness + 1)
    
    # Centro con indicador de confianza
    center = ((x1 + x2) // 2, (y1 + y2) // 2)
    confidence_radius = int(8 * confidence)
    cv2.circle(frame, center, confidence_radius, color, -1)
    cv2.circle(frame, center, confidence_radius + 2, UI_CONFIG['text_primary'], 1)
    
    # Etiqueta moderna
    label_text = f"{label}"
    (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    
    # Fondo de etiqueta con transparencia
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1 - th - 15), (x1 + tw + 20, y1), color, -1)
    cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
    
    cv2.putText(frame, label_text, (x1 + 10, y1 - 8), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Barra de confianza
    conf_bar_width = int(80 * confidence)
    cv2.rectangle(frame, (x1, y1 - 5), (x1 + conf_bar_width, y1 - 2), color, -1)
    
    return center

def draw_modern_trajectory(frame, positions, category, confirmed=False):
    """Dibuja trayectoria con estilo moderno"""
    if len(positions) < 2:
        return
        
    color = get_category_color(category)
    
    if confirmed:
        # Línea sólida con gradiente simulado
        for i in range(1, len(positions)):
            alpha = i / len(positions)
            line_color = tuple(int(c * alpha) for c in color)
            cv2.line(frame, positions[i-1], positions[i], line_color, 3)
        
        # Punto final destacado
        if positions:
            last = positions[-1]
            cv2.circle(frame, last, 6, color, -1)
            cv2.circle(frame, last, 8, UI_CONFIG['text_primary'], 1)
            cv2.putText(frame, "✓", (last[0] + 10, last[1] - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, UI_CONFIG['success_color'], 2)
    else:
        # Línea punteada para no confirmados
        for i in range(1, len(positions)):
            if i % 3 == 0:
                cv2.line(frame, positions[i-1], positions[i], UI_CONFIG['text_secondary'], 1)
        
        if positions:
            last = positions[-1]
            cv2.circle(frame, last, 4, UI_CONFIG['text_secondary'], 1)
            cv2.putText(frame, "?", (last[0] + 8, last[1] - 3), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, UI_CONFIG['warning_color'], 1)

def draw_footer_info(frame):
    """Información del pie de página"""
    footer_height = 40
    y_start = CAM_HEIGHT - footer_height
    
    # Fondo del footer
    cv2.rectangle(frame, (0, y_start), (CAM_WIDTH, CAM_HEIGHT), 
                 UI_CONFIG['card_background'], -1)
    cv2.line(frame, (0, y_start), (CAM_WIDTH, y_start), UI_CONFIG['border_color'], 1)
    
    # Información
    cv2.putText(frame, "Presiona 'Q' para salir", (20, y_start + 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, UI_CONFIG['text_secondary'], 1)
    
    # Total recolectado
    total = sum(data['count'] for data in waste_categories.values())
    cv2.putText(frame, f"Total Recolectado: {total}", (CAM_WIDTH - 200, y_start + 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, UI_CONFIG['accent_color'], 2)
