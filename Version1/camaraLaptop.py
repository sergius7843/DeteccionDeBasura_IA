from ultralytics import YOLO
import cv2
import numpy as np

# Cargar modelo
model = YOLO("best.pt")

# Configuración
CAM_WIDTH, CAM_HEIGHT = 640, 480
LINE_POSITION_PERCENT = 0.65  # 65%
line_x = int(CAM_WIDTH * LINE_POSITION_PERCENT)

# Inicializar video
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

# Nombres de las clases
class_names = ['battery', 'can', 'cardboard_bowl', 'cardboard_box', 'chemical_plastic_bottle', 
               'chemical_plastic_gallon', 'chemical_spray_can', 'light_bulb', 'paint_bucket', 
               'plastic_bag', 'plastic_bottle', 'plastic_bottle_cap', 'plastic_box', 
               'plastic_cultery', 'plastic_cup', 'plastic_cup_lid', 'reuseable_paper', 
               'scrap_paper', 'scrap_plastic', 'snack_bag', 'stick', 'straw']

# Clasificación por categorías
waste_categories = {
    'RECICLABLE': {
        'items': ['can', 'cardboard_bowl', 'cardboard_box', 'plastic_bottle', 'plastic_bottle_cap', 
                 'plastic_box', 'plastic_cup', 'plastic_cup_lid', 'reuseable_paper', 'scrap_paper'],
        'color': (0, 255, 0),  # Verde
        'count': 0
    },
    'NO_RECICLABLE': {
        'items': ['plastic_bag', 'plastic_cultery', 'scrap_plastic', 'snack_bag', 'stick', 'straw'],
        'color': (0, 0, 255),  # Rojo
        'count': 0
    },
    'PELIGROSO': {
        'items': ['battery', 'chemical_plastic_bottle', 'chemical_plastic_gallon', 
                 'chemical_spray_can', 'light_bulb', 'paint_bucket'],
        'color': (0, 165, 255),  # Naranja
        'count': 0
    }
}

def get_item_category(class_name):
    """Determina la categoría de un objeto basado en su clase"""
    for category, data in waste_categories.items():
        if class_name in data['items']:
            return category
    return 'DESCONOCIDO'

def get_category_color(category):
    """Obtiene el color asociado a una categoría"""
    if category in waste_categories:
        return waste_categories[category]['color']
    return (128, 128, 128)  # Gris para desconocido

# Contadores totales
total_counter = 0

# Clase para tracking manual de objetos
class ObjectTracker:
    def __init__(self, max_distance=80, max_disappeared=10):
        self.next_id = 0
        self.objects = {}  # {id: {'center': (x,y), 'disappeared': int, 'positions': [(x,y), ...], 'counted': bool, 'class_name': str, 'category': str}}
        self.max_distance = max_distance
        self.max_disappeared = max_disappeared
    
    def register(self, center, class_name='unknown'):
        """Registra un nuevo objeto"""
        category = get_item_category(class_name)
        self.objects[self.next_id] = {
            'center': center,
            'disappeared': 0,
            'positions': [center],
            'counted': False,
            'class_name': class_name,
            'category': category
        }
        self.next_id += 1
    
    def deregister(self, object_id):
        """Elimina un objeto del tracking"""
        del self.objects[object_id]
    
    def update(self, detections):
        """Actualiza el tracking con nuevas detecciones"""
        if len(detections) == 0:
            # Incrementar contador de desaparición para todos los objetos
            for object_id in list(self.objects.keys()):
                self.objects[object_id]['disappeared'] += 1
                if self.objects[object_id]['disappeared'] > self.max_disappeared:
                    self.deregister(object_id)
            return
        
        # Si no tenemos objetos trackeados, registrar todos
        if len(self.objects) == 0:
            for detection in detections:
                self.register(detection['center'], detection['class_name'])
        else:
            # Calcular distancias entre objetos existentes y nuevas detecciones
            object_centers = np.array([obj['center'] for obj in self.objects.values()])
            detection_centers = np.array([det['center'] for det in detections])
            
            # Calcular matriz de distancias
            distances = np.linalg.norm(object_centers[:, np.newaxis] - detection_centers, axis=2)
            
            # Encontrar la asignación óptima
            used_detection_indices = set()
            used_object_ids = set()
            
            object_ids = list(self.objects.keys())
            
            # Asignar detecciones a objetos existentes
            for _ in range(min(len(object_ids), len(detections))):
                min_dist = np.inf
                min_obj_idx = -1
                min_det_idx = -1
                
                for obj_idx, obj_id in enumerate(object_ids):
                    if obj_idx in used_object_ids:
                        continue
                    for det_idx in range(len(detections)):
                        if det_idx in used_detection_indices:
                            continue
                        if distances[obj_idx, det_idx] < min_dist:
                            min_dist = distances[obj_idx, det_idx]
                            min_obj_idx = obj_idx
                            min_det_idx = det_idx
                
                # Si la distancia es aceptable, actualizar el objeto
                if min_dist < self.max_distance:
                    obj_id = object_ids[min_obj_idx]
                    new_center = detections[min_det_idx]['center']
                    new_class = detections[min_det_idx]['class_name']
                    
                    # Actualizar objeto
                    self.objects[obj_id]['center'] = new_center
                    self.objects[obj_id]['disappeared'] = 0
                    self.objects[obj_id]['positions'].append(new_center)
                    self.objects[obj_id]['class_name'] = new_class
                    self.objects[obj_id]['category'] = get_item_category(new_class)
                    
                    # Mantener solo las últimas 10 posiciones
                    if len(self.objects[obj_id]['positions']) > 10:
                        self.objects[obj_id]['positions'] = self.objects[obj_id]['positions'][-10:]
                    
                    used_object_ids.add(min_obj_idx)
                    used_detection_indices.add(min_det_idx)
            
            # Marcar objetos no asignados como desaparecidos
            for obj_idx, obj_id in enumerate(object_ids):
                if obj_idx not in used_object_ids:
                    self.objects[obj_id]['disappeared'] += 1
                    if self.objects[obj_id]['disappeared'] > self.max_disappeared:
                        self.deregister(obj_id)
            
            # Registrar nuevas detecciones no asignadas
            for det_idx in range(len(detections)):
                if det_idx not in used_detection_indices:
                    self.register(detections[det_idx]['center'], detections[det_idx]['class_name'])
    
    def check_line_crossing(self, line_x):
        """Verifica si algún objeto ha cruzado la línea de izquierda a derecha"""
        crossings_by_category = {}
        
        for obj_id, obj_data in self.objects.items():
            if obj_data['counted']:
                continue
                
            positions = obj_data['positions']
            if len(positions) < 2:
                continue
            
            # Verificar si ha cruzado la línea de izquierda a derecha
            for i in range(len(positions) - 1):
                prev_x = positions[i][0]
                curr_x = positions[i + 1][0]
                
                # Cruzó de izquierda a derecha
                if prev_x < line_x and curr_x >= line_x:
                    obj_data['counted'] = True
                    category = obj_data['category']
                    
                    if category not in crossings_by_category:
                        crossings_by_category[category] = 0
                    crossings_by_category[category] += 1
                    break
        
        return crossings_by_category

