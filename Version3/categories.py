# categories.py
# Responsabilidad: Clasificación optimizada para robot recolector

from config import waste_categories

def get_item_category(class_name: str) -> str:
    """Determina la categoría de un objeto para recolección."""
    for category, data in waste_categories.items():
        if class_name in data['items']:
            return category
    return 'DESCONOCIDO'

def get_category_color(category: str) -> tuple:
    """Obtiene el color (BGR) asociado a una categoría."""
    if category in waste_categories:
        return waste_categories[category]['color']
    return (128, 128, 128)

def get_category_priority(category: str) -> str:
    """Obtiene la prioridad de recolección de una categoría."""
    if category in waste_categories:
        return waste_categories[category]['priority']
    return 'LOW'

def get_priority_order():
    """Retorna categorías ordenadas por prioridad para el robot."""
    high_priority = [cat for cat, data in waste_categories.items() if data['priority'] == 'HIGH']
    medium_priority = [cat for cat, data in waste_categories.items() if data['priority'] == 'MEDIUM']
    low_priority = [cat for cat, data in waste_categories.items() if data['priority'] == 'LOW']
    return high_priority + medium_priority + low_priority