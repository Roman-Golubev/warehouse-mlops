import sys
import os

# Корень проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import shutil
import json

from pipeline.data_pipeline import run_data_pipeline
from pipeline.train import train_model

MODELS_DIR = "artifacts/models"
METRICS_DIR = "artifacts/metrics"


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(METRICS_DIR, exist_ok=True)

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    print(f"Using MLFLOW_TRACKING_URI={tracking_uri}")

    run_data_pipeline(data_dir="artifacts/data/raw", artifacts_dir="artifacts/data")
    metrics = train_model()

    candidate = os.path.join(MODELS_DIR, "model_candidate.pkl")
    blue = os.path.join(MODELS_DIR, "model_blue.pkl")
    
    # диагностика, если падает bootstrap
    if not os.path.exists(candidate):
        raise FileNotFoundError(f"Candidate model was not created: {candidate}")

    shutil.copyfile(candidate, blue)

    with open(os.path.join(MODELS_DIR, "current_prod_model.json"), "w", encoding="utf-8") as f:
        json.dump({
            "active_color": "blue",
            "model_path": blue,
            "version": "bootstrap"
        }, f, indent=2)

    with open(os.path.join(METRICS_DIR, "production_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("Bootstrap model created successfully")


if __name__ == "__main__":
    main()
