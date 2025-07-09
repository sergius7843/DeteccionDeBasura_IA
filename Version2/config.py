# config.py
# Responsabilidad: Parámetros y constantes globales

# Dimensiones de cámara
CAM_WIDTH = 640
CAM_HEIGHT = 640

# Configuración MQTT
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883

# ========== CONFIGURACIÓN ANTI-FALSOS POSITIVOS ==========
# Mínimo de detecciones consecutivas antes de confirmar un objeto
MIN_CONSECUTIVE_DETECTIONS = 5

# Confianza mínima para considerar una detección válida
MIN_CONFIDENCE_THRESHOLD = 0.7

# Tiempo mínimo en segundos entre reportes del mismo objeto (cooldown)
REPORT_COOLDOWN_SECONDS = 3.0

# Mínimo tiempo de permanencia del objeto en pantalla (segundos)
MIN_PRESENCE_TIME = 1.5

# Máxima distancia permitida entre detecciones consecutivas del mismo objeto
MAX_POSITION_VARIANCE = 50

# =======================================================

# Lista de nombres de clases para detección
class_names = [
    'battery', 'can', 'cardboard_bowl', 'cardboard_box', 'chemical_plastic_bottle',
    'chemical_plastic_gallon', 'chemical_spray_can', 'light_bulb', 'paint_bucket',
    'plastic_bag', 'plastic_bottle', 'plastic_bottle_cap', 'plastic_box',
    'plastic_cultery', 'plastic_cup', 'plastic_cup_lid', 'reuseable_paper',
    'scrap_paper', 'scrap_plastic', 'snack_bag', 'stick', 'straw'
]

# Definición de categorías de desechos con colores
waste_categories = {
    'RECICLABLE': {
        'items': [
            'can', 'cardboard_bowl', 'cardboard_box', 'plastic_bottle', 'plastic_bottle_cap',
            'plastic_box', 'plastic_cup', 'plastic_cup_lid', 'reuseable_paper', 'scrap_paper'
        ],
        'color': (0, 255, 0),  # Verde
        'count': 0
    },
    'NO_RECICLABLE': {
        'items': [
            'plastic_bag', 'plastic_cultery', 'scrap_plastic', 'snack_bag', 'stick', 'straw'
        ],
        'color': (0, 0, 255),  # Rojo
        'count': 0
    },
    'PELIGROSO': {
        'items': [
            'battery', 'chemical_plastic_bottle', 'chemical_plastic_gallon',
            'chemical_spray_can', 'light_bulb', 'paint_bucket'
        ],
        'color': (0, 165, 255),  # Naranja
        'count': 0
    }
}