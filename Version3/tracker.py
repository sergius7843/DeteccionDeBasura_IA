# tracker.py
# Responsabilidad: Seguimiento optimizado para robot móvil

import numpy as np
import time
from categories import get_item_category
from config import (MIN_CONSECUTIVE_DETECTIONS, MIN_CONFIDENCE_THRESHOLD, 
                    REPORT_COOLDOWN_SECONDS, MIN_PRESENCE_TIME, MAX_POSITION_VARIANCE)

class ObjectTracker:
    def __init__(self, max_distance=90, max_disappeared=12):  # Ajustado para robot móvil
        self.next_id = 0
        self.objects = {}
        self.max_distance = max_distance  # Mayor distancia por movimiento del robot
        self.max_disappeared = max_disappeared  # Más frames para objetos perdidos

    def register(self, center, class_name='unknown', confidence=0.0):
        """Registra un nuevo objeto optimizado para robot móvil"""
        category = get_item_category(class_name)
        current_time = time.time()
        
        self.objects[self.next_id] = {
            'center': center,
            'disappeared': 0,
            'positions': [center],
            'class_name': class_name,
            'category': category,
            'confidence_history': [confidence],
            'avg_confidence': confidence,
            'consecutive_detections': 1,
            'first_seen': current_time,
            'last_seen': current_time,
            'last_reported': 0,
            'confirmed': False,
            'reported': False,
            'stable_class': class_name,
            'class_changes': 0,
            'position_variance': 0.0,
            'movement_pattern': 'STATIC'  # Nuevo: patrón de movimiento
        }
        self.next_id += 1

    def deregister(self, object_id):
        """Elimina un objeto del tracking"""
        if object_id in self.objects:
            del self.objects[object_id]

    def _calculate_position_variance(self, positions):
        """Calcula varianza ajustada para robot móvil"""
        if len(positions) < 3:
            return 0.0
        
        positions_array = np.array(positions)
        variance_x = np.var(positions_array[:, 0])
        variance_y = np.var(positions_array[:, 1])
        return (variance_x + variance_y) / 2

    def _analyze_movement_pattern(self, positions):
        """Analiza el patrón de movimiento del objeto"""
        if len(positions) < 4:
            return 'STATIC'
        
        # Calcular distancias entre puntos consecutivos
        distances = []
        for i in range(1, len(positions)):
            dist = np.linalg.norm(np.array(positions[i]) - np.array(positions[i-1]))
            distances.append(dist)
        
        avg_movement = np.mean(distances)
        
        if avg_movement < 5:
            return 'STATIC'  # Objeto estático (ideal para recolección)
        elif avg_movement < 20:
            return 'SLOW_MOVING'  # Movimiento lento
        else:
            return 'FAST_MOVING'  # Movimiento rápido

    def _update_class_stability(self, obj_data, new_class):
        """Actualiza estabilidad de clase (más permisivo para robot móvil)"""
        if obj_data['stable_class'] != new_class:
            obj_data['class_changes'] += 1
            
            # Más tolerante a cambios por movimiento del robot
            if obj_data['class_changes'] > 4:  # Aumentado de 3 a 4
                return False
            
            # Actualizar clase estable
            if obj_data['consecutive_detections'] > MIN_CONSECUTIVE_DETECTIONS // 2:
                obj_data['stable_class'] = new_class
                obj_data['category'] = get_item_category(new_class)
        
        return True

    def update(self, detections):
        """Actualiza tracking optimizado para robot móvil"""
        current_time = time.time()
        
        if len(detections) == 0:
            for object_id in list(self.objects.keys()):
                self.objects[object_id]['disappeared'] += 1
                if self.objects[object_id]['disappeared'] > self.max_disappeared:
                    self.deregister(object_id)
            return

        # Filtrar detecciones por confianza
        filtered_detections = [det for det in detections if det['confidence'] >= MIN_CONFIDENCE_THRESHOLD]
        
        if len(filtered_detections) == 0:
            for object_id in list(self.objects.keys()):
                self.objects[object_id]['disappeared'] += 1
                if self.objects[object_id]['disappeared'] > self.max_disappeared:
                    self.deregister(object_id)
            return

        # Registrar nuevos objetos si no hay tracking previo
        if len(self.objects) == 0:
            for det in filtered_detections:
                if det['confidence'] >= MIN_CONFIDENCE_THRESHOLD + 0.05:  # Menos restrictivo
                    self.register(det['center'], det['class_name'], det['confidence'])
            return

        object_ids = list(self.objects.keys())
        object_centers = np.array([self.objects[obj]['center'] for obj in object_ids])
        detection_centers = np.array([det['center'] for det in filtered_detections])
        distances = np.linalg.norm(object_centers[:, None] - detection_centers, axis=2)

        used_obj = set()
        used_det = set()

        # Asociación optimizada para robot móvil
        for _ in range(min(len(object_ids), len(filtered_detections))):
            min_dist = np.inf
            min_obj_idx = -1
            min_det_idx = -1
            
            for obj_idx, obj_id in enumerate(object_ids):
                if obj_idx in used_obj:
                    continue
                for det_idx in range(len(filtered_detections)):
                    if det_idx in used_det:
                        continue
                    if distances[obj_idx, det_idx] < min_dist:
                        min_dist = distances[obj_idx, det_idx]
                        min_obj_idx = obj_idx
                        min_det_idx = det_idx
            
            if min_dist < self.max_distance:
                obj_id = object_ids[min_obj_idx]
                det = filtered_detections[min_det_idx]
                obj_data = self.objects[obj_id]
                
                if not self._update_class_stability(obj_data, det['class_name']):
                    continue
                
                # Actualizar datos
                obj_data['center'] = det['center']
                obj_data['disappeared'] = 0
                obj_data['positions'].append(det['center'])
                obj_data['last_seen'] = current_time
                obj_data['confidence_history'].append(det['confidence'])
                obj_data['consecutive_detections'] += 1
                
                # Mantener historial limitado
                if len(obj_data['positions']) > 12:  # Reducido para robot móvil
                    obj_data['positions'] = obj_data['positions'][-12:]
                if len(obj_data['confidence_history']) > 8:
                    obj_data['confidence_history'] = obj_data['confidence_history'][-8:]
                
                # Calcular métricas
                obj_data['avg_confidence'] = np.mean(obj_data['confidence_history'])
                obj_data['position_variance'] = self._calculate_position_variance(obj_data['positions'])
                obj_data['movement_pattern'] = self._analyze_movement_pattern(obj_data['positions'])
                
                # Criterios de confirmación más flexibles para robot móvil
                if (not obj_data['confirmed'] and 
                    obj_data['consecutive_detections'] >= MIN_CONSECUTIVE_DETECTIONS and
                    obj_data['avg_confidence'] >= MIN_CONFIDENCE_THRESHOLD and
                    (current_time - obj_data['first_seen']) >= MIN_PRESENCE_TIME):
                    
                    obj_data['confirmed'] = True
                    print(f"🤖 Objeto confirmado para recolección: {obj_data['stable_class']} (ID: {obj_id})")
                
                used_obj.add(min_obj_idx)
                used_det.add(min_det_idx)

        # Gestión de objetos no asignados
        for idx, obj_id in enumerate(object_ids):
            if idx not in used_obj:
                self.objects[obj_id]['disappeared'] += 1
                if self.objects[obj_id]['disappeared'] > self.max_disappeared:
                    self.deregister(obj_id)

        # Registrar nuevas detecciones
        for det_idx, det in enumerate(filtered_detections):
            if det_idx not in used_det and det['confidence'] >= MIN_CONFIDENCE_THRESHOLD + 0.05:
                self.register(det['center'], det['class_name'], det['confidence'])

    def get_confirmed_objects_for_report(self):
        """Retorna objetos confirmados listos para reportar al robot"""
        current_time = time.time()
        objects_to_report = {}
        
        for obj_id, data in self.objects.items():
            if (data['confirmed'] and 
                not data['reported'] and
                (current_time - data['last_reported']) >= REPORT_COOLDOWN_SECONDS):
                
                category = data['category']
                if category not in objects_to_report:
                    objects_to_report[category] = []
                
                objects_to_report[category].append({
                    'id': obj_id,
                    'class_name': data['stable_class'],
                    'category': category,
                    'confidence': data['avg_confidence'],
                    'detection_time': current_time - data['first_seen'],
                    'movement_pattern': data['movement_pattern'],
                    'position': data['center']  # Útil para navegación del robot
                })
                
                data['reported'] = True
                data['last_reported'] = current_time
        
        return objects_to_report

    def get_detection_stats(self):
        """Estadísticas optimizadas para robot móvil"""
        total_objects = len(self.objects)
        confirmed_objects = sum(1 for obj in self.objects.values() if obj['confirmed'])
        pending_objects = total_objects - confirmed_objects
        static_objects = sum(1 for obj in self.objects.values() 
                           if obj.get('movement_pattern') == 'STATIC')
        
        return {
            'total_tracked': total_objects,
            'confirmed': confirmed_objects,
            'pending_confirmation': pending_objects,
            'static_objects': static_objects,  # Ideales para recolección
            'collectible_items': static_objects  # Items fáciles de recolectar
        }

# ========================================
