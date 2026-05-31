import sys
import os

# Добавляем корень проекта в sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from pipeline.data_pipeline import generate_synthetic_data

if __name__ == "__main__":
    raw_dir = os.path.join(PROJECT_ROOT, "artifacts", "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)

    generate_synthetic_data(
        data_dir=raw_dir,
        n_products=60,
        n_warehouses=5,
        n_days=180,
        random_state=42
    )
    print(f"Test CSV files generated in {raw_dir}")
