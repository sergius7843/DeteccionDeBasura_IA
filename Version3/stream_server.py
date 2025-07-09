# Responsabilidad: Servidor Flask para streaming de video en tiempo real

from flask import Flask, render_template, Response, jsonify
from flask_cors import CORS
import cv2
import threading
import time
import json
from datetime import datetime
import queue
import base64

class VideoStreamer:
    def __init__(self):
        self.frame = None
        self.frame_lock = threading.Lock()
        self.stats = {
            'fps': 0,
            'total_detections': 0,
            'categories': {},
            'robot_status': 'ACTIVE',
            'last_update': datetime.now().isoformat()
        }
        self.stats_lock = threading.Lock()
        
    def update_frame(self, frame):
        """Actualiza el frame actual de forma thread-safe"""
        with self.frame_lock:
            self.frame = frame.copy()
    
    def get_frame(self):
        """Obtiene el frame actual de forma thread-safe"""
        with self.frame_lock:
            return self.frame.copy() if self.frame is not None else None
    
    def update_stats(self, new_stats):
        """Actualiza las estadísticas de forma thread-safe"""
        with self.stats_lock:
            self.stats.update(new_stats)
            self.stats['last_update'] = datetime.now().isoformat()
    
    def get_stats(self):
        """Obtiene las estadísticas actuales"""
        with self.stats_lock:
            return self.stats.copy()

# Instancia global del streamer
video_streamer = VideoStreamer()

# Configurar Flask
app = Flask(__name__)
CORS(app)  # Permitir CORS para acceso remoto

@app.route('/')
def index():
    """Página principal del dashboard"""
    return render_template('dashboard.html')

@app.route('/video_feed')
def video_feed():
    """Stream de video en tiempo real"""
    return Response(generate_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/stats')
def api_stats():
    """API REST para obtener estadísticas en JSON"""
    return jsonify(video_streamer.get_stats())

@app.route('/api/frame')
def api_frame():
    """API para obtener frame actual como base64"""
    frame = video_streamer.get_frame()
    if frame is not None:
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        return jsonify({
            'success': True,
            'frame': frame_base64,
            'timestamp': datetime.now().isoformat()
        })
    return jsonify({'success': False, 'error': 'No frame available'})

def generate_frames():
    """Generador de frames para streaming"""
    while True:
        frame = video_streamer.get_frame()
        if frame is not None:
            # Codificar frame como JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.033)  # ~30 FPS

def start_flask_server(host='0.0.0.0', port=5000, debug=False):
    """Inicia el servidor Flask en un hilo separado"""
    app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)