# Seguimiento básico (con centroides)
def get_center(xyxy):
    x1, y1, x2, y2 = map(int, xyxy)
    return (int((x1 + x2) / 2), int((y1 + y2) / 2))

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

# Inicializar tracker
tracker = ObjectTracker()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Redimensionar si es necesario
    frame = cv2.resize(frame, (CAM_WIDTH, CAM_HEIGHT))

    # Inferencia
    results = model(frame, imgsz=640, conf=0.5)

    # Dibujar línea de cruce
    cv2.line(frame, (line_x, 0), (line_x, CAM_HEIGHT), (0, 255, 255), 3)
    cv2.putText(frame, "Linea de conteo", (line_x + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    # Extraer detecciones con información de clase
    detections = []
    detection_info = []
    
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for box in boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy()
                center = get_center(xyxy)
                class_name = class_names[cls_id]
                category = get_item_category(class_name)
                
                detections.append({
                    'center': center,
                    'class_name': class_name,
                    'category': category
                })
                
                detection_info.append({
                    'xyxy': xyxy,
                    'cls_id': cls_id,
                    'conf': conf,
                    'center': center,
                    'class_name': class_name,
                    'category': category
                })

    # Actualizar tracker
    tracker.update(detections)
    
    # Verificar cruces de línea
    new_crossings = tracker.check_line_crossing(line_x)
    
    # Actualizar contadores por categoría
    for category, count in new_crossings.items():
        if category in waste_categories:
            waste_categories[category]['count'] += count
        total_counter += count

    # Dibujar detecciones
    for info in detection_info:
        xyxy = info['xyxy']
        cls_id = info['cls_id']
        conf = info['conf']
        center = info['center']
        class_name = info['class_name']
        category = info['category']
        
        # Color según categoría
        color = get_category_color(category)
        
        # Dibujar caja con color de categoría
        cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), color, 2)
        
        # Dibujar centro
        cv2.circle(frame, center, 4, color, -1)
        
        # Etiqueta con clase, categoría y confianza
        label = f"{class_name} ({category}): {conf:.2f}"
        
        # Fondo para el texto
        (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1]) - text_height - 10), 
                     (int(xyxy[0]) + text_width, int(xyxy[1])), color, -1)
        
        cv2.putText(frame, label, (int(xyxy[0]), int(xyxy[1]) - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Dibujar trayectorias de objetos trackeados
    for obj_id, obj_data in tracker.objects.items():
        positions = obj_data['positions']
        category = obj_data['category']
        color = get_category_color(category)
        
        # Dibujar trayectoria
        for i in range(1, len(positions)):
            cv2.line(frame, positions[i-1], positions[i], color, 2)
        
        # Dibujar ID del objeto
        if positions:
            cv2.putText(frame, f"ID:{obj_id}", 
                       (positions[-1][0] + 5, positions[-1][1] - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            
            # Marcar si ya fue contado
            if obj_data['counted']:
                cv2.circle(frame, positions[-1], 8, color, 3)

    # Mostrar información general
    cv2.putText(frame, f"Total: {total_counter}", (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, f"Tracking: {len(tracker.objects)}", (10, 70), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Dibujar estadísticas por categoría
    draw_category_stats(frame)

    # Leyenda de colores
    legend_y = CAM_HEIGHT - 100
    cv2.putText(frame, "LEYENDA:", (CAM_WIDTH - 200, legend_y - 20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    for i, (category, data) in enumerate(waste_categories.items()):
        y_pos = legend_y + (i * 25)
        color = data['color']
        cv2.rectangle(frame, (CAM_WIDTH - 200, y_pos - 10), (CAM_WIDTH - 180, y_pos + 5), color, -1)
        cv2.putText(frame, category, (CAM_WIDTH - 175, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Mostrar imagen
    cv2.imshow("Contador de basura por categorias", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Mostrar resumen final
print(f"\n=== RESUMEN FINAL ===")
print(f"Total de objetos contados: {total_counter}")
for category, data in waste_categories.items():
    print(f"{category}: {data['count']} objetos")
print("====================\n")