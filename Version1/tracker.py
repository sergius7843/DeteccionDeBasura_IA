# tracker.py
# Responsabilidad: Seguimiento manual de detecciones con reinicio de conteo en rebajas

import numpy as np
from categories import get_item_category

class ObjectTracker:
    def __init__(self, max_distance=80, max_disappeared=10):
        self.next_id = 0
        # Estructura: {id: {'center': (x,y), 'disappeared': int, 'positions': [(x,y), ...],
        #                    'counted': bool, 'class_name': str, 'category': str}}
        self.objects = {}
        self.max_distance = max_distance
        self.max_disappeared = max_disappeared

    def register(self, center, class_name='unknown'):
        """Registra un nuevo objeto con ID único"""
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
        """Actualiza el estado de todos los objetos con nuevas detecciones"""
        if len(detections) == 0:
            # Marcar desaparición para todos
            for object_id in list(self.objects.keys()):
                self.objects[object_id]['disappeared'] += 1
                if self.objects[object_id]['disappeared'] > self.max_disappeared:
                    self.deregister(object_id)
            return

        # Si no hay objetos previos, registrar todos
        if len(self.objects) == 0:
            for det in detections:
                self.register(det['center'], det['class_name'])
            return

        object_ids = list(self.objects.keys())
        object_centers = np.array([self.objects[obj]['center'] for obj in object_ids])
        detection_centers = np.array([det['center'] for det in detections])
        distances = np.linalg.norm(object_centers[:, None] - detection_centers, axis=2)

        used_obj = set()
        used_det = set()

        for _ in range(min(len(object_ids), len(detections))):
            min_dist = np.inf
            min_obj_idx = -1
            min_det_idx = -1
            for obj_idx, obj_id in enumerate(object_ids):
                if obj_idx in used_obj:
                    continue
                for det_idx in range(len(detections)):
                    if det_idx in used_det:
                        continue
                    if distances[obj_idx, det_idx] < min_dist:
                        min_dist = distances[obj_idx, det_idx]
                        min_obj_idx = obj_idx
                        min_det_idx = det_idx
            if min_dist < self.max_distance:
                obj_id = object_ids[min_obj_idx]
                det = detections[min_det_idx]
                self.objects[obj_id]['center'] = det['center']
                self.objects[obj_id]['disappeared'] = 0
                self.objects[obj_id]['positions'].append(det['center'])
                self.objects[obj_id]['class_name'] = det['class_name']
                self.objects[obj_id]['category'] = get_item_category(det['class_name'])
                if len(self.objects[obj_id]['positions']) > 10:
                    self.objects[obj_id]['positions'] = self.objects[obj_id]['positions'][-10:]
                used_obj.add(min_obj_idx)
                used_det.add(min_det_idx)

        # Incrementar desaparecidos para objetos no asignados
        for idx, obj_id in enumerate(object_ids):
            if idx not in used_obj:
                self.objects[obj_id]['disappeared'] += 1
                if self.objects[obj_id]['disappeared'] > self.max_disappeared:
                    self.deregister(obj_id)

        # Registrar nuevas detecciones
        for det_idx, det in enumerate(detections):
            if det_idx not in used_det:
                self.register(det['center'], det['class_name'])

    def check_line_crossing(self, line_x):
        """Verifica cruces de objetos de izquierda a derecha y reinicia conteo al cruzar de derecha a izquierda"""
        crossings = {}
        for obj_id, data in self.objects.items():
            positions = data['positions']
            if len(positions) < 2:
                continue
            # Iterar pares de posiciones
            for i in range(len(positions) - 1):
                prev_x, curr_x = positions[i][0], positions[i+1][0]
                # Si cruzó de derecha a izquierda, reiniciar flag de contado
                if data['counted'] and prev_x >= line_x and curr_x < line_x:
                    data['counted'] = False
                # Si cruzó de izquierda a derecha y no está contado, incrementar
                if not data['counted'] and prev_x < line_x and curr_x >= line_x:
                    data['counted'] = True
                    cat = data['category']
                    crossings[cat] = crossings.get(cat, 0) + 1
                    break
        return crossings