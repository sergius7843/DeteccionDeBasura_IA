import cv2

# URL de la cámara IP (reemplaza por tu IP si cambia)
ip_camera_url = "http://192.168.0.4:8080/video"

# Intenta abrir la cámara
cap = cv2.VideoCapture(ip_camera_url)

if not cap.isOpened():
    print("❌ No se pudo conectar a la cámara IP.")
    exit()

print("✅ Conectado a la cámara IP. Presiona 'q' para salir.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ No se pudo leer el frame.")
        break

    # Redimensionar el frame a 640x640
    resized_frame = cv2.resize(frame, (640, 640))

    # Mostrar frame
    cv2.imshow("Camara IP - Redimensionado a 640x640", resized_frame)

    # Salir con 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar recursos
cap.release()
cv2.destroyAllWindows()
