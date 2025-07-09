# config.py
# Responsabilidad: Parámetros y constantes globales

# Dimensiones de cámara
CAM_WIDTH = 640
CAM_HEIGHT = 480

# Posición de la línea de conteo (porcentaje de ancho)
LINE_POSITION_PERCENT = 0.65  # 65%
# Cálculo de la coordenada X de la línea de conteo
line_x = int(CAM_WIDTH * LINE_POSITION_PERCENT)

# Lista de nombres de clases para detección
class_names = [
    'battery', 'can', 'cardboard_bowl', 'cardboard_box', 'chemical_plastic_bottle',
    'chemical_plastic_gallon', 'chemical_spray_can', 'light_bulb', 'paint_bucket',
    'plastic_bag', 'plastic_bottle', 'plastic_bottle_cap', 'plastic_box',
    'plastic_cultery', 'plastic_cup', 'plastic_cup_lid', 'reuseable_paper',
    'scrap_paper', 'scrap_plastic', 'snack_bag', 'stick', 'straw'
]

# Definición de categorías de desechos con colores y contadores iniciales
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

# Contador total de objetos cruzados
total_counter = 0