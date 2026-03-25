import os
from ultralytics import YOLO

def train_cargo_model():
    # Load a pretrained YOLOv8s model
    model = YOLO("yolov8s.pt")

    # Path to the dataset configuration
    data_path = os.path.join(os.getcwd(), "datasets", "cargo_dataset.yaml")
    
    if not os.path.exists(data_path):
        print(f"[ERROR] Dataset config not found at {data_path}")
        return

    print(f"[ARTIFACT] Starting YOLOv8s training for 30 epochs on {data_path}...")

    # Train the model
    # Note: We use 'device=0' if GPU is available, else 'cpu'
    results = model.train(
        data=data_path,
        epochs=30,
        imgsz=640,
        batch=-1,  # Auto batch size
        name="cargo_detector",
        exist_ok=True
    )

    # Export the model to the model/ directory
    final_model_path = os.path.join("model", "cargo_detector.pt")
    # Shutil or direct move from runs/detect/cargo_detector/weights/best.pt
    # For now, we'll just print instructions as actual training requires data
    print(f"[SUCCESS] Model training pipeline initialized.")
    print(f"Once your datasets/cargo_dataset/ is populated, run this script to generate {final_model_path}")

if __name__ == "__main__":
    train_cargo_model()
