# config.py
# Responsabilidad: Configuración para robot recolector móvil

# Dimensiones de cámara
CAM_WIDTH = 640
CAM_HEIGHT = 640

# Configuración MQTT para robot móvil
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883

# ========== CONFIGURACIÓN ANTI-FALSOS POSITIVOS ==========
MIN_CONSECUTIVE_DETECTIONS = 4  # Reducido para robot móvil
MIN_CONFIDENCE_THRESHOLD = 0.75  # Aumentado para mayor precisión
REPORT_COOLDOWN_SECONDS = 2.0  # Reducido para robot en movimiento
MIN_PRESENCE_TIME = 1.0  # Reducido para detección rápida
MAX_POSITION_VARIANCE = 60  # Aumentado para movimiento del robot
# =======================================================

# Lista específica de clases para robot recolector
class_names = [
    'can',                 # 0
    'plastic_bottle',      # 1        
    'plastic_bottle_cap',  # 2
    'plastic_cup',         # 3
    'plastic_cup_lid',     # 4
    'plastic_cultery',     # 5
    'snack_bag',           # 6
    'plastic_bag',         # 7
    'straw',               # 8
    'scrap_paper',         # 9
    'reuseable_paper',     # 10
    'stick'                # 11
]

# Categorías optimizadas para robot recolector
waste_categories = {
    'METAL': {
        'items': ['can'],
        'color': (0, 255, 255),  # Amarillo
        'priority': 'HIGH',
        'count': 0
    },
    'PLASTICO': {
        'items': ['plastic_bottle', 'plastic_bottle_cap', 'plastic_cup', 
                 'plastic_cup_lid', 'plastic_cultery'],
        'color': (0, 165, 255),  # Naranja
        'priority': 'HIGH', 
        'count': 0
    },
    'BOLSAS': {
        'items': ['snack_bag', 'plastic_bag'],
        'color': (0, 0, 255),  # Rojo
        'priority': 'MEDIUM',
        'count': 0
    },
    'PAPEL': {
        'items': ['scrap_paper', 'reuseable_paper'],
        'color': (0, 255, 0),  # Verde
        'priority': 'MEDIUM',
        'count': 0
    },
    'OTROS': {
        'items': ['straw', 'stick'],
        'color': (128, 128, 128),  # Gris
        'priority': 'LOW',
        'count': 0
    }
}

# Configuración de UI minimalista
UI_CONFIG = {
    'background_color': (20, 20, 20),      # Fondo oscuro
    'text_primary': (255, 255, 255),       # Blanco
    'text_secondary': (180, 180, 180),     # Gris claro
    'accent_color': (0, 255, 255),         # Amarillo (accent)
    'success_color': (0, 255, 0),          # Verde
    'warning_color': (0, 165, 255),        # Naranja
    'error_color': (0, 0, 255),            # Rojo
    'card_background': (40, 40, 40),       # Fondo de tarjetas
    'border_color': (80, 80, 80),          # Bordes
}

# ========================================