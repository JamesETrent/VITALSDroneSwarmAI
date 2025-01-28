import time
from ultralytics import YOLO
from pathlib import Path
import json

# Configuration
model_path = "yolo11l.pt"  # Base YOLOv11 model
dataset_path = "AFO-1/data.yaml"  # Path to dataset YAML file
output_dir = Path("benchmarks")  # Directory to save benchmark results
output_dir.mkdir(exist_ok=True)

# Load the model
print("Loading YOLOv11 base model...")
model = YOLO(model_path)

# Run validation to evaluate accuracy
print("Running validation...")
start_time = time.time()
metrics = model.val(
    data=dataset_path,  # Path to dataset YAML file
    conf=0.5,  # Confidence threshold
    device="cpu",  # Run on CPU
)
end_time = time.time()

# Benchmarking metrics
validation_time = end_time - start_time
fps = metrics['fps'] if 'fps' in metrics else 0  # Extract frames per second if available

# Save metrics to JSON
benchmark_results = {
    "model": model_path,
    "dataset": dataset_path,
    "validation_time_sec": validation_time,
    "accuracy": metrics.get("map50"),  # Mean Average Precision @ IoU=0.5
    "fps": fps,
    "other_metrics": metrics,  # Full metrics dictionary
}

benchmark_file = output_dir / "base_model_benchmark.json"
with open(benchmark_file, "w") as f:
    json.dump(benchmark_results, f, indent=4)

# Print results
print("\n--- Benchmark Results ---")
print(f"Validation Time: {validation_time:.2f} seconds")
print(f"Mean Average Precision (mAP@0.5): {metrics.get('map50'):.2f}")
print(f"Frames Per Second (FPS): {fps:.2f}")
print(f"Results saved to {benchmark_file}")

# Perform inference to measure speed
print("\nMeasuring inference speed on test images...")
test_images_dir = Path("AFO-1/test/images")  # Adjust to your dataset's test image folder
inference_times = []
for image_path in test_images_dir.iterdir():
    if image_path.suffix not in [".jpg", ".png", ".jpeg"]:
        continue

    start_time = time.time()
    results = model.predict(source=str(image_path), conf=0.5, device="cpu", show=False)
    end_time = time.time()

    inference_time = end_time - start_time
    inference_times.append(inference_time)

# Compute average inference time
average_inference_time = sum(inference_times) / len(inference_times) if inference_times else 0
print(f"Average Inference Time: {average_inference_time:.2f} seconds per image")
