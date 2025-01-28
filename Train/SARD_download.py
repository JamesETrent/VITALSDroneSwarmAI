from ultralytics import YOLO
from roboflow import Roboflow
import os

# Initialize Roboflow with your API key
rf = Roboflow(api_key="FZ8nMp8jPXuF4Tf2qnEN")
project = rf.workspace("vitals-s7v4a").project("sard_yolo-rybpx")
version = project.version(1)

# Check if the dataset exists before downloading
dataset_path = "datasets/sard_yolo"  # Specify a path for storing datasets
if not os.path.exists(dataset_path):
    dataset = version.download("yolov11")
    print("Dataset downloaded successfully!")
else:
    print("Dataset already exists. Skipping download.")

# Load the YOLO model
model = YOLO("yolo11n.pt")  # Adjust the model version as needed

# Train the model on the CPU
train_results = model.train(
    data=f"{dataset_path}/data.yaml",  # Path to the dataset configuration file
    epochs=100,  # Number of training epochs
    imgsz=640,  # Image size for training
    device="cpu",  # Explicitly set to CPU
    batch=16,  # Adjust batch size for CPU training
    name="yolo11n_cpu_training",  # Run name for tracking
    workers=4  # Number of data loader workers
)

print("Training complete!")
