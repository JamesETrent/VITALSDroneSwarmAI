from ultralytics import YOLO
import json
from pathlib import Path

# Specify the model path (either yolo11n.pt or yolo11l.pt)
model_path = "yolo11n.pt"  # Change this to the desired model

# Load the YOLOv11 model
model = YOLO(model_path)
if "11n" in model_path:
    subfolder_name = "yolo11n"
elif "11m" in model_path:
    subfolder_name = "yolo11m"
elif "11l" in model_path:
    subfolder_name = "yolo11l"
else:
    subfolder_name = "other_runs"  # Fallback if no match is found
# Create unique directories for JSON and video files
base_json_dir = Path("runs/") / subfolder_name / "jsonfile"
base_video_dir = Path("runs/") / subfolder_name / "videorun"

# Increment directory names for new runs
json_output_dir = base_json_dir
video_output_dir = base_video_dir
for i in range(1, 100):  
    if not json_output_dir.exists():
        break
    json_output_dir = Path(f"{base_json_dir}{i}")
    video_output_dir = Path(f"{base_video_dir}{i}")

json_output_dir.mkdir(parents=True, exist_ok=True)
video_output_dir.mkdir(parents=True, exist_ok=True)

results_cache = []  # Store results for JSON creation

try:
    print("Starting model prediction...")
    results = model.predict(
        source=0,  # Webcam index
        imgsz=640,
        device="cpu",  # Use 'cuda' if your GPU is supported
        conf=0.5,  # Confidence threshold
        show=True,  # Display results
        save=True,  # Save results
        project=str(video_output_dir),  # Save video in videorun folder
        name="",  # Leave empty to avoid creating additional subfolders
        stream=True,  # Enable streaming for real-time processing
    )
    for i, result in enumerate(results):
        detections = []
        for box in result.boxes:  # Iterate over detected objects in the frame
            bbox_coords = [float(coord) for coord in box.xyxy[0].tolist()]  # Bounding box in [x_min, y_min, x_max, y_max] format
            detections.append({
                "label": result.names[int(box.cls)],  # Object label
                "confidence": float(box.conf),       # Confidence score
                "bbox": bbox_coords                  # Bounding box coordinates
            })

        # Only create a JSON file if there are detections
        if detections:
            yolo_output = {
                "frame_id": i,         # Frame index
                "detections": detections  # List of detections
            }

            # Save JSON to a file
            json_path = json_output_dir / f"yolo_output_frame_{i}.json"
            with open(json_path, "w") as f:
                json.dump(yolo_output, f, indent=4)

            print(f"Saved YOLO output to {json_path}")
except KeyboardInterrupt:
    print("Detection stopped by user.")
finally:
    print("Detection process completed.")
