# detection.py
# Responsabilidad: Extracción de detección y cálculo de centroides

def get_center(xyxy):
    """Calcula el centroide de una caja xyxy"""
    x1, y1, x2, y2 = map(int, xyxy)
    return ((x1 + x2) // 2, (y1 + y2) // 2)

# Opcional: clase contenedor para detecciones
class Detection:
    def __init__(self, xyxy, cls_id, conf, class_name, category):
        self.xyxy = xyxy
        self.cls_id = cls_id
        self.conf = conf
        self.center = get_center(xyxy)
        self.class_name = class_name
        self.category = category
