import torch

if torch.cuda.is_available():
    print(f"✅ GPU disponible: {torch.cuda.get_device_name(0)}")
else:
    print("❌ GPU NO detectada. Usando CPU.")
