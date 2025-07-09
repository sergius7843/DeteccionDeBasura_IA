from ultralytics import YOLO

def main():
    model = YOLO('yolov8l.pt') 


    model.train(
        data='data.yaml',
        epochs=85,
        imgsz=640,
        batch=16,
        workers=8,
        name='waste-detection',
        project='runs/train',
        patience=20 #guardado cada 20 epoc
    )

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main() 
