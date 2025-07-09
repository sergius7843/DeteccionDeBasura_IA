# categories.py
# Responsabilidad: Lógica de clasificación de objetos

from config import waste_categories

def get_item_category(class_name: str) -> str:
    """Determina la categoría de un objeto basado en su clase."""
    for category, data in waste_categories.items():
        if class_name in data['items']:
            return category
    return 'DESCONOCIDO'

def get_category_color(category: str) -> tuple:
    """Obtiene el color (BGR) asociado a una categoría."""
    if category in waste_categories:
        return waste_categories[category]['color']
    # Gris para desconocido
    return (128, 128, 128)

# ========================================

# detection.py
# Responsabilidad: Extracción de detección y cálculo de centroides

def get_center(xyxy):
    """Calcula el centroide de una caja xyxy"""
    x1, y1, x2, y2 = map(int, xyxy)
    return ((x1 + x2) // 2, (y1 + y2) // 2)

# Clase contenedor para detecciones
class Detection:
    def __init__(self, xyxy, cls_id, conf, class_name, category):
        self.xyxy = xyxy
        self.cls_id = cls_id
        self.conf = conf
        self.center = get_center(xyxy)
        self.class_name = class_name
        self.category = category